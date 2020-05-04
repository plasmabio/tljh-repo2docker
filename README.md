# tljh-repo2docker

TLJH plugin to build and use Docker images as user environments. The Docker images are built using [`repo2docker`](https://repo2docker.readthedocs.io/en/latest/).


## Installation

Add `--plugin git+https://github.com/plasmabio/plasmabio@master` to the TLJH installer command to install `tljh-repo2docker`.

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

![select-env](https://user-images.githubusercontent.com/591645/80963143-abb9fa80-8e0e-11ea-94c1-ddd7962f7283.png)

### Extra documentation

`tljh-repo2docker` is currently developed as part of the [PlasmaBio project](https://github.com/plasmabio).

See the [PlasmaBio documentation on user environments](https://docs.plasmabio.org/en/latest/environments/index.html) for more info.

## Building JupyterHub-ready images

See: https://repo2docker.readthedocs.io/en/latest/howto/jupyterhub_images.html

## Run Locally

Check out the instructions in [CONTRIBUTING.md](./CONTRIBUTING.md) to setup a local environment.
