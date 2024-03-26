from inspect import isawaitable

from tornado import web

from .base import BaseHandler
from .docker import list_images


class ServersHandler(BaseHandler):
    """
    Handler to show the list of servers available
    """

    @web.authenticated
    async def get(self):
        images = await list_images()
        user_data = await self.fetch_user()

        server_data = user_data.all_spawners()

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
