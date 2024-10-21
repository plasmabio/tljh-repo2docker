"""
This file is only used for local development
and overrides some of the default values from the plugin.
"""

from pathlib import Path
from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE
import sys


HERE = Path(__file__).parent

c.JupyterHub.allow_named_servers = True
c.JupyterHub.services.extend(
    [
        {
            "name": "tljhrepo2docker",
            "url": "http://r2d-svc:6789",
            "command": [
                sys.executable,
                "-m",
                "tljh_repo2docker",
                "--ip",
                "0.0.0.0",
                "--port",
                "6789",
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
        ],
        "services": ["tljhrepo2docker"],
    },
    {
        "name": "tljh-repo2docker-service-admin",
        "users": [],  # List of users having admin right on tljh-repo2docker
        "scopes": [TLJH_R2D_ADMIN_SCOPE],
    },
    {
        "name": "user",
        "scopes": [
            "self",
            # access to the env page
            "access:services!service=tljhrepo2docker",
        ],
    },
]
