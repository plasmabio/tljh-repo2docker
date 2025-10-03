import functools
import json
import os
import sys
from contextlib import _AsyncGeneratorContextManager
from http.client import responses
from typing import Any, Callable, Dict, List, Optional, Tuple

from httpx import AsyncClient
from jinja2 import Template
from jupyterhub.services.auth import HubOAuthenticated
from jupyterhub.utils import url_path_join
from sqlalchemy.ext.asyncio import AsyncSession
from tornado import web
from tornado.log import app_log

from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE
from tljh_repo2docker.database.manager import ImagesDatabaseManager

from .model import UserModel

if sys.version_info >= (3, 9):
    AsyncSessionContextFactory = Callable[
        [], _AsyncGeneratorContextManager[AsyncSession]
    ]
else:
    AsyncSessionContextFactory = Any


def require_admin_role(func):
    """decorator to require admin role to perform an action"""

    @functools.wraps(func)
    async def wrapped_func(self, *args, **kwargs):
        user = await self.fetch_user()
        if not user.admin:
            raise web.HTTPError(status_code=404, reason="Unauthorized.")
        else:
            return await func(self, *args, **kwargs)

    return wrapped_func


class BaseHandler(HubOAuthenticated, web.RequestHandler):
    """
    Base handler for tljh_repo2docker service
    """

    _client = None

    @property
    def log(self):
        return self.settings.get("log", app_log)

    @property
    def client(self):
        """
        Get the asynchronous HTTP client with valid authorization token.
        """
        if not BaseHandler._client:
            api_url = os.environ.get("JUPYTERHUB_API_URL", "")
            api_token = os.environ.get("JUPYTERHUB_API_TOKEN", None)
            BaseHandler._client = AsyncClient(
                base_url=api_url,
                headers={"Authorization": f"Bearer {api_token}"},
            )
        return BaseHandler._client

    async def fetch_user(self) -> UserModel:
        user = self.current_user
        url = url_path_join("users", user["name"])
        response = await self.client.get(url + "?include_stopped_servers")
        user_model: dict = response.json()
        user_model.setdefault("name", user["name"])
        user_model.setdefault("servers", {})
        user_model.setdefault("roles", [])
        user_model.setdefault("admin", False)

        if not user_model["admin"]:
            if "admin" in user_model["roles"] or TLJH_R2D_ADMIN_SCOPE in user["scopes"]:
                user_model["admin"] = True

        return UserModel.from_dict(user_model)

    def get_template(self, name: str) -> Template:
        """Return the jinja template object for a given name
        Args:
            name: Template name
        Returns:
            jinja2.Template object
        """
        return self.settings["jinja2_env"].get_template(name)

    async def render_template(self, name: str, **kwargs) -> str:
        """Render the given template with the provided arguments
        Args:
            name: Template name
            **kwargs: Template arguments
        Returns:
            The generated template
        """
        user = await self.fetch_user()
        base_url = self.settings.get("base_url", "/")
        template_ns = dict(
            service_prefix=self.settings.get("service_prefix", "/"),
            hub_prefix=self.settings.get("hub_prefix", "/"),
            base_url=base_url,
            logo_url=self.settings.get("logo_url", "/"),
            logout_url=self.settings.get(
                "logout_url", url_path_join(base_url, "logout")
            ),
            static_url=self.static_url,
            xsrf_token=self.xsrf_token.decode("ascii"),
            user=user,
            admin_access=user.admin,
        )
        template_ns.update(kwargs)
        template = self.get_template(name)
        return template.render(**template_ns)

    def get_json_body(self):
        """Return the body of the request as JSON data."""
        if not self.request.body:
            return None
        body = self.request.body.strip().decode("utf-8")
        try:
            model = json.loads(body)
        except Exception:
            self.log.debug("Bad JSON: %r", body)
            self.log.error("Couldn't parse JSON", exc_info=True)
            raise web.HTTPError(400, "Invalid JSON in body of request")
        return model

    def check_xsrf_cookie(self):
        """
        Copy from https://github.com/jupyterhub/jupyterhub/blob/main/jupyterhub/apihandlers/base.py#L89
        """
        if not hasattr(self, "_jupyterhub_user"):
            return
        if self._jupyterhub_user is None and "Origin" not in self.request.headers:
            return
        if getattr(self, "_token_authenticated", False):
            # if token-authenticated, ignore XSRF
            return
        return super().check_xsrf_cookie()

    def write_error(self, status_code, **kwargs):
        """Write JSON errors instead of HTML"""
        exc_info = kwargs.get("exc_info")
        message = ""
        exception = None
        status_message = responses.get(status_code, "Unknown Error")
        if exc_info:
            exception = exc_info[1]
            # get the custom message, if defined
            try:
                message = exception.log_message % exception.args
            except Exception:
                pass

            # construct the custom reason, if defined
            reason = getattr(exception, "reason", "")
            if reason:
                status_message = reason

        self.set_header("Content-Type", "application/json")
        if isinstance(exception, web.HTTPError):
            # allow setting headers from exceptions
            # since exception handler clears headers
            headers = getattr(exception, "headers", None)
            if headers:
                for key, value in headers.items():
                    self.set_header(key, value)
            # Content-Length must be recalculated.
            self.clear_header("Content-Length")

        self.write(
            json.dumps({"status": status_code, "message": message or status_message})
        )

    @property
    def use_binderhub(self) -> bool:
        """
        Check if BinderHub is being used by checking for the binderhub url
        in the setting.

        Returns:
            bool: True if BinderHub is being used, False otherwise.
        """
        return self.settings.get("binderhub_url", None) is not None

    def get_db_handlers(
        self,
    ) -> Tuple[
        Optional[AsyncSessionContextFactory],
        Optional[ImagesDatabaseManager],
    ]:
        """
        Get database handlers.

        Returns the database context and image database manager based on the
        configuration and settings. If `use_binderhub` flag is set to True,
        returns the configured database context and image database manager;
        otherwise, returns None for both.

        Returns:
            Tuple[Optional[Callable[[], _AsyncGeneratorContextManager[AsyncSession]]],
                Optional[ImagesDatabaseManager]]: A tuple containing:
                - The database context, which is a callable returning an
                    async generator context manager for session management.
                - The image database manager, which handles image database
                    operations.

        """
        if self.use_binderhub:
            db_context = self.settings.get("db_context")
            image_db_manager = self.settings.get("image_db_manager")
            return db_context, image_db_manager
        else:
            return None, None

    async def get_images_from_db(self) -> List[Dict]:
        """
        Retrieve images from the database.

        This method fetches image information from the database, formats it,
        and returns a list of dictionaries representing each image.

        Returns:
            List[Dict]: A list of dictionaries, each containing information
            about an image. Each dictionary has the following keys:
                - image_name (str): The name of the docker image.
                - uid (str): The unique identifier of the image.
                - status (str): The build status of the image.
                - display_name (str): The user defined name of the image.
                - repo (str): Source repo used to build the image.
                - ref (str): Commit reference.
                - cpu_limit (str): CPU limit.
                - mem_limit (str): Memory limit.

        Note:
            If `use_binderhub` flag is set to True and valid database context
            and image database manager are available, it retrieves image
            information; otherwise, an empty list is returned.
        """
        db_context, image_db_manager = self.get_db_handlers()
        all_images = []
        if self.use_binderhub and db_context and image_db_manager:
            async with db_context() as db:
                docker_images = await image_db_manager.read_all(db)
                all_images = [
                    dict(
                        image_name=image.name,
                        uid=str(image.uid),
                        status=image.status,
                        **image.image_meta.model_dump(),
                    )
                    for image in docker_images
                ]

        return all_images
