from inspect import isawaitable

from tornado import web

from .base import BaseHandler, require_admin_role
from .docker import list_containers, list_images


class EnvironmentsHandler(BaseHandler):
    """
    Handler to show the list of environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def get(self):
        images = await list_images()
        containers = await list_containers()
        result = self.render_template(
            "images.html",
            images=images + containers,
            default_mem_limit=self.settings.get("default_mem_limit"),
            default_cpu_limit=self.settings.get("default_cpu_limit"),
            machine_profiles=self.settings.get("machine_profiles", []),
        )
        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)
