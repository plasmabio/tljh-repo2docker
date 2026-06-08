import asyncio
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from aiodocker import Docker, DockerError

from tljh_repo2docker.database.model import DockerImageSQL
from tljh_repo2docker.database.schemas import BuildStatusType

from ..utils import add_environment, remove_environment, wait_for_image


def _insert_image_row(db_session, *, uid, name, status, display_name=None):
    db_session.execute(
        sa.insert(DockerImageSQL).values(
            uid=uid,
            name=name,
            status=status.value if hasattr(status, "value") else status,
            log="",
            image_meta={
                "display_name": display_name or name.split(":")[0],
                "repo": "https://example.com/repo",
                "ref": "HEAD",
                "creation_date": "01/01/2025",
                "owner": "admin",
                "cpu_limit": "",
                "mem_limit": "",
                "node_selector": {},
            },
        )
    )
    db_session.commit()


@pytest.mark.asyncio
async def test_add_environment(
    app, minimal_repo, image_name, generated_image_name, db_session
):
    name, ref = image_name.split(":")
    node_selector = {"key": "value"}
    r = await add_environment(
        app,
        repo=minimal_repo,
        name=name,
        ref=ref,
        provider="git",
        node_selector=node_selector,
    )
    assert r.status_code == 200
    uid = r.json().get("uid", None)
    assert uid is not None

    await wait_for_image(image_name=generated_image_name)
    await asyncio.sleep(3)
    images_db = (
        db_session.execute(
            sa.select(DockerImageSQL).where(DockerImageSQL.uid == UUID(uid))
        )
        .scalars()
        .first()
    )
    assert images_db is not None
    assert images_db.name == generated_image_name
    assert images_db.image_meta["display_name"] == name
    assert images_db.image_meta["ref"] == ref
    assert images_db.image_meta["node_selector"] == node_selector


@pytest.mark.asyncio
async def test_delete_environment(
    app, minimal_repo, image_name, generated_image_name, db_session
):
    name, ref = image_name.split(":")
    node_selector = {"key": "value"}
    r = await add_environment(
        app,
        repo=minimal_repo,
        name=name,
        ref=ref,
        provider="git",
        node_selector=node_selector,
    )
    assert r.status_code == 200
    uid = r.json().get("uid", None)
    assert uid is not None

    await wait_for_image(image_name=generated_image_name)
    await asyncio.sleep(3)
    r = await remove_environment(app, image_name=uid)
    assert r.status_code == 200

    # make sure the image does not exist anymore
    docker = Docker()
    with pytest.raises(DockerError):
        await docker.images.inspect(generated_image_name)
    await docker.close()


@pytest.mark.asyncio
async def test_delete_unknown_environment(app):
    random_uid = "a025d82f-48a7-4d6b-ba31-e7056c3dbca6"
    r = await remove_environment(app, image_name=random_uid)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_no_repo(app, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo="", name=name, ref=ref, provider="git")
    assert r.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "memory, cpu, node_selector, expected_error",
    [
        ("abcded", "", {"key": "value"}, "must be a number"),
        ("", "abcde", {"key": "value"}, "must be a number"),
        ("-1", "", {"key": "value"}, "must be a positive number"),
        ("", "-2", {"key": "value"}, "must be a positive number"),
        ("0", "", {"key": "value"}, "must be a positive number"),
        ("", "0", {"key": "value"}, "must be a positive number"),
    ],
)
async def test_wrong_limits(
    app, minimal_repo, image_name, memory, cpu, node_selector, expected_error
):
    name, ref = image_name.split(":")
    r = await add_environment(
        app,
        repo=minimal_repo,
        name=name,
        ref=ref,
        memory=memory,
        cpu=cpu,
        node_selector=node_selector,
        provider="git",
    )
    assert r.status_code == 400
    assert expected_error in r.text


@pytest.mark.asyncio
async def test_wrong_name(app, minimal_repo):
    r = await add_environment(
        app, repo=minimal_repo, name="#WRONG_NAME#", provider="git"
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_missing_provider(app, minimal_repo):
    r = await add_environment(app, repo=minimal_repo, name="foobar")
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_rebuild_unknown_uid_returns_404(app, minimal_repo):
    r = await add_environment(
        app,
        repo=minimal_repo,
        name="ghost",
        ref="HEAD",
        provider="git",
        uid=str(uuid4()),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_rebuild_with_mismatched_name_returns_400(
    app, minimal_repo, db_session
):
    uid = uuid4()
    _insert_image_row(
        db_session,
        uid=uid,
        name="original:HEAD",
        display_name="original",
        status=BuildStatusType.BUILT,
    )
    try:
        r = await add_environment(
            app,
            repo=minimal_repo,
            name="otherword",
            ref="HEAD",
            provider="git",
            uid=str(uid),
        )
        assert r.status_code == 400
    finally:
        db_session.execute(
            sa.delete(DockerImageSQL).where(DockerImageSQL.uid == uid)
        )
        db_session.commit()


@pytest.mark.asyncio
async def test_rebuild_while_building_returns_409(app, minimal_repo, db_session):
    uid = uuid4()
    _insert_image_row(
        db_session,
        uid=uid,
        name="busy:HEAD",
        display_name="busy",
        status=BuildStatusType.BUILDING,
    )
    try:
        r = await add_environment(
            app,
            repo=minimal_repo,
            name="busy",
            ref="HEAD",
            provider="git",
            uid=str(uid),
        )
        assert r.status_code == 409
    finally:
        db_session.execute(
            sa.delete(DockerImageSQL).where(DockerImageSQL.uid == uid)
        )
        db_session.commit()
