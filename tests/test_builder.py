import asyncio
import json
import os

import pytest

from aiodocker import Docker, DockerError
from jupyterhub.tests.utils import api_request


async def test_api_info(app):
    r = await api_request(app, "info")
    assert r.status_code == 200


async def test_add_environment(app, remove_test_image, minimal_repo, image_name):
    name, ref = image_name.split(':')
    r = await api_request(
        app,
        "environments",
        method="post",
        data=json.dumps(
            {
                "repo": minimal_repo,
                "ref": ref,
                "name": name,
                "memory": "",
                "cpu": "",
            }
        ),
    )
    assert r.status_code == 200

    # wait until build is finished
    count, retries = 0, 30
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

    assert image["ContainerConfig"]["Labels"]["tljh_repo2docker.image_name"] == image_name


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
