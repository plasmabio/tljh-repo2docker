import pytest

from .utils import remove_docker_image


@pytest.fixture(scope="session")
def minimal_repo():
    return "https://github.com/plasmabio/tljh-repo2docker-test-binder"


@pytest.fixture(scope="session")
def minimal_repo_uppercase():
    return "https://github.com/plasmabio/TLJH-REPO2DOCKER-TEST-BINDER"


@pytest.fixture(autouse=True)
async def remove_all_test_images(image_name, generated_image_name):
    await remove_docker_image(image_name)
    await remove_docker_image(generated_image_name)
