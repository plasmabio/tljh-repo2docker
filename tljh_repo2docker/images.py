import json

from aiodocker import Docker
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.utils import admin_only
from tornado import web


async def list_images():
    docker = Docker()
    """
    Retrieve local images built by repo2docker
    """
    r2d_images = await docker.images.list(
        filters=json.dumps({"dangling": ["false"], "label": ["repo2docker.ref"]})
    )
    await docker.close()
    images = [
        {
            "repo": image["Labels"]["repo2docker.repo"],
            "ref": image["Labels"]["repo2docker.ref"],
            "image_name": image["Labels"]["tljh_repo2docker.image_name"],
            "display_name": image["Labels"]["tljh_repo2docker.display_name"],
            "mem_limit": image["Labels"]["tljh_repo2docker.mem_limit"],
            "cpu_limit": image["Labels"]["tljh_repo2docker.cpu_limit"],
            "status": "built",
        }
        for image in r2d_images
        if "tljh_repo2docker.image_name" in image["Labels"]
    ]
    return images


async def list_containers():
    docker = Docker()
    """
    Retrieve the list of local images being built by repo2docker.
    Images are built in a Docker container.
    """
    r2d_containers = await docker.containers.list(
        filters=json.dumps({"label": ["repo2docker.ref"]})
    )
    await docker.close()
    containers = [
        {
            "repo": container["Labels"]["repo2docker.repo"],
            "ref": container["Labels"]["repo2docker.ref"],
            "image_name": container["Labels"]["repo2docker.build"],
            "display_name": container["Labels"]["tljh_repo2docker.display_name"],
            "mem_limit": container["Labels"]["tljh_repo2docker.mem_limit"],
            "cpu_limit": container["Labels"]["tljh_repo2docker.cpu_limit"],
            "status": "building",
        }
        for container in r2d_containers
        if "repo2docker.build" in container["Labels"]
    ]
    return containers


class ImagesHandler(BaseHandler):
    """
    Handler to show the list of environments as Docker images
    """

    @web.authenticated
    @admin_only
    async def get(self):
        images = await list_images()
        containers = await list_containers()
        self.write(
            self.render_template(
                "images.html",
                images=images + containers,
                default_mem_limit=self.settings.get("default_mem_limit"),
                default_cpu_limit=self.settings.get("default_cpu_limit"),
            )
        )
