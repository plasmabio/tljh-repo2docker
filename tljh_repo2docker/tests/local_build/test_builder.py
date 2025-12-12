import pytest
from aiodocker import Docker, DockerError

from ..utils import add_environment, remove_environment, wait_for_image


@pytest.mark.asyncio
async def test_add_environment(app, minimal_repo, image_name):
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    image = await wait_for_image(image_name=image_name)
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
    )
    assert r.status_code == 400
    assert "must be a number" in r.text


@pytest.mark.asyncio
async def test_wrong_name(app, minimal_repo):
    r = await add_environment(app, repo=minimal_repo, name="#WRONG_NAME#")
    assert r.status_code == 400
