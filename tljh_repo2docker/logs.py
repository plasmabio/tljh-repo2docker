import json

from jupyterhub.apihandlers import APIHandler
from jupyterhub.utils import admin_only
from tornado import web
from tornado.iostream import StreamClosedError

from .docker import logs


class LogsHandler(APIHandler):
    """
    Expose a handler to follow the build logs.
    """

    @web.authenticated
    @admin_only
    async def get(self, name):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")

        async for line in logs(name):
            try:
                await self._emit({"phase": "log", "message": line})
            except StreamClosedError:
                raise web.Finish()

        await self._emit({"phase": "built", "message": "built"})

    async def _emit(self, msg):
        self.write(f"data: {json.dumps(msg)}\n\n")
        await self.flush()
