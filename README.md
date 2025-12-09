# tljh-repo2docker

![Github Actions Status](https://github.com/plasmabio/tljh-repo2docker/workflows/Tests/badge.svg)

This service allows users to create and use Docker images for their JupyterHub environments, using repositories from platforms like GitHub or GitLab. It can be deployed as part of The Littlest JupyterHub (TLJH) or as a standalone service in any JupyterHub setup.
The Docker images can be built locally using [`repo2docker`](https://repo2docker.readthedocs.io/en/latest/) or via the [`binderhub`](https://binderhub.readthedocs.io/en/latest/) service.

## Requirements

This plugin requires:

- JupyterHub 1.0 or later (running on JupyterHub 4+).
- Optional: [The Littlest JupyterHub](https://tljh.jupyter.org)

## Installation

### TLJH Installation (Optional)

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

# install TLJH 2.0
curl https://tljh.jupyter.org/bootstrap.py
  | sudo python3 - \
    --version 2.0.0 \
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
- `binderhub_url`: The optional URL of the `binderhub` service. If it is available, `tljh-repo2docker` will use this service to build images.
- `db_url`: The connection string of the database. `tljh-repo2docker` needs a database to store the image metadata. By default, it will create a `sqlite` database in the starting directory of the service. To use other databases (`PostgreSQL` or `MySQL`), users need to specify the connection string via this config and install the additional drivers (`asyncpg` or `aiomysql`).

This service requires the following scopes : `read:users`, `admin:servers` and `read:roles:users`. If `binderhub` service is used, ` access:services!service=binder`is also needed. Here is an example of registering `tljh_repo2docker`'s service with JupyterHub

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
        "scopes": [
            "read:users",
            "read:roles:users",
            "admin:servers",
            "access:services!service=binder",
        ],
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

![environments](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/local_snapshots/ui.test.ts/environment-list.png)

### Add a new environment

Just like on [Binder](https://mybinder.org), new environments can be added by clicking on the _Add New_ button and providing a URL to the repository. Optional names, memory, and CPU limits can also be set for the environment:

![add-new](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/local_snapshots/ui.test.ts/environment-dialog.png)

> [!NOTE]
> If the build backend is `binderhub` service, users need to select the [repository provider](https://binderhub.readthedocs.io/en/latest/developer/repoproviders.html) and can not specify the custom build arguments

![add-new-binderhub](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/binderhub_snapshots/ui.test.ts/environment-dialog.png)

### Follow the build logs

Clicking on the _Logs_ button will open a new dialog with the build logs:

![logs](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/local_snapshots/ui.test.ts/environment-console.png)

### Select an environment

Once ready, the environments can be selected from the JupyterHub spawn page:

![select-env](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/local_snapshots/ui.test.ts/servers-dialog.png)

### Private Repositories

`tljh-repo2docker` also supports building environments from private repositories.

It is possible to provide the `username` and `password` in the `Credentials` section of the form:

![image](https://raw.githubusercontent.com/plasmabio/tljh-repo2docker/master/ui-tests/local_snapshots/ui.test.ts/environment-dialog.png)

On GitHub and GitLab, a user might have to first create an access token with `read` access to use as the password:

![image](https://user-images.githubusercontent.com/591645/107350843-39c3bf80-6aca-11eb-8b82-6fa95ba4c7e4.png)

> [!NOTE]
> The `binderhub` build backend does not support configuring private repositories credentials from the interface.

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

### Node Selector

`tljh-repo2docker` allows specifying node selectors to control which Kubernetes nodes user environments are scheduled on. This can be useful for assigning workloads to specific nodes based on hardware characteristics like GPUs, SSD storage, or other node labels.

## Configuring Node Selectors

To configure node selectors, add the `--node_selector` argument in the service definition:

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
                "--node_selector",
                '{"gpu": {"description": "GPU availability", "values": ["yes", "no"]},'
                ' "ssd": {"description": "SSD availability", "values": ["yes", "no"]}}'
            ],
            "oauth_no_confirm": True,
        }
    ]
)
```

This ensures that workloads are scheduled only on nodes that meet the specified criteria.

## Accessing Node Selector in Spawner

The node selector information is passed through the metadata field of `user_options` and can be accessed in the `start` method of the spawner:

```python
user_options["metadata"]["node_selector"]
```

![node_selector](https://github.com/user-attachments/assets/046bee93-2c7c-4e42-a9a0-94ade6f191d9)

### Direct link to server

You can create a direct link to launch a single-user server with a custom environment using the following format:

```
https://<jupyterhub-server>/services/tljhrepo2docker/servers?name=foo&environment=bar
```

This link will start a server named `foo` using the `bar` environment. If a server with the same name already exists, it will open automatically; otherwise, `tljh-repo2docker` will initiate a new server for you.

### Extra documentation

`tljh-repo2docker` is currently developed as part of the [Plasma project](https://github.com/plasmabio/plasma).

See the [Plasma documentation on user environments](https://docs.plasmabio.org/en/latest/environments/index.html) for more info.

## Building JupyterHub-ready images

See: https://repo2docker.readthedocs.io/en/latest/howto/jupyterhub_images.html

## Deploy on Kubernetes cluster with Zero to JupyterHub

Check out the instructions in [DEPLOYMENT.md](./example/DEPLOYMENT.md) to set up the deployment.

## Run Locally

Check out the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) to set up a local environment.
