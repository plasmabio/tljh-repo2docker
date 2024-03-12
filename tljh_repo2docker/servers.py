from inspect import isawaitable
from typing import Any, Dict
from jupyterhub.orm import Spawner
from jupyterhub.handlers.base import BaseHandler
from tornado import web

from .docker import list_images


class ServersHandler(BaseHandler):
    """
    Handler to show the list of servers available
    """

    @web.authenticated
    async def get(self):
        images = await list_images()
        user = self.current_user
        if user.running:
            # trigger poll_and_notify event in case of a server that died
            await user.spawner.poll_and_notify()
        auth_state = await user.get_auth_state()
        named_spawners = user.all_spawners(include_default=False)
        server_data = []
        for sp in named_spawners:
            server_data.append(
                self._spawner_to_server_data(sp, user)
            )
        try:
            named_server_limit = await self.get_current_user_named_server_limit()
        except Exception:
            named_server_limit = 0
        result = self.render_template(
            "servers.html",
            images=images,
            allow_named_servers=self.allow_named_servers,
            named_server_limit_per_user=named_server_limit,
            server_data=server_data,
            default_server_data=self._spawner_to_server_data(user.spawner, user),
            auth_state=auth_state,
        )

        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)

    def _spawner_to_server_data(self, sp: Spawner, user: Any) -> Dict:
        data = {
            "name": sp.name,
        }
        try:
            data["url"] = user.server_url(sp.name)
        except Exception:
            data["url"] = ""
        try:
            data["last_activity"] = sp.last_activity.isoformat() + "Z"
        except Exception:
            data["last_activity"] = ""

        try:
            data["active"] = sp.active
        except Exception:
            data["active"] = False

        try:
            if sp.user_options:
                data["user_options"] = sp.user_options
            else:
                data["user_options"] = {}
        except Exception:
            data["user_options"] = {}
        return data
