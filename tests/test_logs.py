import json

import pytest

from jupyterhub.tests.utils import api_request, async_requests

from .utils import add_environment, wait_for_image


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


@pytest.mark.asyncio
async def test_stream_simple(app, remove_test_image, minimal_repo, image_name, request):
    name, ref = image_name.split(":")
    await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    r = await api_request(app, "environments", image_name, "logs", stream=True)
    r.raise_for_status()

    assert r.headers["content-type"] == "text/event-stream"
    ex = async_requests.executor
    line_iter = iter(r.iter_lines(decode_unicode=True))
    evt = await ex.submit(next_event, line_iter)
    assert evt == {"phase": "log", "message": "Picked Git content provider.\n"}

    r.close()
    await wait_for_image(image_name=image_name)
