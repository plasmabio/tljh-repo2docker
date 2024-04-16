import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from traitlets.config import Config

from tljh_repo2docker import tljh_custom_jupyterhub_config
from tljh_repo2docker.database.model import DockerImageSQL

ROOT = Path(__file__).parents[3]

binderhub_service_name = "binder"
binderhub_config = ROOT / "ui-tests" / "binderhub_config.py"
tljh_repo2docker_config = ROOT / "ui-tests" / "tljh_repo2docker_binderhub.py"

db_url = "sqlite:///tljh_repo2docker.sqlite"


@pytest.fixture(scope="module")
def generated_image_name():
    return "https-3a-2f-2fgithub-2ecom-2fplasmabio-2ftljh-2drepo2docker-2dtest-2dbinder-3f035a:06bb545ab3a2888477cbddfed0ea77eae313cfed"


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
                    "--binderhub_url",
                    "http://localhost:8585/@/space%20word/services/binder/",
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


@pytest.fixture(scope="session")
def db_session():
    engine = sa.create_engine(db_url)
    Session = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    session = Session()
    yield session
    session.query(DockerImageSQL).delete()
    session.commit()
    session.close()
