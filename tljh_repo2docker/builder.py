import json
import re

from aiodocker import Docker, DockerError
from tornado import web

from .base import BaseHandler, require_admin_role
from .docker import build_image

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"


class BuildHandler(BaseHandler):
    """
    Handle requests to build user environments as Docker images
    """

    @web.authenticated
    @require_admin_role
    async def delete(self):
        data = self.get_json_body()
        name = data["name"]
        async with Docker() as docker:
            try:
                await docker.images.delete(name)
            except DockerError as e:
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
        username = data.get("username", None)
        password = data.get("password", None)

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
        await build_image(
            repo,
            ref,
            node_selector,
            name,
            memory,
            cpu,
            username,
            password,
            extra_buildargs,
        )

        self.set_status(200)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"status": "ok"}))
