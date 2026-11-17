import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: '../tests/e2e', workers: 1, timeout: 30000,
  expect: { timeout: 6000 }, outputDir: '../.chassis/e2e', reporter: 'list',
  use: { viewport: { width: 1440, height: 900 }, colorScheme: 'dark', trace: 'off',
    launchOptions: { executablePath: process.env.CHASSIS_CHROMIUM || '/usr/bin/chromium' } } });
