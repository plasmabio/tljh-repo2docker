import logging
import os
import socket
import typing as tp
from pathlib import Path

from jinja2 import Environment, PackageLoader
from jupyterhub.app import DATA_FILES_PATH
from jupyterhub.handlers.static import LogoHandler
from jupyterhub.utils import url_path_join
from tornado import ioloop, web
from traitlets import Dict, Int, List, Unicode, default, validate
from traitlets.config.application import Application

from .builder import BuildHandler
from .environments import EnvironmentsHandler
from .logs import LogsHandler
from .servers import ServersHandler

if os.environ.get("JUPYTERHUB_API_TOKEN"):
    from jupyterhub.services.auth import HubOAuthCallbackHandler
else:

    class HubOAuthCallbackHandler:
        def get(self):
            pass


HERE = Path(__file__).parent


class TljhRepo2Docker(Application):
    name = Unicode("tljh-repo2docker")

    port = Int(6789, help="Port of the service", config=True)

    base_url = Unicode(help="JupyterHub base URL", config=True)

    @default("base_url")
    def _default_base_url(self):
        return os.environ.get("JUPYTERHUB_BASE_URL", "/")

    service_prefix = Unicode(help="JupyterHub service prefix", config=True)

    @default("service_prefix")
    def _default_api_prefix(self):
        return os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")

    ip = Unicode(
        "localhost",
        config=True,
        help="The IP address of the service.",
    )

    @default("ip")
    def _default_ip(self):
        """Return localhost if available, 127.0.0.1 otherwise."""
        s = socket.socket()
        try:
            s.bind(("localhost", 0))
        except socket.error as e:
            self.log.warning(
                "Cannot bind to localhost, using 127.0.0.1 as default ip\n%s", e
            )
            return "127.0.0.1"
        else:
            s.close()
            return "localhost"

    @validate("ip")
    def _validate_ip(self, proposal):
        value = proposal["value"]
        if value == "*":
            value = ""
        return value

    template_paths = List(
        trait=Unicode,
        default_value=None,
        allow_none=True,
        help="Paths to search for jinja templates, before using the default templates.",
        config=True,
    )

    logo_file = Unicode(
        "",
        help="Specify path to a logo image to override the Jupyter logo in the banner.",
        config=True,
    )

    @default("logo_file")
    def _logo_file_default(self):
        return str(HERE / "static/images/jupyterhub-80.png")

    tornado_settings = Dict(
        {},
        config=True,
        help="Extra settings to apply to tornado application, e.g. headers, ssl, etc",
    )

    @default("log_level")
    def _default_log_level(self):
        return logging.INFO

    machine_profiles = List(
        default_value=[], trait=Dict, config=True, help="Pre-defined machine profiles"
    )

    default_cpu_limit = Unicode(
        None, config=True, help="Default CPU limit.", allow_none=True
    )

    default_memory_limit = Unicode(
        None,
        config=True,
        help="Default Memory limit.",
        allow_none=True,
    )

    aliases = {
        "port": "TljhRepo2Docker.port",
        "ip": "TljhRepo2Docker.ip",
        "default_memory_limit": "TljhRepo2Docker.default_memory_limit",
        "default_cpu_limit": "TljhRepo2Docker.default_cpu_limit",
        "machine_profiles": "TljhRepo2Docker.machine_profiles",
    }

    def init_settings(self) -> tp.Dict:
        """Initialize settings for the service application."""
        static_path = DATA_FILES_PATH + "/static/"
        static_url_prefix = self.service_prefix + "static/"
        env_opt = {"autoescape": True}

        env = Environment(
            loader=PackageLoader("tljh_repo2docker"),
            **env_opt,
        )

        settings = dict(
            log=self.log,
            template_path=str(HERE / "templates"),
            static_path=static_path,
            static_url_prefix=static_url_prefix,
            jinja2_env=env,
            cookie_secret=os.urandom(32),
            base_url=self.base_url,
            hub_prefix=url_path_join(self.base_url, "/hub/"),
            service_prefix=self.service_prefix,
            default_mem_limit=self.default_memory_limit,
            default_cpu_limit=self.default_cpu_limit,
            machine_profiles=self.machine_profiles,
        )
        return settings

    def init_handlers(self) -> tp.List:
        """Initialize handlers for service application."""
        handlers = []
        static_path = str(HERE / "static")
        server_url = url_path_join(self.service_prefix, r"servers")
        environments_url = url_path_join(self.service_prefix, r"environments")
        handlers.extend(
            [
                (
                    url_path_join(self.service_prefix, "logo"),
                    LogoHandler,
                    {"path": self.logo_file},
                ),
                (
                    url_path_join(self.service_prefix, r"/service_static/(.*)"),
                    web.StaticFileHandler,
                    {"path": static_path},
                ),
                (
                    url_path_join(self.service_prefix, "oauth_callback"),
                    HubOAuthCallbackHandler,
                ),
                (self.service_prefix, web.RedirectHandler, {"url": server_url}),
                (server_url, ServersHandler),
                (
                    environments_url,
                    EnvironmentsHandler,
                ),
                (url_path_join(self.service_prefix, r"api/environments"), BuildHandler),
                (
                    url_path_join(
                        self.service_prefix, r"api/environments/([^/]+)/logs"
                    ),
                    LogsHandler,
                ),
            ]
        )

        return handlers

    def make_app(self) -> web.Application:
        """Create the tornado web application.
        Returns:
            The tornado web application.
        """

        application = web.Application()
        application.listen(self.port, self.ip)
        return application

    def start(self):
        """Start the server."""
        settings = self.init_settings()

        self.app = web.Application(**settings)
        self.app.settings.update(self.tornado_settings)
        handlers = self.init_handlers()
        self.app.add_handlers(".*$", handlers)

        self.app.listen(self.port, self.ip)
        self.ioloop = ioloop.IOLoop.current()
        try:
            self.log.info(
                f"tljh-repo2docker service listening on {self.ip}:{self.port}"
            )
            self.log.info("Press Ctrl+C to stop")
            self.ioloop.start()
        except KeyboardInterrupt:
            self.log.info("Stopping...")


main = TljhRepo2Docker.launch_instance
