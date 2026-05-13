import json
import re

import pytest
from jupyterhub.tests.utils import get_page

from ..utils import add_environment, get_service_page, wait_for_image

PAGE_DATA_RE = re.compile(
    r'<script id="tljh-page-data" type="application/json">\s*(.*?)\s*</script>',
    re.DOTALL,
)


def _extract_page_data(html):
    match = PAGE_DATA_RE.search(html)
    assert match, "tljh-page-data block not found in response"
    return json.loads(match.group(1))


@pytest.mark.asyncio
async def test_images_list_admin(app, image_name):
    cookies = await app.login_user("admin")
    r = await get_service_page(
        "environments",
        app,
        cookies=cookies,
        allow_redirects=True,
    )
    r.raise_for_status()

    page_data = _extract_page_data(r.text)
    assert page_data["repo_providers"] == [{"label": "Git", "value": "git"}]
    assert page_data["use_binderhub"] is False
    assert page_data["default_mem_limit"] == "None"
    assert page_data["default_cpu_limit"] == "None"
    assert page_data["machine_profiles"] == []
    assert page_data["node_selector"] == {}
    # The test image must not be built yet. Other Docker images on the host
    # (left over from manual dev runs) are tolerated so the test stays
    # hermetic to the developer's local environment.
    assert all(img["image_name"] != image_name for img in page_data["images"])


@pytest.mark.asyncio
async def test_images_list_not_admin(app):
    cookies = await app.login_user("wash")
    r = await get_service_page(
        "environments", app, cookies=cookies, allow_redirects=True
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_spawn_page(app, minimal_repo, image_name):
    cookies = await app.login_user("admin")

    # go to the spawn page
    r = await get_page("spawn", app, cookies=cookies, allow_redirects=False)
    r.raise_for_status()
    assert minimal_repo not in r.text

    # add a new envionment
    name, ref = image_name.split(":")
    r = await add_environment(app, repo=minimal_repo, name=name, ref=ref)
    assert r.status_code == 200
    await wait_for_image(image_name=image_name)

    # the environment should be on the page
    r = await get_page("spawn", app, cookies=cookies, allow_redirects=False)
    r.raise_for_status()
    assert r.status_code == 200
    assert minimal_repo in r.text
