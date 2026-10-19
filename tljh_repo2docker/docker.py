import collections
import json
from datetime import datetime
from urllib.parse import quote, unquote, urlparse

from aiodocker import Docker, DockerError
from tornado import web
from tornado.log import app_log

from .database.schemas import BuildStatusType, DockerImageUpdateSchema

LOG_HEAD_LINES = 10
LOG_TAIL_LINES = 300
MAX_LINE_CHARS = 4096
REDACTED = "[redacted]"


def _redact(line, secrets):
    """Replace each non-empty secret occurrence in ``line`` with [redacted]."""
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    for secret in secrets:
        if secret:
            line = line.replace(secret, REDACTED)
    if len(line) > MAX_LINE_CHARS:
        line = line[:MAX_LINE_CHARS] + "...[line truncated]\n"
    return line


def split_url_credentials(url: str) -> tuple[str, str, str]:
    """Strip and return any user:password embedded in an http(s) URL.

    Returns ``(cleaned_url, username, password)``. ``username`` / ``password``
    are URL-decoded. For non-http(s) URLs or URLs without an embedded
    userinfo block, returns ``(url, "", "")`` unchanged.

    Used to avoid persisting credentials pasted into the repo URL field
    (DB, Docker labels, build logs).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return url, "", ""
    if not (parsed.username or parsed.password):
        return url, "", ""
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    cleaned = parsed._replace(netloc=host).geturl()
    return (
        cleaned,
        unquote(parsed.username or ""),
        unquote(parsed.password or ""),
    )


def _embed_credentials(repo: str, username: str, password: str) -> str:
    """Return ``repo`` with HTTP basic-auth credentials embedded.

    Used because the upstream ``repo2docker`` image no longer honours the
    ``GIT_CREDENTIAL_ENV`` variable, so the only reliable way to clone a
    private HTTPS repo from inside the build container is to pass the
    token directly in the URL. Returns the URL unchanged for schemes
    other than http(s).
    """
    parsed = urlparse(repo)
    if parsed.scheme not in ("http", "https"):
        return repo
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    netloc = f"{quote(username, safe='')}:{quote(password, safe='')}@{host}"
    return parsed._replace(netloc=netloc).geturl()


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
    # Docker image names must start and end with an alphanumeric character. A
    # trailing slash in the repo URL becomes a trailing "-" here, which
    # repo2docker rejects ("is not a valid docker image name"), so strip any
    # leading/trailing separators.
    name = name.strip("-_.")
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
            "creation_date": image["Labels"].get(
                "tljh_repo2docker.creation_date", "unknow"
            ),
            "owner": image["Labels"].get("tljh_repo2docker.owner", "unknow"),
            "mem_limit": image["Labels"]["tljh_repo2docker.mem_limit"],
            "cpu_limit": image["Labels"]["tljh_repo2docker.cpu_limit"],
            "node_selector": image["Labels"].get("tljh_repo2docker.node_selector", ""),
            "status": "built",
        }
        for image in r2d_images
        if "tljh_repo2docker.image_name" in image["Labels"]
        # skip the temporary build tag, which carries the same labels
        and image["Labels"]["tljh_repo2docker.image_name"]
        in (image.get("RepoTags") or [])
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


def build_tag(image_name):
    """Temporary name of an image while it is being built"""
    return f"{image_name}-build"


async def _delete_image(docker, name):
    try:
        await docker.images.delete(name, force=True)
    except DockerError as e:
        if e.status != 404:
            raise


async def _publish_image(docker, build_name, image_name, exit_code):
    """Move image_name to the image built as build_name, on success only:
    a failed rebuild keeps the previous image. Return whether it was moved."""
    try:
        if exit_code != 0:
            await _delete_image(docker, build_name)
            return False
        try:
            previous = (await docker.images.inspect(image_name))["Id"]
        except DockerError as e:
            if e.status != 404:
                raise
            previous = None
        repository, tag = image_name.rsplit(":", 1)
        await docker.images.tag(build_name, repository, tag=tag)
    except DockerError:
        app_log.exception("Failed to publish the image built for %s", image_name)
        return False

    # from here on the new image is published: errors are only logged
    try:
        # only untags: the image is now also tagged image_name
        await docker.images.delete(build_name)
        if previous is not None:
            previous_image = await docker.images.inspect(previous)
            # free the space of the replaced image, unless something else tags it
            if not previous_image.get("RepoTags"):
                await docker.images.delete(previous)
    except DockerError as e:
        # 409: the replaced image is still used by a running server, and is
        # left dangling for docker image prune
        if e.status != 409:
            app_log.exception("Failed to clean up after publishing %s", image_name)
    return True


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
    # repo2docker skips the build when the image already exists, so a rebuild
    # would keep the old image: build under a temporary tag, moved on success.
    build_name = build_tag(image_name)

    # memory is specified in GB
    memory = f"{memory}G" if memory else ""
    cpu = cpu or ""

    # creation_date
    creation_date = datetime.now().strftime("%d/%m/%Y")

    # repo2docker renders image labels as `LABEL key="value"`, so the value
    # cannot hold a double quote: a repr of strings, not JSON.
    repr_node_selector = {str(k): str(v) for k, v in (node_selector or {}).items()}

    # add extra labels to set additional image properties
    labels = [
        f"tljh_repo2docker.display_name={name}",
        f"tljh_repo2docker.image_name={image_name}",
        f"tljh_repo2docker.creation_date={creation_date}",
        f"tljh_repo2docker.owner={owner}",
        f"tljh_repo2docker.mem_limit={memory}",
        f"tljh_repo2docker.cpu_limit={cpu}",
        f"tljh_repo2docker.node_selector={repr_node_selector}",
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
        build_name,
    ]

    for label in labels:
        cmd += ["--label", label]

    for barg in extra_buildargs or []:
        cmd += ["--build-arg", barg]

    authed_repo = repo
    if git_username and git_password:
        authed_repo = _embed_credentials(repo, git_username, git_password)

    cmd.append(authed_repo)

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
        # SECURITY: repo2docker needs access to the host Docker daemon to
        # build and load images, so /var/run/docker.sock is mounted in. This
        # is a documented trust assumption: only admins can trigger builds,
        # and the repo2docker image itself must be trusted. A malicious repo
        # could still pivot via the socket. Hardening below (no-new-privileges)
        # is defense in depth, not a full mitigation. The proper fix is to
        # switch to a rootless / BuildKit-based builder.
        "Volumes": {
            "/var/run/docker.sock": {
                "bind": "/var/run/docker.sock",
                "mode": "rw",
            }
        },
        "HostConfig": {
            "Binds": ["/var/run/docker.sock:/var/run/docker.sock"],
            "SecurityOpt": ["no-new-privileges:true"],
        },
        "Tty": False,
        "AttachStdout": False,
        "AttachStderr": False,
        "OpenStdin": False,
    }

    # NOTE: previous versions exported GIT_CREDENTIAL_ENV here for repo2docker
    # to consume, but upstream removed that integration. Credentials are now
    # embedded in the URL above; nothing else to inject in the container env.
    secrets = [s for s in (git_password, git_username) if s]
    if authed_repo != repo:
        secrets.append(authed_repo)
    # URL-encoding may transform creds (e.g. when they contain special
    # characters such as '@' or ':'); redact the encoded forms too so a
    # partial leak cannot slip through.
    for s in (git_password, git_username):
        if s and quote(s, safe="") != s:
            secrets.append(quote(s, safe=""))

    async with Docker() as docker:
        # left over by an interrupted build, it would be reused as is
        await _delete_image(docker, build_name)
        container = await docker.containers.run(config=config)

        try:
            if uid and db_context and image_db_manager:
                head_parts = []
                tail_parts = collections.deque(maxlen=LOG_TAIL_LINES)
                line_count = 0
                pending = 0
                async for line in container.log(stdout=True, stderr=True, follow=True):
                    line = _redact(line, secrets)
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
                published = await _publish_image(
                    docker, build_name, image_name, exit_code
                )
                update = DockerImageUpdateSchema(
                    uid=uid,
                    status=(
                        BuildStatusType.BUILT if published else BuildStatusType.FAILED
                    ),
                )
                if exit_code == 0 and not published:
                    # keep the build log, it is not what failed
                    tail_parts.append(
                        f"\nThe image was built but could not be tagged {image_name}."
                        " See service logs for details.\n"
                    )
                    truncated = line_count > LOG_HEAD_LINES + LOG_TAIL_LINES
                    update.log = _build_log(head_parts, tail_parts, truncated)
                async with db_context() as db:
                    await image_db_manager.update(db, update)
            else:
                # No DB context: drain logs to allow the container to finish
                async for _ in container.log(stdout=True, stderr=True, follow=True):
                    pass
                result = await container.wait()
                exit_code = result.get("StatusCode", -1)
                await _publish_image(docker, build_name, image_name, exit_code)
        finally:
            try:
                await container.delete()
            except DockerError:
                # Container may already be gone if the user deleted the
                # environment mid-build (BuildHandler.delete force-removes
                # the in-flight container). Best-effort cleanup.
                pass
