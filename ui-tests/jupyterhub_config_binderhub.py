"""
This file is only used for local development
and overrides some of the default values from the plugin.
"""

import os
from pathlib import Path
from jupyterhub.auth import DummyAuthenticator
from tljh.configurer import apply_config, load_config
from tljh_repo2docker import tljh_custom_jupyterhub_config, TLJH_R2D_ADMIN_SCOPE
import sys


HERE = Path(__file__).parent
tljh_config = load_config()
tljh_config["services"]["cull"]["enabled"] = False
apply_config(tljh_config, c)

tljh_custom_jupyterhub_config(c)
tljh_repo2docker_config = HERE / "tljh_repo2docker_binderhub.py"

c.JupyterHub.authenticator_class = DummyAuthenticator

c.JupyterHub.allow_named_servers = True
c.JupyterHub.ip = "0.0.0.0"


binderhub_service_name = "binder"
binderhub_config = HERE / "binderhub_config.py"


binderhub_environment = {}
for env_var in ["JUPYTERHUB_EXTERNAL_URL", "GITHUB_ACCESS_TOKEN"]:
    if os.getenv(env_var) is not None:
        binderhub_environment[env_var] = os.getenv(env_var)

c.JupyterHub.services.extend(
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
            "environment": binderhub_environment,
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
                "0.0.0.0",
                "--port",
                "6789",
                "--config",
                f"{tljh_repo2docker_config}",
            ],
            "oauth_no_confirm": True,
            "oauth_client_allowed_scopes": [
                TLJH_R2D_ADMIN_SCOPE,
            ],
        },
    ]
)

c.JupyterHub.custom_scopes = {
    TLJH_R2D_ADMIN_SCOPE: {
        "description": "Admin access to myservice",
    },
}

c.JupyterHub.load_roles = [
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
    },
    {
        "name": "tljh-repo2docker-service-admin",
        "users": ["alice"],
        "scopes": [TLJH_R2D_ADMIN_SCOPE],
    },
    {
        "name": "user",
        "scopes": [
            "self",
            # access to the env page
            "access:services!service=tljh_repo2docker",
        ],
    },
]
