from inspect import isawaitable
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.utils import admin_only
from tornado import web

from .docker import list_containers, list_images


class ImagesHandler(BaseHandler):
    """
    Handler to show the list of environments as Docker images
    """

    @web.authenticated
    @admin_only
    async def get(self):
        images = await list_images()
        containers = await list_containers()
        result = self.render_template(
            "images.html",
            images=images + containers,
            default_mem_limit=self.settings.get("default_mem_limit"),
            default_cpu_limit=self.settings.get("default_cpu_limit"),
        )
        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)
