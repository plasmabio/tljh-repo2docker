import asyncio
import json
from uuid import UUID

from tornado import web
from tornado.iostream import StreamClosedError

from .base import BaseHandler, require_admin_role
from .database.schemas import BuildStatusType

TIME_OUT = 3600


class LogsHandler(BaseHandler):
    """
    Expose a handler to follow the build logs.
    Reads from the database (polling for BUILDING, immediate for BUILT/FAILED).
    Accepts both a UUID or an image name as the identifier.
    """

    @web.authenticated
    @require_admin_role
    async def get(self, name):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")

        db_context = self.settings.get("db_context")
        image_db_manager = self.settings.get("image_db_manager")

        if not db_context or not image_db_manager:
            raise web.HTTPError(500, "Database not configured")

        image = await self._lookup(name, db_context, image_db_manager)
        if not image:
            raise web.HTTPError(404, f"No logs for image: {name}")

        status = image.status

        if status == BuildStatusType.FAILED:
            await self._emit({"phase": "error", "message": image.log or ""})
            return

        if status == BuildStatusType.BUILT:
            await self._emit({"phase": "built", "message": image.log or ""})
            return

        # BUILDING: send what we have, then poll for new lines
        current_log_length = len(image.log or "")
        await self._emit({"phase": "log", "message": image.log or ""})

        elapsed = 0
        while elapsed < TIME_OUT:
            elapsed += 1
            await asyncio.sleep(1)
            image = await self._lookup(name, db_context, image_db_manager)
            if not image:
                await self._emit({"phase": "error", "message": "Image not found"})
                return
            log = image.log or ""
            if len(log) > current_log_length:
                await self._emit({"phase": "log", "message": log[current_log_length:]})
                current_log_length = len(log)
            status = image.status
            if status == BuildStatusType.FAILED:
                await self._emit({"phase": "error", "message": ""})
                return
            if status == BuildStatusType.BUILT:
                await self._emit({"phase": "built", "message": ""})
                return

        await self._emit({"phase": "error", "message": "Build timed out"})

    async def _lookup(self, name, db_context, image_db_manager):
        """Look up an image by UUID or image name."""
        async with db_context() as db:
            try:
                return await image_db_manager.read(db, UUID(name))
            except ValueError:
                return await image_db_manager.read_by_image_name(db, name)

    async def _emit(self, msg):
        try:
            self.write(f"data: {json.dumps(msg)}\n\n")
            await self.flush()
        except StreamClosedError:
            self.log.warning("Stream closed while handling %s", self.request.uri)
            raise web.Finish()
