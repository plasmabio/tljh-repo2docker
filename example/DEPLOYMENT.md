# Deploy `tljh_repo2docker` as a hub-managed service

A guide to help you add `tljh_repo2docker` service to a JupyterHub deployment from scratch.

> [!NOTE]
> In this guide, we assume you have experience with setting up JupyterHub on Kubernetes. We will use [Zero to JupyterHub](https://z2jh.jupyter.org/en/latest/index.html#zero-to-jupyterhub-with-kubernetes) as the base JupyterHub deployment.

## Create a new JupyterHub docker image.

Since we are going to use `tljh_repo2docker` as a hub-managed service, the python package needs to be installed into the base JupyterHub image. We will build a custom image based on the [zero-to-jupyterhub image](https://quay.io/repository/jupyterhub/k8s-hub). Here is a minimal docker file to build the custom image:

```docker
FROM quay.io/jupyterhub/k8s-hub:3.3.7

USER root
RUN python3 -m pip install "tljh-repo2docker>=2.0.0a1"

USER jovyan
```

Then you can build and push the image to the registry of your choice:

```bash
docker build . -t k8s-hub-tljh:xxx
```

## Installing JupyterHub and tljh_repo2docker with Helm chart.

With a Kubernetes cluster available and Helm installed, we can install our custom JupyterHub image in the Kubernetes cluster using the JupyterHub Helm chart. You can find a chart template at [example/tljh_r2d](./tljh_r2d).

### Using local build-backend via `repo2docker`.

To build images using the local docker engine, modify the `value.yaml` file with the following content:

```yaml
# values.yaml
jupyterhub:
  enabled: true
  hub:
    image:
      name: k8s-hub-tljh
      tag: xxx
    extraFiles:
      my_jupyterhub_config:
        mountPath: /usr/local/etc/jupyterhub/jupyterhub_config.d/jupyterhub_config.py
```

Now install the chart with the JupyterHub config from `jupyterhub_config_local.py`:

```bash
helm upgrade --install tljh . --wait --set-file jupyterhub.hub.extraFiles.my_jupyterhub_config.stringData=./jupyterhub_config_local.py
```

### Using binderhub service as build-backend.

To use binderhub as the build-backend, you need to deploy [binderhub service](https://binderhub-service.readthedocs.io/en/latest/tutorials/install.html) and config `tljh-repo2docker` to use this service. Here is an example of the configuration:

```yaml
#values.yaml

jupyterhub:
  enabled: true
  hub:
    image:
      name: k8s-hub-binhderhub-tljh
      tag: xxx
    config:
      BinderSpawner:
        auth_enabled: true
    extraFiles:
      my_jupyterhub_config:
        mountPath: /usr/local/etc/jupyterhub/jupyterhub_config.d/jupyterhub_config.py

binderhub-service:
  config:
    BinderHub:
      base_url: /services/binder
      use_registry: true
      image_prefix: ''
      enable_api_only_mode: true

  buildPodsRegistryCredentials:
    server: 'https://index.docker.io/v1/' # Set image registry for pushing images
```

Now install the chart with the JupyterHub config from `jupyterhub_config_binderhub.py` and with image registry credentials passed via command line:

```bash
helm upgrade --install tljh . --wait --set-file jupyterhub.hub.extraFiles.my_jupyterhub_config.stringData=./jupyterhub_config_binderhub.py --set binderhub-service.buildPodsRegistryCredentials.password=xxx --set binderhub-service.buildPodsRegistryCredentials.username=xxx
```

Now you should have a working instance of JupyterHub with `tljh_repo2docker` service deployed.
