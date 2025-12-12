import asyncio

import pytest
import sqlalchemy as sa
from aiodocker import Docker, DockerError

from tljh_repo2docker.database.model import DockerImageSQL

from ..utils import add_environment, remove_environment, wait_for_image


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
    images_db = db_session.execute(sa.select(DockerImageSQL)).scalars().first()
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
    "memory, cpu, node_selector",
    [
        ("abcded", "", {"key": "value"}),
        ("", "abcde", {"key": "value"}),
    ],
)
async def test_wrong_limits(app, minimal_repo, image_name, memory, cpu, node_selector):
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
    assert "must be a number" in r.text


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
