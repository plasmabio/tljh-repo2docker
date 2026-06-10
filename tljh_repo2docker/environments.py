from inspect import isawaitable

from tornado import web

from .base import BaseHandler, require_admin_role
from .database.schemas import BuildStatusType
from .docker import list_containers, list_images


async def build_image_list(handler):
    """
    Build the list of environments shown in the admin page. Used both by
    EnvironmentsHandler.get (HTML render) and by the JSON GET on
    api/environments consumed by the auto-refresh polling.
    """
    if handler.use_binderhub:
        return await handler.get_images_from_db()

    images = await list_images()
    containers = await list_containers()
    all_images = images + containers

    db_context = handler.settings.get("db_context")
    image_db_manager = handler.settings.get("image_db_manager")
    if db_context and image_db_manager:
        all_images = await _enrich_with_db(all_images, db_context, image_db_manager)

    return all_images


async def _enrich_with_db(images, db_context, image_db_manager):
    """
    Enrich Docker images with their DB uid, and append FAILED or BUILDING
    images that are only in the DB (no Docker image/container yet).
    """
    async with db_context() as db:
        all_db_entries = await image_db_manager.read_all(db)

    db_by_name = {entry.name: entry for entry in all_db_entries}
    docker_names = {img["image_name"] for img in images}

    # Add uid + buildargs to images that have a matching DB entry. The
    # buildargs are only persisted in the DB (no Docker label), so they
    # need to be backfilled here for the rebuild dialog to pre-fill them.
    for image in images:
        entry = db_by_name.get(image["image_name"])
        if entry:
            image["uid"] = str(entry.uid)
            if entry.image_meta.buildargs:
                image["buildargs"] = entry.image_meta.buildargs

    extra = [
        dict(
            image_name=entry.name,
            uid=str(entry.uid),
            status=entry.status,
            **entry.image_meta.model_dump(),
        )
        for entry in all_db_entries
        if entry.status in (BuildStatusType.FAILED, BuildStatusType.BUILDING)
        and entry.name not in docker_names
    ]

    return images + extra


class EnvironmentsHandler(BaseHandler):
    """
    Handler to show the list of environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def get(self):
        all_images = await build_image_list(self)

        result = self.render_template(
            "images.html",
            images=all_images,
            default_mem_limit=self.settings.get("default_mem_limit"),
            default_cpu_limit=self.settings.get("default_cpu_limit"),
            machine_profiles=self.settings.get("machine_profiles", []),
            node_selector=self.settings.get("node_selector", {}),
            repo_providers=self.settings.get("repo_providers", None),
            use_binderhub=self.use_binderhub,
        )
        if isawaitable(result):
            self.write(await result)
        else:
            self.write(result)
