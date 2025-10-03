from inspect import isawaitable
from typing import Dict, List

from tornado import web

from .base import BaseHandler
from .docker import list_images


class ServersHandler(BaseHandler):
    """
    Handler to show the list of servers available
    """

    @web.authenticated
    async def get(self):
        images = []
        if self.use_binderhub:
            images = await self.get_images_from_db()
        else:
            try:
                images = await list_images()
            except ValueError:
                pass

        user_data = await self.fetch_user()

        server_data: List[Dict] = user_data.all_spawners() or []

        db_context, image_db_manager = self.get_db_handlers()
        if db_context and image_db_manager:
            async with db_context() as db:
                for data in server_data:
                    if not isinstance(data, dict):
                        continue
                    user_options = data.get("user_options", {})
                    if not isinstance(user_options, dict):
                        continue
                    image_name = user_options.get("image", None)
                    if image_name:
                        db_data = await image_db_manager.read_by_image_name(
                            db, image_name
                        )
                        if db_data:
                            data["user_options"]["uid"] = str(db_data.uid)
                            data["user_options"][
                                "display_name"
                            ] = db_data.image_meta.display_name
        named_server_limit = 0
        result = self.render_template(
            "servers.html",
            images=images,
            allow_named_servers=True,
            named_server_limit_per_user=named_server_limit,
            server_data=server_data,
            default_server_data={},
            user_is_admin=True,
        )

        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)
