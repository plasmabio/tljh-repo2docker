"""
This file is only used for local development
and overrides some of the default values from the plugin.
"""

from kubespawner import KubeSpawner
from pathlib import Path
from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE
from tornado import web
from traitlets import Bool, Unicode
from traitlets.config import Configurable
import sys


"""
Helpers for creating BinderSpawners
This file is defined in binderhub/binderspawner_mixin.py and is copied to here
"""


class BinderSpawnerMixin(Configurable):
    """
    Mixin to convert a JupyterHub container spawner to a BinderHub spawner

    Container spawner must support the following properties that will be set
    via spawn options:
    - image: Container image to launch
    - token: JupyterHub API token
    """

    def __init__(self, *args, **kwargs):
        # Is this right? Is it possible to having multiple inheritance with both
        # classes using traitlets?
        # https://stackoverflow.com/questions/9575409/calling-parent-class-init-with-multiple-inheritance-whats-the-right-way
        # https://github.com/ipython/traitlets/pull/175
        super().__init__(*args, **kwargs)

    auth_enabled = Bool(
        False,
        help="""
        Enable authenticated binderhub setup.

        Requires `jupyterhub-singleuser` to be available inside the repositories
        being built.
        """,
        config=True,
    )

    cors_allow_origin = Unicode(
        "",
        help="""
        Origins that can access the spawned notebooks.

        Sets the Access-Control-Allow-Origin header in the spawned
        notebooks. Set to '*' to allow any origin to access spawned
        notebook servers.

        See also BinderHub.cors_allow_origin in binderhub config
        for controlling CORS policy for the BinderHub API endpoint.
        """,
        config=True,
    )

    def get_args(self):
        if self.auth_enabled:
            args = super().get_args()
        else:
            args = [
                "--ip=0.0.0.0",
                f"--port={self.port}",
                f"--NotebookApp.base_url={self.server.base_url}",
                f"--NotebookApp.token={self.user_options['token']}",
                "--NotebookApp.trust_xheaders=True",
            ]
            if self.default_url:
                args.append(f"--NotebookApp.default_url={self.default_url}")

            if self.cors_allow_origin:
                args.append("--NotebookApp.allow_origin=" + self.cors_allow_origin)
            # allow_origin=* doesn't properly allow cross-origin requests to single files
            # see https://github.com/jupyter/notebook/pull/5898
            if self.cors_allow_origin == "*":
                args.append("--NotebookApp.allow_origin_pat=.*")
            args += self.args
            # ServerApp compatibility: duplicate NotebookApp args
            for arg in list(args):
                if arg.startswith("--NotebookApp."):
                    args.append(arg.replace("--NotebookApp.", "--ServerApp."))
        return args

    def start(self):
        if not self.auth_enabled:
            if "token" not in self.user_options:
                raise web.HTTPError(400, "token required")
            if "image" not in self.user_options:
                raise web.HTTPError(400, "image required")
        if "image" in self.user_options:
            self.image = self.user_options["image"]
        return super().start()

    def get_env(self):
        env = super().get_env()
        if "repo_url" in self.user_options:
            env["BINDER_REPO_URL"] = self.user_options["repo_url"]
        for key in (
            "binder_ref_url",
            "binder_launch_host",
            "binder_persistent_request",
            "binder_request",
        ):
            if key in self.user_options:
                env[key.upper()] = self.user_options[key]
        return env


class BinderSpawner(BinderSpawnerMixin, KubeSpawner):
    pass


HERE = Path(__file__).parent

c.JupyterHub.spawner_class = BinderSpawner

c.JupyterHub.allow_named_servers = True

c.JupyterHub.services.extend(
    [
        {"name": "binder", "url": "http://tljh-binderhub-service"},
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
                "--TljhRepo2Docker.binderhub_url",
                "http://tljh-binderhub-service/services/binder",
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
