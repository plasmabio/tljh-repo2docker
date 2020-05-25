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
from tljh_repo2docker import tljh_custom_jupyterhub_config
from traitlets import Bunch

class DummyConfig:
    def __getattr__(self, k):
        if k not in self.__dict__:
            self.__dict__[k] = Bunch()
        return self.__dict__[k]


async def remove_docker_image(image_name):
    async with Docker() as docker:
        try:
            await docker.images.delete(image_name, force=True)
        except DockerError:
            pass


@pytest.fixture(scope='module')
def minimal_repo():
    return "https://github.com/jtpio/test-binder"


@pytest.fixture(scope='module')
def minimal_repo_uppercase():
    return "https://github.com/jtpio/TEST-BINDER"


@pytest.fixture(scope='module')
def generated_image_name():
    return "jtpio-test-binder:master"


@pytest.fixture(scope='module')
def image_name():
    return "tljh-repo2docker-test:master"


@pytest.fixture(scope='module')
def app(request, io_loop):
    """
    Adapted from:
    https://github.com/jupyterhub/jupyterhub/blob/8a3790b01ff944c453ffcc0486149e2a58ffabea/jupyterhub/tests/conftest.py#L74
    """

    mocked_app = MockHub.instance()
    c = DummyConfig()
    c.JupyterHub = mocked_app
    tljh_custom_jupyterhub_config(c)

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


@pytest.fixture(autouse=True)
def remove_all_test_images(image_name, generated_image_name, io_loop):
    try:
        yield
    finally:
        async def _clean():
            await remove_docker_image(image_name)
            await remove_docker_image(generated_image_name)

        io_loop.run_sync(_clean)
