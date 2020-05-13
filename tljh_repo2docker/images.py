import os

from concurrent.futures import ThreadPoolExecutor

import docker

from jupyterhub.handlers.base import BaseHandler
from jupyterhub.services.auth import HubAuthenticated
from jupyterhub.utils import admin_only, url_path_join
from tornado import ioloop, web
from tornado.concurrent import run_on_executor
from tornado.options import define, options, parse_command_line

from .builder import client


def list_images():
    """
    Retrieve local images built by repo2docker
    """
    r2d_images = [
        image
        for image in client.images.list(
            filters={"dangling": False, "label": ["repo2docker.ref"]}
        )
    ]
    images = [
        {
            "repo": image.labels["repo2docker.repo"],
            "ref": image.labels["repo2docker.ref"],
            "image_name": image.labels["tljh_repo2docker.image_name"],
            "display_name": image.labels["tljh_repo2docker.display_name"],
            "mem_limit": image.labels["tljh_repo2docker.mem_limit"],
            "cpu_limit": image.labels["tljh_repo2docker.cpu_limit"],
            "status": "built",
        }
        for image in r2d_images
        if "tljh_repo2docker.image_name" in image.labels
    ]
    return images


def list_containers():
    """
    Retrieve data for the local images being built by repo2docker.
    Images are built in a Docker container.
    """
    r2d_containers = [
        container
        for container in client.containers.list(filters={"label": ["repo2docker.ref"]})
    ]
    containers = [
        {
            "repo": container.labels["repo2docker.repo"],
            "ref": container.labels["repo2docker.ref"],
            "image_name": container.labels["repo2docker.build"],
            "display_name": container.labels["tljh_repo2docker.display_name"],
            "mem_limit": container.labels["tljh_repo2docker.mem_limit"],
            "cpu_limit": container.labels["tljh_repo2docker.cpu_limit"],
            "status": "building",
        }
        for container in r2d_containers
        if "repo2docker.build" in container.labels
    ]
    return containers


class ImagesHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=5)

    @admin_only
    @run_on_executor
    def get(self):
        images = list_images() + list_containers()
        self.write(
            self.render_template("images.html",
                images=images,
                default_mem_limit=self.settings.get("default_mem_limit"),
                default_cpu_limit=self.settings.get("default_cpu_limit"),
            )
        )
