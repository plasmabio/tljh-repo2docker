import os
import sys

from dockerspawner import DockerSpawner
from jinja2 import Environment, BaseLoader
from jupyter_client.localinterfaces import public_ips
from tljh.hooks import hookimpl
from tljh.configurer import load_config, CONFIG_FILE
from traitlets import default, validate, Unicode
from traitlets.config import Configurable

from .images import list_images, client

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
                <input type='hidden' name='display_name' value='{{ image.display_name }}' />
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
        """
    )

    def image_whitelist(self, spawner):
        """
        Retrieve the list of available images
        """
        images = list_images()
        return {image["image_name"]: image["image_name"] for image in images}

    def options_form(self, spawner):
        """
        Override the default form to handle the case when there is only one image.
        """
        images = list_images()
        # add memory and cpu limits
        for image in images:
            image['mem_limit'] = image['mem_limit'] or spawner.mem_limit
            image['cpu_limit'] = image['cpu_limit'] or spawner.cpu_limit

        image_form_template = Environment(loader=BaseLoader).from_string(self.image_form_template)
        return image_form_template.render(image_list=images)

    def options_from_form(self, formdata):
        default_options = super().options_from_form(formdata)
        default_options['display_name'] = formdata['display_name'][0]
        return default_options

    def set_limits(self):
        """
        Set the user environment limits if they are defined in the image
        """
        imagename = self.user_options.get("image")
        image = client.images.get(imagename)
        mem_limit = image.labels.get("tljh_repo2docker.mem_limit", None)
        cpu_limit = image.labels.get("tljh_repo2docker.cpu_limit", None)

        # override the spawner limits if defined in the image
        if mem_limit:
            self.mem_limit = mem_limit
        if cpu_limit:
            self.cpu_limit = float(cpu_limit)

        if self.cpu_limit:
            self.extra_host_config = {
                "cpu_period": CPU_PERIOD,
                "cpu_quota": int(float(CPU_PERIOD) * self.cpu_limit),
            }


class R2DSpawner(SpawnerMixin, DockerSpawner):
    """
    A custom spawner for using local Docker images built with tljh-repo2docker.
    """

    def start(self, *args, **kwargs):
        self.set_limits()
        return super().start(*args, **kwargs)


@hookimpl
def tljh_custom_jupyterhub_config(c):
    # hub
    c.JupyterHub.hub_ip = public_ips()[0]
    c.JupyterHub.cleanup_servers = False
    c.JupyterHub.spawner_class = R2DSpawner

    # add extra templates for the service UI
    c.JupyterHub.template_paths.insert(
        0, os.path.join(os.path.dirname(__file__), "templates")
    )

    # spawner
    c.DockerSpawner.cmd = ["jupyterhub-singleuser"]
    c.DockerSpawner.pull_policy = "Never"

    # fetch limits from the TLJH config
    tljh_config = load_config()
    limits = tljh_config["limits"]
    cpu_limit = limits["cpu"]
    mem_limit = limits["memory"]

    # register the service to manage the user images
    c.JupyterHub.services.append(
        {
            "name": "environments",
            "admin": True,
            "url": "http://127.0.0.1:9988",
            "command": [
                sys.executable,
                "-m",
                "tljh_repo2docker.images",
                f"--default-mem-limit={mem_limit}",
                f"--default-cpu-limit={cpu_limit}",
            ],
        }
    )


@hookimpl
def tljh_extra_hub_pip_packages():
    return ["dockerspawner", "jupyter_client"]
