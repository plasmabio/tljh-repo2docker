import asyncio
import json
import re
import subprocess
import sys

from concurrent.futures import ThreadPoolExecutor
from http.client import responses
from threading import Event
from urllib.parse import urlparse

import docker

from jupyterhub.services.auth import HubAuthenticated
from tornado import web, escape
from tornado.concurrent import run_on_executor
from tornado.log import app_log

client = docker.from_env()

DISPLAY_NAME_RE = r'^[a-zA-Z0-9-_]+$'


def build_image(repo, ref, display_name="", memory=None, cpu=None):
    """
    Build an image given a repo, ref and limits
    """
    ref = ref or "master"
    if len(ref) >= 40:
        ref = ref[:7]
    name = urlparse(repo).path.strip("/")
    image_name = f"{name}:{ref}"
    display_name = display_name or f"{name}-{ref}"

    # memory is specified in GB
    memory = f"{memory}G" if memory else ""
    cpu = cpu or ""

    # add extra labels to set additional image properties
    labels = [
        f"LABEL tljh_repo2docker.display_name={display_name}",
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
            "tljh_repo2docker.display_name": display_name,
            "tljh_repo2docker.mem_limit": memory,
            "tljh_repo2docker.cpu_limit": cpu,
        },
        volumes={
            "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}
        },
        detach=True,
        remove=True,
    )


def remove_image(name):
    """
    Remove an image by name
    """
    client.images.remove(name)


class BuildHandler(HubAuthenticated, web.RequestHandler):

    executor = ThreadPoolExecutor(max_workers=5)

    def initialize(self):
        self.log = app_log

    def write_error(self, status_code, **kwargs):
        exc_info = kwargs.get("exc_info")
        message = ""
        exception = None
        status_message = responses.get(status_code, "Unknown Error")
        if exc_info:
            exception = exc_info[1]
            try:
                message = exception.log_message % exception.args
            except Exception:
                pass

            reason = getattr(exception, "reason", "")
            if reason:
                status_message = reason

        self.set_header("Content-Type", "application/json")
        self.write(
            json.dumps({"status": status_code, "message": message or status_message})
        )

    @web.authenticated
    @run_on_executor
    def delete(self):
        data = escape.json_decode(self.request.body)
        name = data["name"]
        try:
            remove_image(name)
        except docker.errors.ImageNotFound:
            raise web.HTTPError(400, f"Image {name} does not exist")
        except docker.errors.APIError as e:
            raise web.HTTPError(500, str(e))

        self.set_status(200)

    @web.authenticated
    @run_on_executor
    def post(self):
        data = escape.json_decode(self.request.body)
        repo = data["repo"]
        ref = data["ref"]
        display_name = data["displayName"]
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

        if display_name and not re.match(DISPLAY_NAME_RE, display_name):
            raise web.HTTPError(400, f"Display Name is restricted to the following characters: {DISPLAY_NAME_RE}")

        build_image(repo, ref, display_name, memory, cpu)
        self.set_status(200)
