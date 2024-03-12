import pytest

from aiodocker import Docker, DockerError
from tljh_repo2docker import tljh_custom_jupyterhub_config
from traitlets.config import Config


async def remove_docker_image(image_name):
    async with Docker() as docker:
        try:
            await docker.images.delete(image_name, force=True)
        except DockerError:
            pass


@pytest.fixture(scope='module')
def minimal_repo():
    return "https://github.com/plasmabio/tljh-repo2docker-test-binder"


@pytest.fixture(scope='module')
def minimal_repo_uppercase():
    return "https://github.com/plasmabio/TLJH-REPO2DOCKER-TEST-BINDER"


@pytest.fixture(scope='module')
def generated_image_name():
    return "plasmabio-tljh-repo2docker-test-binder:HEAD"


@pytest.fixture(scope='module')
def image_name():
    return "tljh-repo2docker-test:HEAD"


@pytest.fixture
async def app(hub_app):
    config = Config()
    tljh_custom_jupyterhub_config(config)

    app = await hub_app(config=config)
    return app


@pytest.fixture(autouse=True)
async def remove_all_test_images(image_name, generated_image_name, app):
    yield
    await remove_docker_image(image_name)
    await remove_docker_image(generated_image_name)
