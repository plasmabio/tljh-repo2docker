# tljh-repo2docker

![Github Actions Status](https://github.com/plasmabio/tljh-repo2docker/workflows/Tests/badge.svg)

TLJH plugin providing a JupyterHub service to build and use Docker images as user environments. The Docker images are built using [`repo2docker`](https://repo2docker.readthedocs.io/en/latest/).

## Requirements

This plugin requires [The Littlest JupyterHub](https://tljh.jupyter.org) 1.0 or later (running on JupyterHub 4+).

## Installation

During the [TLJH installation process](http://tljh.jupyter.org/en/latest/install/index.html), use the following post-installation script:

```bash
#!/bin/bash

# install Docker
sudo apt update && sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt update && sudo apt install -y docker-ce

# pull the repo2docker image
sudo docker pull quay.io/jupyterhub/repo2docker:main

# install TLJH 1.0
curl https://tljh.jupyter.org/bootstrap.py
  | sudo python3 - \
    --version 1.0.0 \
    --admin test:test \
    --plugin tljh-repo2docker
```

Refer to [The Littlest JupyterHub documentation](http://tljh.jupyter.org/en/latest/topic/customizing-installer.html?highlight=plugins#installing-tljh-plugins)
for more info on installing TLJH plugins.

## Configuration

This Python package is designed for deployment as [a service managed by JupyterHub](https://jupyterhub.readthedocs.io/en/stable/reference/services.html#launching-a-hub-managed-service). The service runs its own Tornado server. Requests will be forwarded to it by the JupyterHub internal proxy from the standard URL `https://{my-hub-url}/services/my-service/`.

The available settings for this service are:

- `port`: Port of the service; defaults to 6789
- `ip`: Internal IP of the service; defaults to 127.0.0.1
- `default_memory_limit`: Default memory limit of a user server; defaults to `None`
- `default_cpu_limit`: Default CPU limit of a user server; defaults to `None`
- `machine_profiles`: Instead of entering directly the CPU and Memory value, `tljh-repo2docker` can be configured with pre-defined machine profiles and users can only choose from the available option; defaults to `[]`

This service requires the following scopes : `read:users`, `admin:servers` and `read:roles:users`. Here is an example of registering `tljh_repo2docker`'s service with JupyterHub

```python
# jupyterhub_config.py

from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE
import sys

c.JupyterHub.services.extend(
    [
        {
            "name": "tljh_repo2docker",
            "url": "http://127.0.0.1:6789", # URL must match the `ip` and `port` config
            "command": [
                sys.executable,
                "-m",
                "tljh_repo2docker",
                "--ip",
                "127.0.0.1",
                "--port",
                "6789"
            ],
            "oauth_no_confirm": True,
        }
    ]
)
# Set required scopes for the service and users
c.JupyterHub.load_roles = [
    {
        "description": "Role for tljh_repo2docker service",
        "name": "tljh-repo2docker-service",
        "scopes": ["read:users", "admin:servers", "read:roles:users"],
        "services": ["tljh_repo2docker"],
    },
    {
        "name": "user",
        "scopes": [
            "self",
            # access to the serve page
            "access:services!service=tljh_repo2docker",
        ],
    },
]
```

By default, only users with an admin role can access the environment builder page and APIs, by leveraging the RBAC system of JupyterHub, non-admin users can also be granted the access right.

Here is an example of the configuration

```python
# jupyterhub_config.py

from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE
import sys

c.JupyterHub.services.extend(
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
                "6789"
            ],
            "oauth_no_confirm": True,
            "oauth_client_allowed_scopes": [
                TLJH_R2D_ADMIN_SCOPE, # Allows this service to check if users have its admin scope.
            ],
        }
    ]
)

c.JupyterHub.custom_scopes = {
    TLJH_R2D_ADMIN_SCOPE: {
        "description": "Admin access to tljh_repo2docker",
    },
}

c.JupyterHub.load_roles = [
    ... # Other role settings
    {
        "name": 'tljh-repo2docker-service-admin',
        "users": ["alice"],
        "scopes": [TLJH_R2D_ADMIN_SCOPE],
    },
]

```

## Usage

### List the environments

The _Environments_ page shows the list of built environments, as well as the ones currently being built:

![environments](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/tests/ui.test.ts-snapshots/environment-list-linux.png)

### Add a new environment

Just like on [Binder](https://mybinder.org), new environments can be added by clicking on the _Add New_ button and providing a URL to the repository. Optional names, memory, and CPU limits can also be set for the environment:

![add-new](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/tests/ui.test.ts-snapshots/environment-dialog-linux.png)

### Follow the build logs

Clicking on the _Logs_ button will open a new dialog with the build logs:

![logs](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/tests/ui.test.ts-snapshots/environment-console-linux.png)

### Select an environment

Once ready, the environments can be selected from the JupyterHub spawn page:

![select-env](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/tests/ui.test.ts-snapshots/servers-dialog-linux.png)

### Private Repositories

`tljh-repo2docker` also supports building environments from private repositories.

It is possible to provide the `username` and `password` in the `Credentials` section of the form:

![image](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/tests/ui.test.ts-snapshots/environment-dialog-linux.png)

On GitHub and GitLab, a user might have to first create an access token with `read` access to use as the password:

![image](https://user-images.githubusercontent.com/591645/107350843-39c3bf80-6aca-11eb-8b82-6fa95ba4c7e4.png)

### Machine profiles

Instead of entering directly the CPU and Memory value, `tljh-repo2docker` can be configured with pre-defined machine profiles and users can only choose from the available options. The following configuration will add 3 machines with labels Small, Medium and Large to the profile list:

```python
c.JupyterHub.services.extend(
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
                "--machine_profiles",
                '{"label": "Small", "cpu": 2, "memory": 2}',
                "--machine_profiles",
                '{"label": "Medium", "cpu": 4, "memory": 4}',
                "--machine_profiles",
                '{"label": "Large", "cpu": 8, "memory": 8}'

            ],
            "oauth_no_confirm": True,
        }
    ]
)
```

![image](https://github.com/plasmabio/tljh-repo2docker/assets/4451292/c1f0231e-a02d-41dc-85e0-97a97ffa0311)

### Extra documentation

`tljh-repo2docker` is currently developed as part of the [Plasma project](https://github.com/plasmabio/plasma).

See the [Plasma documentation on user environments](https://docs.plasmabio.org/en/latest/environments/index.html) for more info.

## Building JupyterHub-ready images

See: https://repo2docker.readthedocs.io/en/latest/howto/jupyterhub_images.html

## Run Locally

Check out the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) to set up a local environment.
