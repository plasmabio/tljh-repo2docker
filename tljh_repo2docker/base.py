import functools
import json
import os
from http.client import responses

from httpx import AsyncClient
from jinja2 import Template
from jupyterhub.services.auth import HubOAuthenticated
from jupyterhub.utils import url_path_join
from tornado import web

from tljh_repo2docker import TLJH_R2D_ADMIN_SCOPE

from .model import UserModel


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
    def client(self):
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
