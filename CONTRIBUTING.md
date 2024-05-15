# Setting up a dev environment

It is possible to test the project locally without installing TLJH. Instead we use the `jupyterhub` Python package.

## Requirements

`Docker` is used as a `Spawner` to start the user servers, and is then required to run the project locally.

Check out the official Docker documentation to know how to install Docker on your machine: https://docs.docker.com/install/linux/docker-ce/ubuntu/

## Create a virtual environment

Using `mamba` / `conda`:

```bash
mamba create -n tljh-repo2docker -c conda-forge python nodejs
conda activate tljh-repo2docker
```

Alternatively, with Python's built in `venv` module, you can create a virtual environment with:

```bash
python3 -m venv .
source bin/activate
```

## Install the development requirements

```bash
python -m pip install -r dev-requirements.txt

# dev install of the package
python -m pip install -e .

# Install CHP (https://github.com/jupyterhub/configurable-http-proxy)
npm -g install configurable-http-proxy
```

## Pull the repo2docker Docker image

User environments are built with `repo2docker` running in a Docker container. To pull the Docker image:

```bash
docker pull quay.io/jupyterhub/repo2docker:main
```

## Run

Finally, start `jupyterhub` with local build backend:

```bash
python -m jupyterhub -f ui-tests/jupyterhub_config_local.py --debug
```

or using `binderhub` build backend

```bash
python -m jupyterhub -f ui-tests/jupyterhub_config_binderhub.py --debug
```

Open https://localhost:8000 in a web browser.

## Tests

Tests are located in the [tests](./tests) folder.

To run the tests:

```bash
python -m pytest --cov
```
