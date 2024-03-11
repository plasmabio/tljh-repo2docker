import json

from aiodocker import Docker
from jupyterhub.apihandlers import APIHandler
from jupyterhub.scopes import needs_scope
from tornado import web
from tornado.iostream import StreamClosedError


class LogsHandler(APIHandler):
    """
    Expose a handler to follow the build logs.
    """
    @web.authenticated
    @needs_scope('admin-ui')
    async def get(self, name):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")

        async with Docker() as docker:
            containers = await docker.containers.list(
                filters=json.dumps({"label": [f"repo2docker.build={name}"]})
            )

            if not containers:
                raise web.HTTPError(404, f"No logs for image: {name}")

            async for line in containers[0].log(stdout=True, stderr=True, follow=True):
                await self._emit({"phase": "log", "message": line})

        await self._emit({"phase": "built", "message": "built"})

    async def _emit(self, msg):
        try:
            self.write(f"data: {json.dumps(msg)}\n\n")
            await self.flush()
        except StreamClosedError:
            self.log.warning("Stream closed while handling %s", self.request.uri)
            raise web.Finish()
