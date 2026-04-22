import pytest
from jupyterhub.tests.utils import async_requests

from ..utils import add_environment, api_request, next_event, wait_for_image


@pytest.mark.asyncio
async def test_stream_simple(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    r = await api_request(app, "environments", image_name, "logs", stream=True)
    r.raise_for_status()

    assert r.headers["content-type"] == "text/event-stream"
    ex = async_requests.executor
    line_iter = iter(r.iter_lines(decode_unicode=True))

    # Read all events until build finishes (DB-based streaming sends incremental
    # updates; we accumulate the full log across events)
    full_log = ""
    final_phase = None
    while True:
        evt = await ex.submit(next_event, line_iter)  # type: ignore[misc]
        if evt is None:
            break
        full_log += evt.get("message", "")
        if evt.get("phase") in ("built", "error"):
            final_phase = evt["phase"]
            break

    r.close()
    assert final_phase == "built"
    assert "Picked Git content provider" in full_log


@pytest.mark.asyncio
async def test_no_build(app, image_name, request):
    r = await api_request(
        app, "environments", "image-not-found:12345", "logs", stream=True
    )
    request.addfinalizer(r.close)
    assert r.status_code == 404
