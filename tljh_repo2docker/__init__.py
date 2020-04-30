import os
import sys

from dockerspawner import DockerSpawner
from jupyter_client.localinterfaces import public_ips
from tljh.hooks import hookimpl
from tljh.configurer import load_config, CONFIG_FILE
from traitlets import default, validate

from .images import list_images, client

# Default CPU period
# See: https://docs.docker.com/config/containers/resource_constraints/#limit-a-containers-access-to-memory#configure-the-default-cfs-scheduler
CPU_PERIOD = 100_000


class TLJHDockerSpawner(DockerSpawner):
    def set_limits(self):
        imagename = self.user_options.get("image")
        image = client.images.get(imagename)
        mem_limit = image.labels.get("tljh_repo2docker.mem_limit", None)
        cpu_limit = image.labels.get("tljh_repo2docker.cpu_limit", None)
        self.mem_limit = mem_limit or self.mem_limit
        self.cpu_limit = float(cpu_limit) if cpu_limit else self.cpu_limit
        if self.cpu_limit:
            self.extra_host_config = {
                "cpu_period": CPU_PERIOD,
                "cpu_quota": int(float(CPU_PERIOD) * self.cpu_limit),
            }

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
        option_t = '<option value="{image_name}" {selected}>{display_name}</option>'
        options = [
            option_t.format(
                image_name=image["image_name"],
                display_name=image["display_name"],
                selected="selected" if image["image_name"] == self.image else "",
            )
            for image in images
        ]
        return """
        <label for="image">Select an image:</label>
        <select class="form-control" name="image" required autofocus>
        {options}
        </select>
        """.format(
            options=options
        )

    def start(self, *args, **kwargs):
        self.set_limits()
        return super().start(*args, **kwargs)


@hookimpl
def tljh_custom_jupyterhub_config(c):
    # hub
    c.JupyterHub.hub_ip = public_ips()[0]
    c.JupyterHub.cleanup_servers = False
    c.JupyterHub.spawner_class = TLJHDockerSpawner

    # add extra templates for the service UI
    c.JupyterHub.template_paths.insert(
        0, os.path.join(os.path.dirname(__file__), "templates")
    )

    # spawner
    c.TLJHDockerSpawner.cmd = ["jupyterhub-singleuser"]
    c.TLJHDockerSpawner.pull_policy = "Never"

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
