from uuid import uuid4

import pytest
from jupyterhub.tests.utils import async_requests
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tljh_repo2docker.database.manager import ImagesDatabaseManager
from tljh_repo2docker.database.schemas import (
    BuildStatusType,
    DockerImageCreateSchema,
    ImageMetadataType,
)

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


@pytest.mark.asyncio
async def test_logs_stream_by_uid(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    uid = r.json()["uid"]

    r = await api_request(app, "environments", uid, "logs", stream=True)
    r.raise_for_status()
    assert r.headers["content-type"] == "text/event-stream"

    ex = async_requests.executor
    line_iter = iter(r.iter_lines(decode_unicode=True))
    evt = await ex.submit(next_event, line_iter)  # type: ignore[misc]
    assert evt is not None
    assert "message" in evt

    r.close()
    await wait_for_image(image_name=image_name)


@pytest.mark.asyncio
async def test_logs_failed_image(app, image_name):
    """Logs endpoint returns phase=error immediately for a FAILED image."""
    uid = uuid4()
    error_msg = "Build failed: invalid Dockerfile"

    engine = create_async_engine("sqlite+aiosqlite:///tljh_repo2docker.sqlite")
    maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    manager = ImagesDatabaseManager()
    async with maker() as session:
        await manager.create(
            session,
            DockerImageCreateSchema(
                uid=uid,
                name=image_name,
                status=BuildStatusType.FAILED,
                log=error_msg,
                image_meta=ImageMetadataType(
                    display_name="test",
                    repo="https://github.com/test/test",
                    ref="HEAD",
                    creation_date="01/01/2025",
                    owner="admin",
                    cpu_limit="",
                    mem_limit="",
                    node_selector={},
                ),
            ),
        )
    await engine.dispose()

    r = await api_request(app, "environments", str(uid), "logs", stream=True)
    r.raise_for_status()
    assert r.headers["content-type"] == "text/event-stream"

    ex = async_requests.executor
    line_iter = iter(r.iter_lines(decode_unicode=True))
    evt = await ex.submit(next_event, line_iter)  # type: ignore[misc]
    r.close()

    assert evt is not None
    assert evt.get("phase") == "error"
    assert error_msg in evt.get("message", "")
