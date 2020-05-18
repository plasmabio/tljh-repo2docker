import json

from jupyterhub.apihandlers import APIHandler
from jupyterhub.utils import admin_only
from tornado import web
from tornado.iostream import StreamClosedError

from .docker import logs


class LogsHandler(APIHandler):
    """
    Server build logs.
    """

    async def _emit(self, msg):
        self.write(f"data: {json.dumps(msg)}\n\n")
        await self.flush()

    @web.authenticated
    @admin_only
    async def get(self, name):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")

        async for line in logs(name):
            try:
                msg = {"phase": "log", "message": line}
                await self._emit(msg)
            except StreamClosedError:
                raise web.Finish()

        msg = {"phase": "built", "message": "built"}
        await self._emit(msg)
