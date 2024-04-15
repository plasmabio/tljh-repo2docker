from pathlib import Path
import sys

import pytest
from traitlets.config import Config

from tljh_repo2docker import tljh_custom_jupyterhub_config

ROOT = Path(__file__).parents[3]

binderhub_service_name = "binder"
binderhub_config = ROOT / "ui-tests" / "binderhub_config.py"
tljh_repo2docker_config = ROOT / "ui-tests" / "tljh_repo2docker_binderhub.py"


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
                "name": binderhub_service_name,
                "admin": True,
                "command": [
                    sys.executable,
                    "-m",
                    "binderhub",
                    f"--config={binderhub_config}",
                ],
                "url": "http://localhost:8585",
                "oauth_client_id": "service-binderhub",
                "oauth_no_confirm": True,
            },
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
                    "--config",
                    f"{tljh_repo2docker_config}",
                ],
                "oauth_no_confirm": True,
            },
        ]
    )

    config.JupyterHub.load_roles = [
        {
            "description": "Role for tljh_repo2docker service",
            "name": "tljh-repo2docker-service",
            "scopes": [
                "read:users",
                "read:roles:users",
                "admin:servers",
                "access:services!service=binder",
            ],
            "services": ["tljh_repo2docker"],
        }
    ]

    app = await hub_app(config=config)
    return app
