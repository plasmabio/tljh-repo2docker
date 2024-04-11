import asyncio
import json
from uuid import UUID

from tornado import web
from tornado.iostream import StreamClosedError

from .base import BaseHandler, require_admin_role
from .database.schemas import BuildStatusType


class BinderHubLogsHandler(BaseHandler):
    """
    Expose a handler to follow the build logs.
    """

    @web.authenticated
    @require_admin_role
    async def get(self, image_uid: str):
        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")

        db_context, image_db_manager = self.get_db_handlers()
        if not db_context or not image_db_manager:
            return

        async with db_context() as db:

            image = await image_db_manager.read(db, UUID(image_uid))
            if not image:
                await self._emit({"phase": "error", "message": "Image not found"})
                return

            status = image.status
            if status == BuildStatusType.FAILED:
                await self._emit({"phase": "error", "message": image.log})
                return
            if status == BuildStatusType.BUILT:
                await self._emit({"phase": "built", "message": image.log})
                return

            current_log_length = len(image.log)
            await self._emit({"phase": "log", "message": image.log})
            time = 0
            TIME_OUT = 3600
            while time < TIME_OUT:
                time += 1
                await asyncio.sleep(1)
                image = await image_db_manager.read(db, UUID(image_uid))
                if len(image.log) > current_log_length:
                    await self._emit(
                        {"phase": "log", "message": image.log[current_log_length:]}
                    )
                    current_log_length = len(image.log)
                status = image.status
                if status == BuildStatusType.FAILED:
                    await self._emit({"phase": "error", "message": ""})
                    break
                if status == BuildStatusType.BUILT:
                    await self._emit({"phase": "built", "message": ""})
                    break

    async def _emit(self, msg):
        try:
            self.write(f"data: {json.dumps(msg)}\n\n")
            await self.flush()
        except StreamClosedError:
            self.log.warning("Stream closed while handling %s", self.request.uri)
            raise web.Finish()
