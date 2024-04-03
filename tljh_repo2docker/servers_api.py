from jupyterhub.utils import url_path_join
from tornado import web

from .base import BaseHandler


class ServersAPIHandler(BaseHandler):
    """
    Handler to manage single servers
    """

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
        except Exception:
            raise web.HTTPError(500, "Server error")

    @web.authenticated
    async def delete(self):
        data = self.get_json_body()
        user_name = data.get("userName", None)
        server_name = data.get("serverName", "")
        if user_name != self.current_user["name"]:
            raise web.HTTPError(403, "Unauthorized")

        path = ""
        post_data = {}
        if len(server_name) > 0:
            path = url_path_join("users", user_name, "servers", server_name)
            post_data = {"remove": True}
        else:
            path = url_path_join("users", user_name, "server")
        try:
            response = await self.client.request("DELETE", path, json=post_data)
            response.raise_for_status()
        except Exception:
            raise web.HTTPError(500, "Server error")
