import asyncio
import json

from aiodocker import Docker, DockerError
from jupyterhub.tests.utils import (
    async_requests,
    auth_header,
    check_db_locks,
    public_host,
    public_url,
)
from jupyterhub.utils import url_path_join as ujoin
from tornado.httputil import url_concat


@check_db_locks
async def api_request(app, *api_path, method="get", noauth=False, **kwargs):
    """Make an API request"""

    base_url = public_url(app, path="services/tljh_repo2docker")

    headers = kwargs.setdefault("headers", {})
    if "Authorization" not in headers and not noauth and "cookies" not in kwargs:
        # make a copy to avoid modifying arg in-place
        kwargs["headers"] = h = {}
        h.update(headers)
        h.update(auth_header(app.db, kwargs.pop("name", "admin")))

    url = ujoin(base_url, "api", *api_path)
    if "cookies" in kwargs:
        # for cookie-authenticated requests,
        # add _xsrf to url params
        if "_xsrf" in kwargs["cookies"] and not noauth:
            url = url_concat(url, {"_xsrf": kwargs["cookies"]["_xsrf"]})

    f = getattr(async_requests, method)
    if app.internal_ssl:
        kwargs["cert"] = (app.internal_ssl_cert, app.internal_ssl_key)
        kwargs["verify"] = app.internal_ssl_ca
    resp = await f(url, **kwargs)

    return resp


def get_service_page(path, app, **kw):
    prefix = app.base_url
    service_prefix = "services/tljh_repo2docker"
    url = ujoin(public_host(app), prefix, service_prefix, path)
    return async_requests.get(url, **kw)


async def add_environment(
    app,
    *,
    repo,
    ref="HEAD",
    name="",
    memory="",
    cpu="",
    provider=None,
    node_selector={},
):
    """Use the POST endpoint to add a new environment"""
    data = {
        "repo": repo,
        "ref": ref,
        "name": name,
        "memory": memory,
        "cpu": cpu,
        "node_selector": node_selector,
    }
    if provider:
        data["provider"] = provider
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(data),
    )
    return r


async def wait_for_image(*, image_name):
    """wait until an image is built"""
    count, retries = 0, 60 * 10
    image = None
    async with Docker() as docker:
        while count < retries:
            await asyncio.sleep(1)
            try:
                image = await docker.images.inspect(image_name)
            except DockerError:
                count += 1
                continue
            else:
                break
    return image


async def remove_environment(app, *, image_name):
    """Use the DELETE endpoint to remove an environment"""
    r = await api_request(
        app,
        "environments",
        method="delete",
        data=json.dumps(
            {
                "name": image_name,
            }
        ),
    )
    return r


async def remove_docker_image(image_name):
    async with Docker() as docker:
        try:
            await docker.images.delete(image_name, force=True)
        except DockerError:
            pass


def next_event(it):
    """read an event from an eventstream
    From: https://github.com/jupyterhub/jupyterhub/blob/81d423d6c674765400a6fe88064c1366b7070f94/jupyterhub/tests/test_api.py#L692-L700
    """
    while True:
        try:
            line = next(it)
        except StopIteration:
            return
        if line.startswith("data:"):
            return json.loads(line.split(":", 1)[1])
