import collections
import json
from datetime import datetime
from urllib.parse import urlparse

from aiodocker import Docker
from tornado import web

from .database.schemas import BuildStatusType, DockerImageUpdateSchema

LOG_HEAD_LINES = 10
LOG_TAIL_LINES = 300


def _build_log(head, tail, truncated):
    if not truncated:
        return "".join(list(head) + list(tail))
    return "".join(head) + "\n[...truncated...]\n" + "".join(tail)


def compute_image_name(repo, ref, name):
    """Return the Docker image name derived from repo/ref/name."""
    ref = ref or "HEAD"
    if len(ref) >= 40:
        ref = ref[:7]
    name = name or urlparse(repo).path.strip("/")
    name = name.lower().replace("/", "-")
    return f"{name}:{ref}", ref, name


async def list_images():
    """
    Retrieve local images built by repo2docker
    """
    async with Docker() as docker:
        r2d_images = await docker.images.list(
            filters=json.dumps({"dangling": ["false"], "label": ["repo2docker.ref"]})
        )
    images = [
        {
            "repo": image["Labels"]["repo2docker.repo"],
            "ref": image["Labels"]["repo2docker.ref"],
            "image_name": image["Labels"]["tljh_repo2docker.image_name"],
            "display_name": image["Labels"]["tljh_repo2docker.display_name"],
            "creation_date": image["Labels"].get("tljh_repo2docker.creation_date", "unknow"),
            "owner": image["Labels"].get("tljh_repo2docker.owner", "unknow"),
            "mem_limit": image["Labels"]["tljh_repo2docker.mem_limit"],
            "cpu_limit": image["Labels"]["tljh_repo2docker.cpu_limit"],
            "node_selector": image["Labels"].get("tljh_repo2docker.node_selector", ""),
            "status": "built",
        }
        for image in r2d_images
        if "tljh_repo2docker.image_name" in image["Labels"]
    ]
    return images


async def list_containers():
    """
    Retrieve the list of local images being built by repo2docker.
    Images are built in a Docker container.
    """
    async with Docker() as docker:
        r2d_containers = await docker.containers.list(
            filters=json.dumps({"label": ["repo2docker.ref"]})
        )
    containers = [
        {
            "repo": container["Labels"]["repo2docker.repo"],
            "ref": container["Labels"]["repo2docker.ref"],
            "image_name": container["Labels"]["repo2docker.build"],
            "display_name": container["Labels"]["tljh_repo2docker.display_name"],
            "mem_limit": container["Labels"]["tljh_repo2docker.mem_limit"],
            "cpu_limit": container["Labels"]["tljh_repo2docker.cpu_limit"],
            "node_selector": container["Labels"].get(
                "tljh_repo2docker.node_selector", ""
            ),
            "status": "building",
        }
        for container in r2d_containers
        if "repo2docker.build" in container["Labels"]
    ]
    return containers


async def get_image_metadata(image_name):
    """
    Retrieve metadata of a specific locally built Docker image.
    """
    async with Docker() as docker:
        images = await docker.images.list(
            filters=json.dumps({"reference": [image_name]})
        )
        if not images:
            raise web.HTTPError(404, "Image not found")

        image = images[0]
        return {
            "repo": image["Labels"].get("repo2docker.repo", ""),
            "ref": image["Labels"].get("repo2docker.ref", ""),
            "display_name": image["Labels"].get("tljh_repo2docker.display_name", ""),
            "creation_date": image["Labels"].get("tljh_repo2docker.creation_date", ""),
            "owner": image["Labels"].get("tljh_repo2docker.owner", ""),
            "mem_limit": image["Labels"].get("tljh_repo2docker.mem_limit", ""),
            "cpu_limit": image["Labels"].get("tljh_repo2docker.cpu_limit", ""),
            "node_selector": image["Labels"].get("tljh_repo2docker.node_selector", ""),
        }


async def build_image(
    repo,
    ref,
    node_selector={},
    name="",
    owner="",
    memory=None,
    cpu=None,
    git_username=None,
    git_password=None,
    extra_buildargs=None,
    uid=None,
    db_context=None,
    image_db_manager=None,
):
    """
    Build an image given a repo, ref and limits.
    When uid/db_context/image_db_manager are provided, logs are streamed to
    the database in real time and the final status (built/failed) is persisted.
    """
    image_name, ref, name = compute_image_name(repo, ref, name)

    # memory is specified in GB
    memory = f"{memory}G" if memory else ""
    cpu = cpu or ""

    # creation_date
    creation_date = datetime.now().strftime("%d/%m/%Y")

    # add extra labels to set additional image properties
    labels = [
        f"tljh_repo2docker.display_name={name}",
        f"tljh_repo2docker.image_name={image_name}",
        f"tljh_repo2docker.creation_date={creation_date}",
        f"tljh_repo2docker.owner={owner}",
        f"tljh_repo2docker.mem_limit={memory}",
        f"tljh_repo2docker.cpu_limit={cpu}",
        f"tljh_repo2docker.node_selector={node_selector}",
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
    ]

    for label in labels:
        cmd += ["--label", label]

    for barg in extra_buildargs or []:
        cmd += ["--build-arg", barg]

    cmd.append(repo)

    config = {
        "Cmd": cmd,
        "Image": "quay.io/jupyterhub/repo2docker:2025.12.0",
        "Labels": {
            "repo2docker.repo": repo,
            "repo2docker.ref": ref,
            "repo2docker.build": image_name,
            "tljh_repo2docker.display_name": name,
            "tljh_repo2docker.mem_limit": memory,
            "tljh_repo2docker.cpu_limit": cpu,
            "tljh_repo2docker.node_selector": json.dumps(node_selector),
        },
        "Volumes": {
            "/var/run/docker.sock": {
                "bind": "/var/run/docker.sock",
                "mode": "rw",
            }
        },
        "HostConfig": {
            "Binds": ["/var/run/docker.sock:/var/run/docker.sock"],
        },
        "Tty": False,
        "AttachStdout": False,
        "AttachStderr": False,
        "OpenStdin": False,
    }

    if git_username and git_password:
        config.update(
            {
                "Env": [f"GIT_CREDENTIAL_ENV=username={git_username}\npassword={git_password}"],
            }
        )

    async with Docker() as docker:
        container = await docker.containers.run(config=config)

        try:
            if uid and db_context and image_db_manager:
                head_parts = []
                tail_parts = collections.deque(maxlen=LOG_TAIL_LINES)
                line_count = 0
                pending = 0
                async for line in container.log(
                    stdout=True, stderr=True, follow=True
                ):
                    if line_count < LOG_HEAD_LINES:
                        head_parts.append(line)
                    else:
                        tail_parts.append(line)
                    line_count += 1
                    pending += 1
                    if pending >= 10:
                        truncated = line_count > LOG_HEAD_LINES + LOG_TAIL_LINES
                        async with db_context() as db:
                            await image_db_manager.update(
                                db,
                                DockerImageUpdateSchema(
                                    uid=uid,
                                    log=_build_log(head_parts, tail_parts, truncated),
                                ),
                            )
                        pending = 0
                # Flush remaining lines
                if pending:
                    truncated = line_count > LOG_HEAD_LINES + LOG_TAIL_LINES
                    async with db_context() as db:
                        await image_db_manager.update(
                            db,
                            DockerImageUpdateSchema(
                                uid=uid,
                                log=_build_log(head_parts, tail_parts, truncated),
                            ),
                        )

                result = await container.wait()
                exit_code = result.get("StatusCode", -1)
                status = (
                    BuildStatusType.BUILT if exit_code == 0 else BuildStatusType.FAILED
                )
                async with db_context() as db:
                    await image_db_manager.update(
                        db, DockerImageUpdateSchema(uid=uid, status=status)
                    )
            else:
                # No DB context: drain logs to allow the container to finish
                async for _ in container.log(stdout=True, stderr=True, follow=True):
                    pass
                await container.wait()
        finally:
            await container.delete()
