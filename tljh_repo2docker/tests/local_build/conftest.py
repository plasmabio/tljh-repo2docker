import sys

import pytest
import sqlalchemy as sa
from traitlets.config import Config

from tljh_repo2docker import tljh_custom_jupyterhub_config
from tljh_repo2docker.database.model import DockerImageSQL


@pytest.fixture(scope="module")
def generated_image_name():
    return "plasmabio-tljh-repo2docker-test-binder:HEAD"


@pytest.fixture(scope="module")
def image_name():
    return "tljh-repo2docker-test:HEAD"


@pytest.fixture
async def app(hub_app):
    config = Config()
    tljh_custom_jupyterhub_config(config)

    config.JupyterHub.services.extend(
        [
            {
                "name": "tljh_repo2docker",
                "url": "http://127.0.0.1:6789",
                "command": [
                    sys.executable,
                    "-m",
                    "tljh_repo2docker",
                    "--ip",
                    "127.0.0.1",
                    "--port",
                    "6789",
                ],
                "oauth_no_confirm": True,
            }
        ]
    )

    config.JupyterHub.load_roles = [
        {
            "description": "Role for tljh_repo2docker service",
            "name": "tljh-repo2docker-service",
            "scopes": ["read:users", "read:roles:users", "admin:servers"],
            "services": ["tljh_repo2docker"],
        }
    ]

    app = await hub_app(config=config)
    return app


@pytest.fixture(autouse=True)
def clean_db():
    """Delete all DB entries after each test to avoid cross-test contamination."""
    yield
    try:
        engine = sa.create_engine("sqlite:///tljh_repo2docker.sqlite")
        with engine.begin() as conn:
            conn.execute(sa.delete(DockerImageSQL))
        engine.dispose()
    except Exception:
        pass
