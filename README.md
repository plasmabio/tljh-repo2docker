# tljh-repo2docker

![Github Actions Status](https://github.com/plasmabio/tljh-repo2docker/workflows/CI/badge.svg)

TLJH plugin to build and use Docker images as user environments. The Docker images are built using [`repo2docker`](https://repo2docker.readthedocs.io/en/latest/).

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
sudo docker pull jupyter/repo2docker:master

# install TLJH
curl https://raw.githubusercontent.com/jupyterhub/the-littlest-jupyterhub/master/bootstrap/bootstrap.py \
  | sudo python3 - \
    --admin test:test \
    --plugin git+https://github.com/plasmabio/tljh-repo2docker@master
```

Refer to [The Littlest JupyterHub documentation](http://tljh.jupyter.org/en/latest/topic/customizing-installer.html?highlight=plugins#installing-tljh-plugins)
for more info on installing TLJH plugins.


## Usage

### List the environments

The *Environments* page shows the list of built environments, as well as the ones currently being built:

![environments](https://user-images.githubusercontent.com/591645/80962805-056df500-8e0e-11ea-81ab-6efc1c97432d.png)

### Add a new environment

Just like on [Binder](https://mybinder.org), new environments can be added by clicking on the *Add New* button and providing a URL to the repository. Optional names, memory, and CPU limits can also be set for the environment:

![add-new](https://user-images.githubusercontent.com/591645/80963115-9fce3880-8e0e-11ea-890b-c9b928f7edb1.png)

### Select an environment

Once ready, the environments can be selected from the JupyterHub spawn page:

![select-env](https://user-images.githubusercontent.com/591645/81152248-10e22d00-8f82-11ea-9b5f-5831d8f7d085.png)

### Extra documentation

`tljh-repo2docker` is currently developed as part of the [Plasma project](https://github.com/plasmabio/plasma).

See the [Plasma documentation on user environments](https://docs.plasmabio.org/en/latest/environments/index.html) for more info.

## Building JupyterHub-ready images

See: https://repo2docker.readthedocs.io/en/latest/howto/jupyterhub_images.html

## Run Locally

Check out the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) to setup a local environment.
