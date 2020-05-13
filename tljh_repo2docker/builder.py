import json
import re

from urllib.parse import urlparse

import docker

from jupyterhub.apihandlers import APIHandler
from tornado import web

from .executor import DockerExecutor

client = docker.from_env()

IMAGE_NAME_RE = r"^[a-z0-9-_]+$"


def build_image(repo, ref, name="", memory=None, cpu=None):
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
    client.containers.run(
        "jupyter/repo2docker:master",
        cmd,
        labels={
            "repo2docker.repo": repo,
            "repo2docker.ref": ref,
            "repo2docker.build": image_name,
            "tljh_repo2docker.display_name": name,
            "tljh_repo2docker.mem_limit": memory,
            "tljh_repo2docker.cpu_limit": cpu,
        },
        volumes={
            "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}
        },
        detach=True,
        remove=True,
    )


class BuildHandler(APIHandler, DockerExecutor):

    @web.authenticated
    async def delete(self):
        data = self.get_json_body()
        name = data["name"]
        try:
            await self._run_in_executor(client.images.remove, name)
        except docker.errors.ImageNotFound:
            raise web.HTTPError(400, f"Image {name} does not exist")
        except docker.errors.APIError as e:
            raise web.HTTPError(500, str(e))

        self.set_status(200)
        self.finish(json.dumps({"status": "ok"}))

    @web.authenticated
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
            except:
                raise web.HTTPError(400, "Memory Limit must be a number")

        if cpu:
            try:
                float(cpu)
            except:
                raise web.HTTPError(400, "CPU Limit must be a number")

        if name and not re.match(IMAGE_NAME_RE, name):
            raise web.HTTPError(
                400,
                f"The name of the environment is restricted to the following characters: {IMAGE_NAME_RE}",
            )

        await self._run_in_executor(build_image, repo, ref, name, memory, cpu)
        self.set_status(200)
        self.finish(json.dumps({"status": "ok"}))
