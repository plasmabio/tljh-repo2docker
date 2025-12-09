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
        uid = UUID(data["name"])

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
                    pass
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
        if len(repo) == 0:
            raise web.HTTPError(400, "Repository is empty")

        if name and not re.match(IMAGE_NAME_RE, name):
            raise web.HTTPError(
                400,
                f"The name of the environment is restricted to the following characters: {IMAGE_NAME_RE}",
            )

        if memory:
            try:
                float(memory)
            except ValueError:
                raise web.HTTPError(400, "Memory Limit must be a number")

        if cpu:
            try:
                float(cpu)
            except ValueError:
                raise web.HTTPError(400, "CPU Limit must be a number")

        binder_url = self.settings.get("binderhub_url")
        quoted_repo = quote(repo, safe="")
        url = url_path_join(binder_url, "build", provider, quoted_repo, ref)

        params = {"build_only": "true"}

        db_context, image_db_manager = self.get_db_handlers()
        if not db_context or not image_db_manager:
            return

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
                node_selector=node_selector,
            ),
        )
        self.set_status(200)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"uid": str(uid), "status": "ok"}))

        log = ""
        async with db_context() as db:
            await image_db_manager.create(db, image_in)
            async with self.client.stream("GET", url, params=params, timeout=None) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data:"):
                        json_log = json.loads(line.split(":", 1)[1])
                        phase = json_log.get("phase", None)
                        message = json_log.get("message", "")
                        if phase != "unknown":
                            log += message
                        update_data = DockerImageUpdateSchema(uid=uid, log=log)
                        stop = False
                        if phase == "ready" or phase == "built":
                            image_name = json_log.get("imageName", name)
                            update_data.status = BuildStatusType.BUILT
                            update_data.name = image_name
                            stop = True
                        elif phase == "failed":
                            update_data.status = BuildStatusType.FAILED
                            stop = True
                        await image_db_manager.update(db, update_data)
                        if stop:
                            return
