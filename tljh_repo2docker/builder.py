import json
import re

from urllib.parse import urlparse

from aiodocker import Docker, DockerError
from jupyterhub.apihandlers import APIHandler
from jupyterhub.utils import admin_only
from tornado import web

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"


class BuildHandler(APIHandler):

    def initialize(self):
        self.docker = Docker()

    """
    Handle requests to build user environments as Docker images
    """

    @web.authenticated
    @admin_only
    async def delete(self):
        data = self.get_json_body()
        name = data["name"]
        try:
            await self.docker.images.delete(name)
        except DockerError as e:
            raise web.HTTPError(e.status, e.message)

        self.set_status(200)
        self.finish(json.dumps({"status": "ok"}))

    @web.authenticated
    @admin_only
    async def post(self):
        data = self.get_json_body()
        repo = data["repo"]
        ref = data["ref"]
        name = data["name"].lower()
        memory = data["memory"]
        cpu = data["cpu"]

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

        await self._build_image(repo, ref, name, memory, cpu)

        self.set_status(200)
        self.finish(json.dumps({"status": "ok"}))

    async def _build_image(self, repo, ref, name="", memory=None, cpu=None):
        """
        Build an image given a repo, ref and limits
        """
        ref = ref or "master"
        if len(ref) >= 40:
            ref = ref[:7]

        # default to the repo name if no name specified
        # and sanitize the name of the docker image
        name = name or urlparse(repo).path.strip("/")
        name = name.replace("/", "-")
        image_name = f"{name}:{ref}"

        # memory is specified in GB
        memory = f"{memory}G" if memory else ""
        cpu = cpu or ""

        # add extra labels to set additional image properties
        labels = [
            f"LABEL tljh_repo2docker.display_name={name}",
            f"LABEL tljh_repo2docker.image_name={image_name}",
            f"LABEL tljh_repo2docker.mem_limit={memory}",
            f"LABEL tljh_repo2docker.cpu_limit={cpu}",
        ]
        cmd = [
            "jupyter-repo2docker",
            "--ref",
            ref,
            "--user-name",
            "jovyan",
            "--user-id",
            "1100",
            "--no-run",
            "--image-name",
            image_name,
            "--appendix",
            "\n".join(labels),
            repo,
        ]
        await self.docker.containers.run(
            config={
                "Cmd": cmd,
                "Image": "jupyter/repo2docker:master",
                "Labels": {
                    "repo2docker.repo": repo,
                    "repo2docker.ref": ref,
                    "repo2docker.build": image_name,
                    "tljh_repo2docker.display_name": name,
                    "tljh_repo2docker.mem_limit": memory,
                    "tljh_repo2docker.cpu_limit": cpu,
                },
                "Volumes": {
                    "/var/run/docker.sock": {
                        "bind": "/var/run/docker.sock",
                        "mode": "rw",
                    }
                },
                "HostConfig": {"Binds": ["/var/run/docker.sock:/var/run/docker.sock"],},
                "Tty": False,
                "AttachStdout": False,
                "AttachStderr": False,
                "OpenStdin": False,
            }
        )
