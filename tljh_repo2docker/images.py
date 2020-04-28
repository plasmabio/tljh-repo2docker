import json
import os

import docker

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    PrefixLoader,
)
from jupyterhub._data import DATA_FILES_PATH
from jupyterhub.services.auth import HubAuthenticated
from jupyterhub.utils import auth_decorator, url_path_join
from tornado import ioloop, web
from tornado.options import define, options, parse_command_line

from .builder import BuildHandler

loader = ChoiceLoader(
    [
        PackageLoader("tljh_repo2docker", "templates"),
        PrefixLoader(
            {
                "templates": FileSystemLoader(
                    [os.path.join(DATA_FILES_PATH, "templates")]
                )
            },
            "/",
        ),
        FileSystemLoader(os.path.join(DATA_FILES_PATH, "templates")),
    ]
)
templates = Environment(loader=loader)
client = docker.from_env()


def list_images():
    """
    Retrieve local images built by repo2docker
    """
    r2d_images = [
        image
        for image in client.images.list(
            filters={"dangling": False, "label": ["repo2docker.ref"]}
        )
    ]
    images = [
        {
            "repo": image.labels["repo2docker.repo"],
            "ref": image.labels["repo2docker.ref"],
            "image_name": image.labels["tljh_repo2docker.image_name"],
            "display_name": image.labels["tljh_repo2docker.display_name"],
            "mem_limit": image.labels["tljh_repo2docker.mem_limit"],
            "cpu_limit": image.labels["tljh_repo2docker.cpu_limit"],
            "status": "built",
        }
        for image in r2d_images
        if "tljh_repo2docker.display_name" in image.labels
    ]
    return images


def list_containers():
    """
    Retrieve data for the local images being built by repo2docker.
    Images are built in a Docker container.
    """
    r2d_containers = [
        container
        for container in client.containers.list(filters={"label": ["repo2docker.ref"]})
    ]
    containers = [
        {
            "repo": container.labels["repo2docker.repo"],
            "ref": container.labels["repo2docker.ref"],
            "image_name": container.labels["repo2docker.build"],
            "mem_limit": container.labels["tljh_repo2docker.mem_limit"],
            "cpu_limit": container.labels["tljh_repo2docker.cpu_limit"],
            "status": "building",
        }
        for container in r2d_containers
        if "repo2docker.build" in container.labels
    ]
    return containers


@auth_decorator
def admin_only(self):
    """Decorator for restricting access to admin users"""
    user = self.get_current_user()
    if user is None or not user["admin"]:
        raise web.HTTPError(403)


class ImagesHandler(HubAuthenticated, web.RequestHandler):
    def static_url(self, path, **kwargs):
        return url_path_join(self.settings.get("static_url"), path)

    @admin_only
    def get(self):
        template = templates.get_template("images.html")
        user = self.get_current_user()
        prefix = self.hub_auth.hub_prefix
        logout_url = url_path_join(prefix, "logout")
        images = list_images() + list_containers()
        self.write(
            template.render(
                user=user,
                images=images,
                default_mem_limit=self.settings.get("default_mem_limit"),
                default_cpu_limit=self.settings.get("default_cpu_limit"),
                static_url=self.static_url,
                login_url=self.hub_auth.login_url,
                logout_url=logout_url,
                base_url=prefix,
                no_spawner_check=True,
            )
        )


class MultiStaticFileHandler(web.StaticFileHandler):
    """
    A static file handler that 'merges' a list of directories

    If initialized like this::
        application = web.Application([
            (r"/content/(.*)", web.MultiStaticFileHandler, {"paths": ["/var/1", "/var/2"]}),
        ])
    A file will be looked up in /var/1 first, then in /var/2.

    From: https://github.com/voila-dashboards/voila/blob/112163d88a2d1a5c7706327e68825ddc02819d3a/voila/static_file_handler.py#L16
    """

    def initialize(self, paths, default_filename=None):
        # find the first absolute path that exists
        self.roots = paths
        super(MultiStaticFileHandler, self).initialize(
            path=paths[0], default_filename=default_filename
        )

    def get_absolute_path(self, root, path):
        self.root = self.roots[0]
        for root in self.roots:
            abspath = os.path.abspath(os.path.join(root, path))
            if os.path.exists(abspath):
                self.root = root  # make sure all the other methods in the base class know how to find the file
                break
        return abspath


def make_app(default_mem_limit=None, default_cpu_limit=None):
    service_prefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"]
    static_paths = [
        # JupyterHub static files
        os.path.join(DATA_FILES_PATH, "static"),
        # The PlasmaBio static files
        os.path.join(os.path.dirname(__file__), "static"),
    ]
    app_settings = {
        "static_url": url_path_join(service_prefix, "static/"),
        "default_mem_limit": default_mem_limit,
        "default_cpu_limit": default_cpu_limit,
    }
    return web.Application(
        [
            (rf"{service_prefix}?", ImagesHandler),
            (rf"{service_prefix}api/build", BuildHandler),
            (
                rf"{service_prefix}static/(.*)",
                MultiStaticFileHandler,
                {"paths": static_paths},
            ),
        ],
        **app_settings,
    )


if __name__ == "__main__":
    define(
        "default_mem_limit", default=None, help="The default memory limit",
    )
    define(
        "default_cpu_limit", default=None, help="The default cpu limit",
    )
    parse_command_line()

    app = make_app(
        default_mem_limit=options.default_mem_limit,
        default_cpu_limit=options.default_cpu_limit,
    )
    app.listen(9988)
    ioloop.IOLoop.current().start()
