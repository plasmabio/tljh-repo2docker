module.exports = {
  timeout: 600000,
  reporter: [[process.env.CI ? 'dot' : 'list'], ['html']],
  use: {
    baseURL: 'http://localhost:8000',
    video: 'retain-on-failure',
    trace: 'on-first-retry'
  },
  retries: 1,
  expect: {
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.01
    }
  },
  webServer: {
    command: 'python -m jupyterhub -f ../jupyterhub_config.py',
    url: 'http://localhost:8000',
    timeout: 120 * 1000,
    reuseExistingServer: true
  }
};
