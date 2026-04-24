import json
import re
from datetime import datetime
from uuid import UUID, uuid4

from aiodocker import Docker, DockerError
from tornado import web

from .base import BaseHandler, require_admin_role
from .database.schemas import (
    BuildStatusType,
    DockerImageCreateSchema,
    DockerImageUpdateSchema,
    ImageMetadataType,
)
from .docker import build_image, compute_image_name

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"


class BuildHandler(BaseHandler):
    """
    Handle requests to build user environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def delete(self):
        data = self.get_json_body()
        image_name = data["name"]

        db_context = self.settings.get("db_context")
        image_db_manager = self.settings.get("image_db_manager")

        db_entry_deleted = False
        if db_context and image_db_manager:
            async with db_context() as db:
                try:
                    entry = await image_db_manager.read(db, UUID(image_name))
                except ValueError:
                    entry = await image_db_manager.read_by_image_name(db, image_name)
                if entry:
                    image_name = entry.name
                    await image_db_manager.delete(db, entry.uid)
                    db_entry_deleted = True

        async with Docker() as docker:
            try:
                await docker.images.delete(image_name)
            except DockerError as e:
                if e.status != 404 or not db_entry_deleted:
                    raise web.HTTPError(e.status, e.message)

        self.set_status(200)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"status": "ok"}))

    @web.authenticated
    @require_admin_role
    async def post(self):
        data = self.get_json_body()
        repo = data["repo"]
        ref = data["ref"]
        name = data["name"].lower()
        memory = data["memory"]
        cpu = data["cpu"]
        node_selector = data.get("node_selector", {})
        buildargs = data.get("buildargs", None)
        git_username = data.get("username", None)
        git_password = data.get("password", None)
        owner = self.get_current_user().get("name", "unknow")

        if not repo:
            raise web.HTTPError(400, "Repository is empty")

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

        if name and not re.match(IMAGE_NAME_RE, name):
            raise web.HTTPError(
                400,
                f"The name of the environment is restricted to the following characters: {IMAGE_NAME_RE}",
            )

        extra_buildargs = []
        if buildargs:
            for barg in buildargs.split("\n"):
                if "=" not in barg:
                    raise web.HTTPError(400, "Invalid build argument format")
                extra_buildargs.append(barg)

        image_name, ref_norm, name_norm = compute_image_name(repo, ref, name)

        creation_date = datetime.now().strftime("%d/%m/%Y")

        db_context = self.settings.get("db_context")
        image_db_manager = self.settings.get("image_db_manager")

        uid = None
        if db_context and image_db_manager:
            uid = uuid4()
            image_in = DockerImageCreateSchema(
                uid=uid,
                name=image_name,
                status=BuildStatusType.BUILDING,
                log="",
                image_meta=ImageMetadataType(
                    display_name=name_norm,
                    repo=repo,
                    ref=ref_norm,
                    cpu_limit=cpu or "",
                    mem_limit=memory or "",
                    creation_date=creation_date,
                    owner=owner,
                    node_selector=node_selector,
                ),
            )
            async with db_context() as db:
                await image_db_manager.create(db, image_in)

        self.set_status(200)
        self.set_header("content-type", "application/json")
        response = {"status": "ok"}
        if uid is not None:
            response["uid"] = str(uid)
        self.finish(json.dumps(response))

        try:
            await build_image(
                repo,
                ref,
                node_selector,
                name,
                owner,
                memory,
                cpu,
                git_username,
                git_password,
                extra_buildargs,
                uid=uid,
                db_context=db_context,
                image_db_manager=image_db_manager,
            )
        except Exception as e:
            self.log.error("Build failed with exception: %s", e, exc_info=True)
            if db_context and image_db_manager:
                async with db_context() as db:
                    await image_db_manager.update(
                        db,
                        DockerImageUpdateSchema(
                            uid=uid,
                            status=BuildStatusType.FAILED,
                            log=str(e),
                        ),
                    )
