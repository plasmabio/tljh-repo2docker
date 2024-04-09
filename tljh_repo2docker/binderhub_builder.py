import json

import requests
from tornado import web
from .base import BaseHandler, require_admin_role
from urllib.parse import quote
from jupyterhub.utils import url_path_join


class BinderHubBuildHandler(BaseHandler):
    """
    Handle requests to build user environments using BinderHub service
    """

    @web.authenticated
    @require_admin_role
    async def post(self):
        data = self.get_json_body()
        repo = data["repo"]
        ref = data["ref"]
        name = data["name"].lower()
        memory = data["memory"]
        cpu = data["cpu"]
        provider = data["provider"]
        print(f"Building binder for {provider}@{repo}@{ref}")
        binder_url = self.settings.get("binderhub_url")
        quoted_repo = quote(repo, safe="")
        url = url_path_join(binder_url, "build", provider, quoted_repo, ref)

        params = {"build_only": "true"}
        
        async with self.client.stream("GET", url, params=params, timeout=None) as r:
            async for line in r.aiter_lines():
                print("proviDDDDDDDDDDDDDDDDder", line)
                # if line.startswith("data:"):
                    # print(line.split(":", 1)[1])

        self.set_status(200)
        self.set_header("content-type", "application/json")
        self.finish(json.dumps({"status": "ok"}))
