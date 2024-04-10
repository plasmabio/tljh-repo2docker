from inspect import isawaitable

from tornado import web

from .base import BaseHandler, require_admin_role
from .database.manager import ImagesDatabaseManager
from .docker import list_containers, list_images


class EnvironmentsHandler(BaseHandler):
    """
    Handler to show the list of environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def get(self):
        all_images = []
        if self.settings.get("binderhub_url", None):
            db_context = self.settings.get("db_context")
            image_db_manager: ImagesDatabaseManager = self.settings.get(
                "image_db_manager"
            )
            async with db_context() as db:
                docker_images = await image_db_manager.read_all(db)
                all_images = [
                    dict(
                        image_name=image.name,
                        uid=str(image.uid),
                        status=image.status,
                        **image.image_meta.model_dump()
                    )
                    for image in docker_images
                ]
            use_binderhub = True
        else:
            use_binderhub = False
            images = await list_images()
            containers = await list_containers()
            all_images = images + containers

        result = self.render_template(
            "images.html",
            images=all_images,
            default_mem_limit=self.settings.get("default_mem_limit"),
            default_cpu_limit=self.settings.get("default_cpu_limit"),
            machine_profiles=self.settings.get("machine_profiles", []),
            repo_providers=self.settings.get("repo_providers", None),
            use_binderhub=use_binderhub,
        )
        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)
