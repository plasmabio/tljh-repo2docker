import pytest

from jupyterhub.tests.utils import get_page


@pytest.mark.asyncio
async def test_images_list_admin(app):
    cookies = await app.login_user('admin')
    r = await get_page('environments', app, cookies=cookies, allow_redirects=False)
    r.raise_for_status()
    assert 'Repository' in r.text


@pytest.mark.asyncio
async def test_images_list_not_admin(app):
    cookies = await app.login_user('wash')
    r = await get_page('environments', app, cookies=cookies, allow_redirects=False)
    assert r.status_code == 403
