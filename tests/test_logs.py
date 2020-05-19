import pytest

from jupyterhub.tests.utils import api_request

from .utils import add_environment


@pytest.mark.asyncio
async def test_stream_simple(app, remove_test_image, minimal_repo, image_name, request):
    name, ref = image_name.split(":")
    await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    r = await api_request(app, "environments", image_name, "logs", stream=True)
    r.raise_for_status()
    request.addfinalizer(r.close)
    assert r.headers["content-type"] == "text/event-stream"
