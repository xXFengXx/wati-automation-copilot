import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  outputDir: '../tmp/browser-tests',
  use: { baseURL: 'http://127.0.0.1:8011', channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true, viewport: {width: 1440, height: 1050}, trace: 'retain-on-failure' },
  webServer: {
    command: '.venv\\Scripts\\python.exe -m uvicorn backend.tests.e2e_server:app --host 127.0.0.1 --port 8011',
    cwd: '..',
    url: 'http://127.0.0.1:8011/api/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
});
