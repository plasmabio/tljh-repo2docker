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
from .docker import build_image, compute_image_name, split_url_credentials
from .environments import build_image_list

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"


class BuildHandler(BaseHandler):
    """
    Handle requests to build user environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def get(self):
        images = await build_image_list(self)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"images": images}))

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
            # Kill any in-progress build container for this image. Without
            # this, deleting an environment mid-build leaves the repo2docker
            # container running: list_containers() keeps showing it as
            # "building" while the DB row (and its log) is gone.
            containers = await docker.containers.list(
                filters=json.dumps(
                    {"label": [f"repo2docker.build={image_name}"]}
                )
            )
            for container in containers:
                try:
                    await container.delete(force=True)
                except DockerError:
                    self.log.exception(
                        "Failed to delete build container for %s", image_name
                    )

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
        rebuild_uid_raw = data.get("uid")
        owner = self.get_current_user().get("name", "unknow")

        if not repo:
            raise web.HTTPError(400, "Repository is empty")

        # Strip credentials embedded in the repo URL so they are never
        # persisted in the DB or Docker labels. Form values take priority;
        # URL-embedded creds are only used when the form is empty.
        repo, url_user, url_pass = split_url_credentials(repo)
        if not git_username:
            git_username = url_user
        if not git_password:
            git_password = url_pass

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

        db_context = self.settings.get("db_context")
        image_db_manager = self.settings.get("image_db_manager")

        rebuild_uid = None
        existing_entry = None
        if rebuild_uid_raw:
            if not (db_context and image_db_manager):
                raise web.HTTPError(400, "Rebuild requires the database backend")
            try:
                rebuild_uid = UUID(rebuild_uid_raw)
            except (ValueError, AttributeError, TypeError):
                raise web.HTTPError(400, "Invalid uid")
            async with db_context() as db:
                existing_entry = await image_db_manager.read(db, rebuild_uid)
            if existing_entry is None:
                raise web.HTTPError(404, "Environment not found")
            if existing_entry.status == BuildStatusType.BUILDING.value:
                raise web.HTTPError(409, "Environment is already building")
            if existing_entry.image_meta.display_name != name_norm:
                raise web.HTTPError(
                    400, "Environment name does not match the rebuilt entry"
                )

        uid = None
        if db_context and image_db_manager:
            if rebuild_uid is not None:
                assert existing_entry is not None
                uid = rebuild_uid
                # Refresh creation_date so the table shows when the current
                # image was last (re)built, not when it was first created.
                creation_date = datetime.now().strftime("%d/%m/%Y")
                update_in = DockerImageUpdateSchema(
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
                        owner=existing_entry.image_meta.owner,
                        node_selector=node_selector,
                        buildargs=buildargs or None,
                    ),
                )
                async with db_context() as db:
                    await image_db_manager.update(db, update_in)
            else:
                uid = uuid4()
                creation_date = datetime.now().strftime("%d/%m/%Y")
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
                        buildargs=buildargs or None,
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
        except Exception:
            # Log the full exception server-side, but persist a generic
            # message in the DB to avoid leaking credentials or repo URLs
            # via the admin-visible build log.
            self.log.exception("Build failed for image %s", image_name)
            if db_context and image_db_manager:
                async with db_context() as db:
                    await image_db_manager.update(
                        db,
                        DockerImageUpdateSchema(
                            uid=uid,
                            status=BuildStatusType.FAILED,
                            log="Build failed. See service logs for details.",
                        ),
                    )
