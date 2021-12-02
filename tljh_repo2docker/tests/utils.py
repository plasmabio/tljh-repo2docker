import asyncio
import json

from aiodocker import Docker, DockerError
from jupyterhub.tests.utils import api_request


async def add_environment(
    app, *, repo, ref="HEAD", name="", memory="", cpu=""
):
    """Use the POST endpoint to add a new environment"""
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(
            {"repo": repo, "ref": ref, "name": name, "memory": memory, "cpu": cpu,}
        ),
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
        app, "environments", method="delete", data=json.dumps({"name": image_name,}),
    )
    return r
