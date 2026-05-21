from datetime import datetime
import json
import re
from urllib.parse import quote
from uuid import UUID, uuid4

from aiodocker import Docker
from jupyterhub.utils import url_path_join
from tornado import web

from .base import BaseHandler, require_admin_role
from .database.schemas import (
    BuildStatusType,
    DockerImageCreateSchema,
    DockerImageUpdateSchema,
    ImageMetadataType,
)

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"

# Max time we'll keep the BinderHub SSE connection open for a single build.
# Builds longer than this should be killed; this also bounds DB session reuse.
BUILD_STREAM_TIMEOUT = 60 * 60  # 1h

# Caps for the buffered build log (chars). The BinderHub SSE stream can emit
# arbitrarily many messages, so without these bounds images.log could grow
# without limit and exhaust the DB. Total persisted log size is at most
# MAX_LOG_HEAD + MAX_LOG_TAIL plus the truncation marker.
MAX_LOG_HEAD = 32 * 1024
MAX_LOG_TAIL = 32 * 1024
TRUNCATION_MARKER = "\n[...truncated...]\n"


class _BoundedLog:
    """Append-only log buffer that keeps the first MAX_LOG_HEAD chars and
    the most recent MAX_LOG_TAIL chars."""

    def __init__(self) -> None:
        self._head = ""
        self._tail = ""

    def append(self, chunk: str) -> None:
        if len(self._head) < MAX_LOG_HEAD:
            room = MAX_LOG_HEAD - len(self._head)
            self._head += chunk[:room]
            chunk = chunk[room:]
        if chunk:
            self._tail = (self._tail + chunk)[-MAX_LOG_TAIL:]

    def render(self) -> str:
        if not self._tail:
            return self._head
        return self._head + TRUNCATION_MARKER + self._tail


class BinderHubBuildHandler(BaseHandler):
    """
    Handle requests to build user environments using BinderHub service
    """

    @web.authenticated
    @require_admin_role
    async def delete(self):
        """
        Method to handle the deletion of a specific image.

        Note:
        - Only users with admin role or with `TLJH_R2D_ADMIN_SCOPE` scope can access it.
        """

        data = self.get_json_body()
        try:
            uid = UUID(data["name"])
        except (KeyError, ValueError, AttributeError, TypeError):
            raise web.HTTPError(400, "Invalid image identifier")

        db_context, image_db_manager = self.get_db_handlers()
        if not db_context or not image_db_manager:
            return

        deleted = False
        async with db_context() as db:
            image = await image_db_manager.read(db, uid)
            if image:
                try:
                    async with Docker() as docker:
                        await docker.images.delete(image.name)
                except Exception:
                    # The DB row is the source of truth for the UI; the Docker
                    # image may already be gone or unreachable. Keep going with
                    # the DB delete but record what happened.
                    self.log.exception(
                        "Failed to delete Docker image %s, continuing with DB delete",
                        image.name,
                    )
                deleted = await image_db_manager.delete(db, uid)

        self.set_header("content-type", "application/json")
        if deleted:
            self.set_status(200)
            self.finish(json.dumps({"status": "ok"}))
        else:
            self.set_status(404)
            self.finish(json.dumps({"status": "error"}))

    @web.authenticated
    @require_admin_role
    async def post(self):
        """
        Method to handle the creation of a new environment based on provided specifications.
        As the build progresses, it updates the build log in the database and checks for completion.

        Note:
        - Only users with admin role or with `TLJH_R2D_ADMIN_SCOPE` scope can access it.
        """
        data = self.get_json_body()

        repo = data["repo"]
        ref = data["ref"]
        name = data["name"].lower()
        memory = data["memory"]
        cpu = data["cpu"]
        provider = data["provider"]
        node_selector = data.get("node_selector", {})
        owner = self.get_current_user().get("name", "unknow")

        if len(repo) == 0:
            raise web.HTTPError(400, "Repository is empty")

        if name and not re.match(IMAGE_NAME_RE, name):
            raise web.HTTPError(
                400,
                f"The name of the environment is restricted to the following characters: {IMAGE_NAME_RE}",
            )

        if memory:
            try:
                if float(memory) <= 0:
                    raise web.HTTPError(400, "Memory Limit must be a positive number")
            except ValueError:
                raise web.HTTPError(400, "Memory Limit must be a number")

        if cpu:
            try:
                if float(cpu) <= 0:
                    raise web.HTTPError(400, "CPU Limit must be a positive number")
            except ValueError:
                raise web.HTTPError(400, "CPU Limit must be a number")

        binder_url = self.settings.get("binderhub_url")
        quoted_repo = quote(repo, safe="")
        url = url_path_join(binder_url, "build", provider, quoted_repo, ref)

        params = {"build_only": "true"}

        db_context, image_db_manager = self.get_db_handlers()
        if not db_context or not image_db_manager:
            return

        creation_date = datetime.now().strftime("%d/%m/%Y")

        uid = uuid4()
        image_in = DockerImageCreateSchema(
            uid=uid,
            name=name,
            status=BuildStatusType.BUILDING,
            log="",
            image_meta=ImageMetadataType(
                display_name=name,
                repo=repo,
                ref=ref,
                cpu_limit=cpu,
                mem_limit=memory,
                creation_date=creation_date,
                owner=owner,
                node_selector=node_selector,
            ),
        )
        self.set_status(200)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"uid": str(uid), "status": "ok"}))

        async with db_context() as db:
            await image_db_manager.create(db, image_in)

        log_buf = _BoundedLog()
        # Open a short-lived session per write so a slow BinderHub stream
        # cannot keep a DB transaction open for the entire build.
        async with self.client.stream(
            "GET", url, params=params, timeout=BUILD_STREAM_TIMEOUT
        ) as r:
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                json_log = json.loads(line.split(":", 1)[1])
                phase = json_log.get("phase", None)
                message = json_log.get("message", "")
                if phase != "unknown":
                    log_buf.append(message)
                update_data = DockerImageUpdateSchema(uid=uid, log=log_buf.render())
                stop = False
                if phase == "ready" or phase == "built":
                    image_name = json_log.get("imageName", name)
                    update_data.status = BuildStatusType.BUILT
                    update_data.name = image_name
                    stop = True
                elif phase == "failed":
                    update_data.status = BuildStatusType.FAILED
                    stop = True
                async with db_context() as db:
                    await image_db_manager.update(db, update_data)
                if stop:
                    return
