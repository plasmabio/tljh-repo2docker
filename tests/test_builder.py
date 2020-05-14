import asyncio
import json
import os

import pytest

from aiodocker import Docker, DockerError
from jupyterhub.tests.utils import api_request


async def add_environment(app, minimal_repo, image_name):
    """Use the POST endpoint to add a new environment"""
    name, ref = image_name.split(":")
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(
            {"repo": minimal_repo, "ref": ref, "name": name, "memory": "", "cpu": "",}
        ),
    )
    return r


async def wait_for_image(image_name):
    """wait until an image is built"""
    count, retries = 0, 60 * 10
    image = None
    docker = Docker()
    while count < retries:
        await asyncio.sleep(1)
        try:
            image = await docker.images.inspect(image_name)
        except DockerError:
            count += 1
            continue
        else:
            break

    await docker.close()
    return image


async def remove_environment(app, image_name):
    """Use the DELETE endpoint to remove an environment"""
    r = await api_request(
        app, "environments", method="delete", data=json.dumps({"name": image_name,}),
    )
    return r


@pytest.mark.asyncio
async def test_add_environment(app, remove_test_image, minimal_repo, image_name):
    r = await add_environment(app, minimal_repo, image_name)
    assert r.status_code == 200
    image = await wait_for_image(image_name)
    assert (
        image["ContainerConfig"]["Labels"]["tljh_repo2docker.image_name"] == image_name
    )


@pytest.mark.asyncio
async def test_delete_environment(app, remove_test_image, minimal_repo, image_name):
    await add_environment(app, minimal_repo, image_name)
    image = await wait_for_image(image_name)
    r = await remove_environment(app, image_name)
    assert r.status_code == 200

    # make sure the image does not exist anymore
    docker = Docker()
    with pytest.raises(DockerError):
        await docker.images.inspect(image_name)
    await docker.close()


async def test_no_repo(app):
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(
            {
                "repo": "",
                "ref": "master",
                "name": "custom-name",
                "memory": "",
                "cpu": "",
            }
        ),
    )
    assert r.status_code == 400


@pytest.mark.parametrize(
    "memory, cpu", [("abcded", ""), ("", "abcde"),],
)
async def test_wrong_limits(app, memory, cpu):
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(
            {
                "repo": ".",
                "ref": "master",
                "name": "custom-name",
                "memory": memory,
                "cpu": cpu,
            }
        ),
    )
    assert r.status_code == 400
    assert "must be a number" in r.text
