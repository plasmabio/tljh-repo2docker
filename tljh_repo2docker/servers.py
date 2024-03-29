from inspect import isawaitable

import requests
from tornado import web
from jupyterhub.utils import url_path_join
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

    @web.authenticated
    async def post(self):
        data = self.get_json_body()
        image_name = data.get("imageName", None)
        user_name = data.get("userName", None)
        server_name = data.get("serverName", "")
        if user_name != self.current_user["name"]:
            raise web.HTTPError(403, "Unauthorized")
        if not image_name:
            raise web.HTTPError(400, "Missing image name")

        post_data = {"image": image_name}

        path = ""
        if len(server_name) > 0:
            path = url_path_join("users", user_name, "servers", server_name)
        else:
            path = url_path_join("users", user_name, "server")
        try:
            response = await self.client.post(path, json=post_data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
