import { expect, test, Page } from '@playwright/test';

async function login(page: Page, user: string) {
  await page.goto('hub/login');
  await page.getByText('Sign in');
  await page.getByLabel('Username:').fill(user);
  await page.getByLabel('Password:').fill('123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'JupyterHub logo' });
}
test.describe('tljh_repo2docker UI Tests', () => {
  test.beforeEach(({ page }) => {
    page.setDefaultTimeout(60000);
  });

  test.afterEach(async ({ page }) => {
    await page.close({ runBeforeUnload: true });
  });

  test('Render Login', async ({ page }) => {
    await page.goto('hub/login');
    await page.getByText('Sign in');
    await expect(await page.screenshot()).toMatchSnapshot('login-page.png');
  });

  test('Log in with admin account', async ({ page }) => {
    await login(page, 'alice');
    await page.getByRole('button', { name: 'Services' }).click();
    await page.getByRole('link', { name: 'tljh_repo2docker' }).click();
    await page.waitForURL('**/servers');
    await page.waitForTimeout(500);
    await expect(await page.screenshot()).toMatchSnapshot('admin.png');
  });

  test('Log in with user account', async ({ page }) => {
    await login(page, 'user');
    await page.getByRole('button', { name: 'Services' }).click();
    await page.getByRole('link', { name: 'tljh_repo2docker' }).click();
    await page.waitForURL('**/servers');
    await page.waitForTimeout(500);
    await expect(await page.screenshot()).toMatchSnapshot('user.png');
  });

  test('Render servers page', async ({ page }) => {
    await login(page, 'alice');
    await page.getByRole('button', { name: 'Services' }).click();
    await page.getByRole('link', { name: 'tljh_repo2docker' }).click();
    await page.waitForURL('**/servers');
    await page.waitForTimeout(500);
    await page.waitForSelector('div:has-text("No servers are running")', {
      timeout: 1000
    });
    await expect(await page.screenshot()).toMatchSnapshot('servers-page.png');
  });

  test('Render environments page', async ({ page }) => {
    await login(page, 'alice');
    await page.getByRole('button', { name: 'Services' }).click();
    await page.getByRole('link', { name: 'tljh_repo2docker' }).click();
    await page.waitForURL('**/servers');
    await page.getByRole('link', { name: 'Environments' }).click();
    await page.waitForURL('**/environments');
    await page.waitForTimeout(500);
    await page.waitForSelector('div:has-text("No environment available")', {
      timeout: 1000
    });
    await expect(await page.screenshot()).toMatchSnapshot(
      'environments-page.png'
    );
  });

  test('Render environments dialog', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/environments');
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Create new environment' }).click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Create Environment' });
    await expect(await page.screenshot()).toMatchSnapshot(
      'environment-dialog.png'
    );
  });

  test('Create new environments', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/environments');
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Create new environment' }).click();
    await page
      .getByLabel('Repository URL *')
      .fill('https://github.com/plasmabio/template-python');
    await page.getByPlaceholder('HEAD').fill('HEAD');
    await page
      .getByPlaceholder('Example: course-python-101-B37')
      .fill('python-env');
    await page.getByRole('button', { name: 'Create Environment' }).click();

    await page.waitForTimeout(1000);
    await page.waitForURL('**/environments');
    await page
      .getByRole('row', { name: 'python-env https://github.com' })
      .getByRole('button')
      .first()
      .click();
    if (process.env.CONFIG_FILE === 'binderhub') {
      await page.waitForSelector('span:has-text("Successfully tagged")', {
        timeout: 600000
      });
    } else {
      await page.waitForSelector('span:has-text("naming to docker")', {
        timeout: 600000
      });
    }

    await expect(await page.screenshot()).toMatchSnapshot(
      'environment-console.png',
      {
        maxDiffPixelRatio: 0.05
      }
    );
    await page.getByRole('button', { name: 'Close' }).click();
    await page.waitForTimeout(500);
    await expect(await page.screenshot()).toMatchSnapshot(
      'environment-list.png'
    );
  });

  test('Render servers dialog', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/servers');
    await page.waitForTimeout(500);
    await page.waitForSelector('div:has-text("No servers are running")', {
      timeout: 1000
    });
    await page.getByRole('button', { name: 'Create new Server' }).click();
    await page.waitForTimeout(1000);
    await page.getByText('Server Options').click();
    await expect(await page.screenshot()).toMatchSnapshot('servers-dialog.png');
  });

  test('Start server', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/servers');
    await page.waitForTimeout(500);
    await page.waitForSelector('div:has-text("No servers are running")', {
      timeout: 1000
    });
    await page.getByRole('button', { name: 'Create new Server' }).click();

    await page
      .getByRole('textbox', { name: 'Server name' })
      .fill('test-server');
    await page.getByLabel('Select row').check();
    await page.waitForSelector('div:has-text("1 row selected")', {
      timeout: 1000
    });
    const createServer = await page.getByRole('button', {
      name: 'Create Server'
    });
    await createServer.click();
    await await expect(createServer).toHaveCount(0, { timeout: 20000 });
    await page.waitForURL('**/servers');
    await page.waitForTimeout(1000);

    await expect(await page.screenshot()).toMatchSnapshot(
      'running-servers.png'
    );
  });

  test('Remove server', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/servers');
    await page.waitForTimeout(1000);

    await page.getByRole('button', { name: 'Stop Server' }).click();
    await page.waitForTimeout(500);
    await expect(await page.screenshot()).toMatchSnapshot(
      'server-remove-confirm.png'
    );
    const accept = await page.getByRole('button', { name: 'Accept' });
    await accept.click();
    await await expect(accept).toHaveCount(0);
    await page.waitForTimeout(1000);
    await page.waitForURL('**/servers');
    await expect(await page.screenshot()).toMatchSnapshot('server-removed.png');
  });

  test('Remove environment', async ({ page }) => {
    await login(page, 'alice');
    await page.goto('/services/tljh_repo2docker/environments');
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: 'Remove' }).click();
    await page.waitForTimeout(500);
    await expect(await page.screenshot()).toMatchSnapshot(
      'environment-remove-confirm.png'
    );
    const accept = await page.getByRole('button', { name: 'Accept' });
    await accept.click();
    await await expect(accept).toHaveCount(0);
    await page.waitForTimeout(1000);
    await page.waitForURL('**/environments');
    await expect(await page.screenshot()).toMatchSnapshot(
      'environment-removed.png'
    );
  });
});
