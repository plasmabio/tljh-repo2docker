import asyncio
import os
import sys

import pytest

from aiodocker import Docker, DockerError
from jupyterhub.tests.conftest import (
    io_loop,
    event_loop,
    db,
    pytest_collection_modifyitems,
)
from jupyterhub.tests.mocking import MockHub
from tljh_repo2docker import Repo2DockerSpawner
from tljh_repo2docker.builder import BuildHandler
from tljh_repo2docker.images import ImagesHandler


@pytest.fixture(scope='module')
def minimal_repo():
    return "https://github.com/jtpio/test-binder"


@pytest.fixture(scope='module')
def image_name():
    return "tljh-repo2docker-test:master"


@pytest.mark.asyncio
@pytest.fixture(scope='module')
async def remove_test_image(image_name):
    docker = Docker()
    try:
        await docker.images.delete(image_name)
    except DockerError:
        pass
    await docker.close()


@pytest.fixture(scope='module')
def app(request, io_loop):
    """
    Adapted from:
    https://github.com/jupyterhub/jupyterhub/blob/8a3790b01ff944c453ffcc0486149e2a58ffabea/jupyterhub/tests/conftest.py#L74
    """
    mocked_app = MockHub.instance()
    mocked_app.spawner_class = Repo2DockerSpawner
    mocked_app.template_paths.insert(
        0, os.path.join(os.path.dirname(__file__), "../tljh_repo2docker", "templates")
    )
    mocked_app.extra_handlers.extend([
        (r"environments", ImagesHandler),
        (r"api/environments", BuildHandler),
    ])

    async def make_app():
        await mocked_app.initialize([])
        await mocked_app.start()

    def fin():
        # disconnect logging during cleanup because pytest closes captured FDs prematurely
        mocked_app.log.handlers = []
        MockHub.clear_instance()
        try:
            mocked_app.stop()
        except Exception as e:
            print("Error stopping Hub: %s" % e, file=sys.stderr)

    request.addfinalizer(fin)
    io_loop.run_sync(make_app)
    return mocked_app
