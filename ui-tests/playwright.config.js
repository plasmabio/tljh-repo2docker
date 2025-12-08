const snapshotDir = `${process.env.CONFIG_FILE}_snapshots`;

const configFile = `jupyterhub_config_${process.env.CONFIG_FILE}.py`;

module.exports = {
  timeout: 600000,
  reporter: [[process.env.CI ? 'dot' : 'list'], ['html']],
  outputDir: `${process.env.CONFIG_FILE}-test-results`,
  use: {
    baseURL: 'http://localhost:8000',
    video: 'retain-on-failure',
    trace: 'retain-on-failure'
  },
  retries: 0,
  expect: {
    toMatchSnapshot: {
      maxDiffPixelRatio: 0.001
    }
  },
  snapshotPathTemplate: `{testDir}/${snapshotDir}/{testFileName}/{arg}{ext}`,
  webServer: {
    command: `python -m jupyterhub -f ./${configFile}`,
    url: 'http://localhost:8000',
    timeout: 120 * 1000,
    reuseExistingServer: true,
    gracefulShutdown: 60000
  }
};
