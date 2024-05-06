import pytest
from jupyterhub.tests.utils import async_requests

from ..utils import add_environment, api_request, next_event, wait_for_image


@pytest.mark.asyncio
async def test_stream_simple(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    build_response = await add_environment(
        app, repo=minimal_repo, name=name, ref=ref, provider="git"
    )
    uid = build_response.json().get("uid", None)
    assert uid is not None
    r = await api_request(app, "environments", uid, "logs", stream=True)
    r.raise_for_status()

    assert r.headers["content-type"] == "text/event-stream"
    ex = async_requests.executor
    line_iter = iter(r.iter_lines(decode_unicode=True))
    evt = await ex.submit(next_event, line_iter)
    evt = await ex.submit(next_event, line_iter)
    msg = evt.get("message", "")
    assert "Picked Git content provider." in msg

    r.close()
    await wait_for_image(image_name=image_name)


@pytest.mark.asyncio
async def test_bad_uuid(app, image_name, request):
    r = await api_request(app, "environments", "bad-uuid", "logs", stream=True)
    request.addfinalizer(r.close)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_image_not_found(app, image_name, request):
    random_uid = "a025d82f-48a7-4d6b-ba31-e7056c3dbca6"
    r = await api_request(app, "environments", random_uid, "logs", stream=True)
    request.addfinalizer(r.close)
    assert r.status_code == 404
