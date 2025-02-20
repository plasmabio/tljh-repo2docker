import pytest
from jupyterhub.tests.utils import get_page

from ..utils import add_environment, get_service_page, wait_for_image


@pytest.mark.asyncio
async def test_images_list_admin(app):
    cookies = await app.login_user("admin")
    r = await get_service_page(
        "environments",
        app,
        cookies=cookies,
        allow_redirects=True,
    )
    r.raise_for_status()
    assert (
        '{"repo_providers": [{"label": "Git", "value": "git"}], "use_binderhub": false, "images": [], "default_mem_limit": "None", "default_cpu_limit":"None", "machine_profiles": [], "node_selector": {}}'
        in r.text
    )


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
