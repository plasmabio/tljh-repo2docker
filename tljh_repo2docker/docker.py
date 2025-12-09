import json
from urllib.parse import urlparse

from aiodocker import Docker
from tornado import web


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
            "mem_limit": image["Labels"].get("tljh_repo2docker.mem_limit", ""),
            "cpu_limit": image["Labels"].get("tljh_repo2docker.cpu_limit", ""),
            "node_selector": image["Labels"].get("tljh_repo2docker.node_selector", ""),
        }


async def build_image(
    repo,
    ref,
    node_selector={},
    name="",
    memory=None,
    cpu=None,
    username=None,
    password=None,
    extra_buildargs=None,
):
    """
    Build an image given a repo, ref and limits
    """
    ref = ref or "HEAD"
    if len(ref) >= 40:
        ref = ref[:7]

    # default to the repo name if no name specified
    # and sanitize the name of the docker image
    name = name or urlparse(repo).path.strip("/")
    name = name.lower().replace("/", "-")
    image_name = f"{name}:{ref}"

    # memory is specified in GB
    memory = f"{memory}G" if memory else ""
    cpu = cpu or ""

    # add extra labels to set additional image properties
    labels = [
        f"tljh_repo2docker.display_name={name}",
        f"tljh_repo2docker.image_name={image_name}",
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
        "Image": "quay.io/jupyterhub/repo2docker:main",
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

    if username and password:
        config.update(
            {
                "Env": [f"GIT_CREDENTIAL_ENV=username={username}\npassword={password}"],
            }
        )

    async with Docker() as docker:
        await docker.containers.run(config=config)
