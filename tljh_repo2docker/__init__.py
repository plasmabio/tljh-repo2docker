import os
from typing import Any, Coroutine, Optional

from aiodocker import Docker
from dockerspawner import DockerSpawner
from jinja2 import Environment, BaseLoader
from jupyter_client.localinterfaces import public_ips
from jupyterhub.handlers.static import CacheControlStaticFilesHandler
from jupyterhub.traitlets import ByteSpecification
from tljh.hooks import hookimpl
from tljh.configurer import load_config
from traitlets import Unicode
from traitlets.config import Configurable

from .builder import BuildHandler
from .docker import list_images
from .servers import ServersHandler
from .images import ImagesHandler
from .logs import LogsHandler

# Default CPU period
# See: https://docs.docker.com/config/containers/resource_constraints/#limit-a-containers-access-to-memory#configure-the-default-cfs-scheduler
CPU_PERIOD = 100_000


class SpawnerMixin(Configurable):

    """
    Mixin for spawners that derive from DockerSpawner, to use local Docker images
    built with tljh-repo2docker.

    Call `set_limits` in the spawner `start` method to set the memory and cpu limits.
    """

    image_form_template = Unicode(
        """
        <style>
            #image-list {
                max-height: 600px;
                overflow: auto;
            }
            .image-info {
                font-weight: normal;
            }
        </style>
        <div class='form-group' id='image-list'>
        {% for image in image_list %}
        <label for='image-item-{{ loop.index0 }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='image' id='image-item-{{ loop.index0 }}' value='{{ image.image_name }}' />
            </div>
            <div class='col-md-11'>
                <strong>{{ image.display_name }}</strong>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        Repository:
                    </div>
                    <div class='col-md-8'>
                        <a href="{{ image.repo }}" target="_blank">{{ image.repo }}</a>
                    </div>
                </div>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        Reference:
                    </div>
                    <div class='col-md-8'>
                        <a href="{{ image.repo }}/tree/{{ image.ref }}" target="_blank">{{ image.ref }}</a>
                    </div>
                </div>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        Memory Limit (GB):
                    </div>
                    <div class='col-md-8'>
                        <strong>{{ image.mem_limit | replace("G", "") }}</strong>
                    </div>
                </div>
                <div class='row image-info'>
                    <div class='col-md-4'>
                        CPU Limit:
                    </div>
                    <div class='col-md-8'>
                        <strong>{{ image.cpu_limit }}</strong>
                    </div>
                </div>
            </div>
        </label>
        {% endfor %}
        </div>
        """,
        config=True,
        help="""
        Jinja2 template for constructing the list of images shown to the user.
        """,
    )

    async def list_images(self):
        """
        Return the list of available images
        """
        return await list_images()

    async def get_options_form(self):
        """
        Override the default form to handle the case when there is only one image.
        """
        images = await self.list_images()

        # make default limits human readable
        default_mem_limit = self.mem_limit
        if isinstance(default_mem_limit, (float, int)):
            # default memory unit is in GB
            default_mem_limit /= ByteSpecification.UNIT_SUFFIXES["G"]
            if float(default_mem_limit).is_integer():
                default_mem_limit = int(default_mem_limit)

        default_cpu_limit = self.cpu_limit
        if default_cpu_limit and float(default_cpu_limit).is_integer():
            default_cpu_limit = int(default_cpu_limit)

        # add memory and cpu limits
        for image in images:
            image["mem_limit"] = image["mem_limit"] or default_mem_limit
            image["cpu_limit"] = image["cpu_limit"] or default_cpu_limit

        image_form_template = Environment(loader=BaseLoader).from_string(
            self.image_form_template
        )
        return image_form_template.render(image_list=images)

    async def set_limits(self):
        """
        Set the user environment limits if they are defined in the image
        """
        imagename = self.user_options.get("image")
        async with Docker() as docker:
            image = await docker.images.inspect(imagename)

        mem_limit = image["ContainerConfig"]["Labels"].get(
            "tljh_repo2docker.mem_limit", None
        )
        cpu_limit = image["ContainerConfig"]["Labels"].get(
            "tljh_repo2docker.cpu_limit", None
        )

        # override the spawner limits if defined in the image
        if mem_limit:
            self.mem_limit = mem_limit
        if cpu_limit:
            self.cpu_limit = float(cpu_limit)

        if self.cpu_limit:
            self.extra_host_config.update(
                {
                    "cpu_period": CPU_PERIOD,
                    "cpu_quota": int(float(CPU_PERIOD) * self.cpu_limit),
                }
            )


class Repo2DockerSpawner(SpawnerMixin, DockerSpawner):
    """
    A custom spawner for using local Docker images built with tljh-repo2docker.
    """

    async def start(self, *args, **kwargs):
        await self.set_limits()
        return await super().start(*args, **kwargs)


@hookimpl
def tljh_custom_jupyterhub_config(c):
    # hub
    c.JupyterHub.hub_ip = public_ips()[0]
    c.JupyterHub.cleanup_servers = False
    c.JupyterHub.spawner_class = Repo2DockerSpawner

    # add extra templates for the service UI
    c.JupyterHub.template_paths.insert(
        0, os.path.join(os.path.dirname(__file__), "templates")
    )

    # spawner
    c.DockerSpawner.cmd = ["jupyterhub-singleuser"]
    c.DockerSpawner.pull_policy = "Never"
    c.DockerSpawner.remove = True

    # fetch limits from the TLJH config
    tljh_config = load_config()
    limits = tljh_config["limits"]
    cpu_limit = limits["cpu"]
    mem_limit = limits["memory"]

    c.JupyterHub.tornado_settings.update(
        {"default_cpu_limit": cpu_limit, "default_mem_limit": mem_limit}
    )

    machine_profiles = limits.get("machine_profiles", [])

    c.JupyterHub.tornado_settings.update(
        {"machine_profiles": machine_profiles}
    )

    # register the handlers to manage the user images
    c.JupyterHub.extra_handlers.extend(
        [
            (r"servers", ServersHandler),
            (r"environments", ImagesHandler),
            (r"api/environments", BuildHandler),
            (r"api/environments/([^/]+)/logs", LogsHandler),
            (
                r"environments-static/(.*)",
                CacheControlStaticFilesHandler,
                {"path": os.path.join(os.path.dirname(__file__), "static")},
            ),
        ]
    )


@hookimpl
def tljh_extra_hub_pip_packages():
    return ["dockerspawner~=0.11", "jupyter_client~=6.1", "aiodocker~=0.19"]
