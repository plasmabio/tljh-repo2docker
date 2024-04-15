"""
A development config to test BinderHub locally.

If you are running BinderHub manually (not via JupyterHub) run
`python -m binderhub -f binderhub_config.py`

Override the external access URL for JupyterHub by setting the
environment variable JUPYTERHUB_EXTERNAL_URL
Host IP is needed in a few places
"""

import os

from binderhub.build_local import LocalRepo2dockerBuild
from binderhub.quota import LaunchQuota


c.BinderHub.debug = True
c.BinderHub.auth_enabled = True
c.BinderHub.enable_api_only_mode = True

use_registry = bool(os.getenv("BINDERHUB_USE_REGISTRY", False))
c.BinderHub.use_registry = use_registry

if use_registry:
    c.BinderHub.image_prefix = os.getenv(
        "BINDERHUB_IMAGE_PREFIX", ""
    )  # https://binderhub.readthedocs.io/en/latest/zero-to-binderhub/setup-binderhub.html#id2
    c.DockerRegistry.auth_config_url = "https://index.docker.io/v1/"

    c.BuildExecutor.push_secret = "*"  #

c.BinderHub.builder_required = False

c.BinderHub.build_class = LocalRepo2dockerBuild
c.BinderHub.launch_quota_class = LaunchQuota

c.BinderHub.hub_url_local = "http://localhost:8000"
# c.BinderHub.enable_api_only_mode = True

# Assert that we're running as a managed JupyterHub service
# (otherwise c.BinderHub.hub_api_token is needed)
assert os.getenv("JUPYTERHUB_API_TOKEN")

c.BinderHub.base_url = os.getenv("JUPYTERHUB_SERVICE_PREFIX")
c.BinderHub.hub_url = os.getenv("JUPYTERHUB_BASE_URL")
