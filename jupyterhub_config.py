"""
This file is only used for local development
and overrides some of the default values from the plugin.
"""

import getpass

from jupyterhub.auth import DummyAuthenticator
from tljh.configurer import apply_config, load_config
from tljh_repo2docker import tljh_custom_jupyterhub_config

c.JupyterHub.services = []

tljh_config = load_config()

# set default limits in the TLJH config in memory
# tljh_config["limits"]["memory"] = "2G"
# tljh_config["limits"]["cpu"] = 2

# set CPU and memory based on machine profiles
tljh_config["limits"]["machine_profiles"] = [
    {"label": "Small", "cpu": 2, "memory": 2},
    {"label": "Medium", "cpu": 4, "memory": 4},
    {"label": "Large", "cpu": 8, "memory": 8},
]

apply_config(tljh_config, c)

tljh_custom_jupyterhub_config(c)

c.JupyterHub.authenticator_class = DummyAuthenticator

user = getpass.getuser()
c.Authenticator.admin_users = {user, "alice"}
c.JupyterHub.allow_named_servers = True
c.JupyterHub.ip = "0.0.0.0"
