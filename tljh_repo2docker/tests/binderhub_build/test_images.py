import asyncio

import pytest

from ..utils import add_environment, get_service_page, wait_for_image


@pytest.mark.asyncio
async def test_images_list_not_admin(app):
    cookies = await app.login_user("wash")
    r = await get_service_page(
        "environments", app, cookies=cookies, allow_redirects=True
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_images_list_admin(app, minimal_repo, image_name, generated_image_name):
    cookies = await app.login_user("admin")
    # add a new envionment
    name, ref = image_name.split(":")
    r = await add_environment(
        app, repo=minimal_repo, name=name, ref=ref, provider="git"
    )
    assert r.status_code == 200
    await wait_for_image(image_name=generated_image_name)
    await asyncio.sleep(3)
    # the environment should be on the page
    r = await get_service_page(
        "environments",
        app,
        cookies=cookies,
        allow_redirects=True,
    )
    r.raise_for_status()

    assert r.status_code == 200
    assert minimal_repo in r.text
