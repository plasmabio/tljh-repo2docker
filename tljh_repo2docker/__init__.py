from aiodocker import Docker
from dockerspawner import DockerSpawner
from jinja2 import BaseLoader, Environment
from jupyter_client.localinterfaces import public_ips
from jupyterhub.traitlets import ByteSpecification
from traitlets import Unicode
from traitlets.config import Configurable

try:
    from tljh.hooks import hookimpl
except ModuleNotFoundError:
    hookimpl = None

from .docker import list_images

# Default CPU period
# See: https://docs.docker.com/config/containers/resource_constraints/#limit-a-containers-access-to-memory#configure-the-default-cfs-scheduler
CPU_PERIOD = 100_000

TLJH_R2D_ADMIN_SCOPE = "custom:tljh_repo2docker:admin"


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
        try:
            images = await self.list_images()
        except ValueError:
            images = []

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
        label = {
            **(image.get("ContainerConfig", {}).get("Labels") or {}),
            **(image.get("Config", {}).get("Labels") or {}),
        }

        mem_limit = label.get("tljh_repo2docker.mem_limit", None)
        cpu_limit = label.get("tljh_repo2docker.cpu_limit", None)

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


if hookimpl:

    @hookimpl
    def tljh_custom_jupyterhub_config(c):
        # hub
        c.JupyterHub.hub_ip = public_ips()[0]
        c.JupyterHub.cleanup_servers = False
        c.JupyterHub.spawner_class = Repo2DockerSpawner

        # spawner
        c.DockerSpawner.allowed_images = "*"
        c.DockerSpawner.cmd = ["jupyterhub-singleuser"]
        c.DockerSpawner.pull_policy = "Never"
        c.DockerSpawner.remove = True

    @hookimpl
    def tljh_extra_hub_pip_packages():
        return ["dockerspawner~=14.0", "jupyter_client>=6.1,<8", "aiodocker~=0.21"]

else:
    tljh_custom_jupyterhub_config = None
    tljh_extra_hub_pip_packages = None
