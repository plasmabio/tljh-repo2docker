"""
This file is only used for local development
and overrides some of the default values from the plugin.
"""

import getpass

from jupyterhub.auth import DummyAuthenticator
from tljh.configurer import apply_config, load_config
from tljh_repo2docker import tljh_custom_jupyterhub_config

c.JupyterHub.services = []

# set default limits in the TLJH config in memory
tljh_config = load_config()
tljh_config["limits"]["memory"] = "2G"
tljh_config["limits"]["cpu"] = 2
apply_config(tljh_config, c)

tljh_custom_jupyterhub_config(c)

c.JupyterHub.authenticator_class = DummyAuthenticator

user = getpass.getuser()
c.Authenticator.admin_users = {user, "alice"}
