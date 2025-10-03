from uuid import UUID

from jupyterhub.utils import url_path_join
from tornado import web

from tljh_repo2docker.docker import get_image_metadata

from .base import BaseHandler
from typing import List, Dict


class ServersAPIHandler(BaseHandler):
    """
    Handler to manage single servers
    """

    @web.authenticated
    async def post(self):
        data = self.get_json_body()

        user_data = await self.fetch_user()
        server_data: List[Dict] = user_data.all_spawners() or []

        all_server_names = []
        for it in server_data:
            if not isinstance(it, dict):
                continue
            it_name = it.get("name", "")
            all_server_names.append(it_name)

        image_name_or_uid = data.get("imageName", None)
        user_name = data.get("userName", None)
        server_name = data.get("serverName", "")
        if user_name != self.current_user["name"]:
            raise web.HTTPError(403, "Unauthorized")
        if not image_name_or_uid:
            raise web.HTTPError(400, "Missing image name")

        image_metadata = {}
        image_name = image_name_or_uid
        if self.use_binderhub:
            db_context, image_db_manager = self.get_db_handlers()
            if not db_context or not image_db_manager:
                raise web.HTTPError(500, "Server error, missing database")

            async with db_context() as db:
                image = await image_db_manager.read(db, UUID(image_name_or_uid))
                if not image:
                    raise web.HTTPError(404, "Image not found")
                image_name = image.name
                image_metadata = image.image_meta.model_dump()
        else:
            image_metadata = await get_image_metadata(image_name)

        post_data = {"image": image_name, "metadata": image_metadata}
        path = ""
        if len(server_name) > 0:
            path = url_path_join("users", user_name, "servers", server_name)
        else:
            path = url_path_join("users", user_name, "server")
        try:
            response = await self.client.post(path, json=post_data, timeout=10)
            response.raise_for_status()
            return response
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
