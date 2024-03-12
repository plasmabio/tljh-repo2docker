# tljh-repo2docker

![Github Actions Status](https://github.com/plasmabio/tljh-repo2docker/workflows/Tests/badge.svg)

TLJH plugin to build and use Docker images as user environments. The Docker images are built using [`repo2docker`](https://repo2docker.readthedocs.io/en/latest/).

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
    --plugin git+https://github.com/plasmabio/tljh-repo2docker@master
```

Refer to [The Littlest JupyterHub documentation](http://tljh.jupyter.org/en/latest/topic/customizing-installer.html?highlight=plugins#installing-tljh-plugins)
for more info on installing TLJH plugins.

## Usage

### List the environments

The _Environments_ page shows the list of built environments, as well as the ones currently being built:

![environments](https://user-images.githubusercontent.com/591645/80962805-056df500-8e0e-11ea-81ab-6efc1c97432d.png)

### Add a new environment

Just like on [Binder](https://mybinder.org), new environments can be added by clicking on the _Add New_ button and providing a URL to the repository. Optional names, memory, and CPU limits can also be set for the environment:

![add-new](https://user-images.githubusercontent.com/591645/80963115-9fce3880-8e0e-11ea-890b-c9b928f7edb1.png)

### Follow the build logs

Clicking on the _Logs_ button will open a new dialog with the build logs:

![logs](https://user-images.githubusercontent.com/591645/82306574-86f18580-99bf-11ea-984b-4749ddde15e7.png)

### Select an environment

Once ready, the environments can be selected from the JupyterHub spawn page:

![select-env](https://user-images.githubusercontent.com/591645/81152248-10e22d00-8f82-11ea-9b5f-5831d8f7d085.png)

### Private Repositories

`tljh-repo2docker` also supports building environments from private repositories.

It is possible to provide the `username` and `password` in the `Credentials` section of the form:

![image](https://user-images.githubusercontent.com/591645/107362654-51567480-6ad9-11eb-93be-74d3b1c37828.png)

On GitHub and GitLab, a user might have to first create an access token with `read` access to use as the password:

![image](https://user-images.githubusercontent.com/591645/107350843-39c3bf80-6aca-11eb-8b82-6fa95ba4c7e4.png)

### Set CPU and Memory via machine profiles

Instead of entering directly the CPU and Memory value, `tljh-repo2docker` can be configured with pre-defined machine profiles and users can only choose from the available options. The following snippet will add 3 machines with labels `Small`, `Medium` and `Large` to the profile list:

```python
from tljh.configurer import apply_config, load_config

tljh_config = load_config()
tljh_config["limits"]["machine_profiles"] = [
    {"label": "Small", "cpu": 2, "memory": 2},
    {"label": "Medium", "cpu": 4, "memory": 4},
    {"label": "Large", "cpu": 8, "memory": 8},
]
apply_config(tljh_config, c)
```

![image](https://github.com/plasmabio/tljh-repo2docker/assets/4451292/c1f0231e-a02d-41dc-85e0-97a97ffa0311)

### Extra documentation

`tljh-repo2docker` is currently developed as part of the [Plasma project](https://github.com/plasmabio/plasma).

See the [Plasma documentation on user environments](https://docs.plasmabio.org/en/latest/environments/index.html) for more info.

## Building JupyterHub-ready images

See: https://repo2docker.readthedocs.io/en/latest/howto/jupyterhub_images.html

## Run Locally

Check out the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) to set up a local environment.
