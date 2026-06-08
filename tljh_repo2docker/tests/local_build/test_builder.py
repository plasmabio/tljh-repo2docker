from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from aiodocker import Docker, DockerError

from tljh_repo2docker.database.model import DockerImageSQL
from tljh_repo2docker.database.schemas import BuildStatusType

from ..utils import add_environment, remove_environment, wait_for_image


def _insert_image_row(*, uid, name, status, display_name=None, repo="https://example.com/repo", ref="HEAD"):
    """Insert an image row directly in the sqlite DB used by the test service."""
    engine = sa.create_engine("sqlite:///tljh_repo2docker.sqlite")
    with engine.begin() as conn:
        conn.execute(
            sa.insert(DockerImageSQL).values(
                uid=uid,
                name=name,
                status=status.value if hasattr(status, "value") else status,
                log="",
                image_meta={
                    "display_name": display_name or name.split(":")[0],
                    "repo": repo,
                    "ref": ref,
                    "creation_date": "01/01/2025",
                    "owner": "admin",
                    "cpu_limit": "",
                    "mem_limit": "",
                    "node_selector": {},
                },
            )
        )
    engine.dispose()


def _read_image_row(uid):
    engine = sa.create_engine("sqlite:///tljh_repo2docker.sqlite")
    with engine.begin() as conn:
        row = conn.execute(
            sa.select(DockerImageSQL).where(DockerImageSQL.uid == uid)
        ).first()
    engine.dispose()
    return row


@pytest.mark.asyncio
async def test_add_environment(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    image = await wait_for_image(image_name=image_name)
    assert image is not None, "Docker image was not found after build"
    config = image.get("ContainerConfig", image.get("Config", {}))
    assert config["Labels"]["tljh_repo2docker.image_name"] == image_name


@pytest.mark.asyncio
async def test_delete_environment(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    await wait_for_image(image_name=image_name)
    r = await remove_environment(app, image_name=image_name)
    assert r.status_code == 200

    # make sure the image does not exist anymore
    docker = Docker()
    with pytest.raises(DockerError):
        await docker.images.inspect(image_name)
    await docker.close()


@pytest.mark.asyncio
async def test_delete_unknown_environment(app):
    r = await remove_environment(app, image_name="image-not-found:12345")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_uppercase_repo(app, minimal_repo_uppercase, generated_image_name):
    r = await add_environment(app, repo=minimal_repo_uppercase)
    assert r.status_code == 200
    image = await wait_for_image(image_name=generated_image_name)
    config = image.get("ContainerConfig", image.get("Config", {}))
    assert config["Labels"]["tljh_repo2docker.image_name"] == generated_image_name


@pytest.mark.asyncio
async def test_no_repo(app, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo="", name=name, ref=ref)
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
    )
    assert r.status_code == 400
    assert expected_error in r.text


@pytest.mark.asyncio
async def test_wrong_name(app, minimal_repo):
    r = await add_environment(app, repo=minimal_repo, name="#WRONG_NAME#")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_build_response_contains_uid(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    data = r.json()
    assert "uid" in data
    assert data["uid"]
    await wait_for_image(image_name=image_name)


@pytest.mark.asyncio
async def test_delete_by_uid(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    uid = r.json()["uid"]
    await wait_for_image(image_name=image_name)

    r = await remove_environment(app, image_name=uid)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_rebuild_unknown_uid_returns_404(app, minimal_repo):
    r = await add_environment(
        app,
        repo=minimal_repo,
        name="ghost",
        ref="HEAD",
        uid=str(uuid4()),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_rebuild_with_mismatched_name_returns_400(app, minimal_repo):
    uid = uuid4()
    _insert_image_row(
        uid=uid,
        name="original:HEAD",
        display_name="original",
        status=BuildStatusType.BUILT,
        repo=minimal_repo,
    )
    r = await add_environment(
        app,
        repo=minimal_repo,
        name="otherword",
        ref="HEAD",
        uid=str(uid),
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_rebuild_while_building_returns_409(app, minimal_repo):
    uid = uuid4()
    _insert_image_row(
        uid=uid,
        name="busy:HEAD",
        display_name="busy",
        status=BuildStatusType.BUILDING,
        repo=minimal_repo,
    )
    r = await add_environment(
        app,
        repo=minimal_repo,
        name="busy",
        ref="HEAD",
        uid=str(uid),
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_rebuild_existing_env_reuses_uid(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    uid = r.json()["uid"]
    await wait_for_image(image_name=image_name)

    # Remove the locally built image so wait_for_image after rebuild has
    # something to look for.
    async with Docker() as docker:
        try:
            await docker.images.delete(image_name, force=True)
        except DockerError:
            pass

    r = await add_environment(
        app, repo=minimal_repo, name=name, ref=ref, uid=uid
    )
    assert r.status_code == 200
    assert r.json()["uid"] == uid
    image = await wait_for_image(image_name=image_name)
    assert image is not None

    # Confirm the DB row was kept in place rather than duplicated.
    row = _read_image_row(UUID(uid))
    assert row is not None
