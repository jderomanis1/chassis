import { existsSync } from 'node:fs';
import { test, expect } from './harness.mjs';

for (const gesture of ['autoplay', 'click', 'keydown', 'tap']) {
  test(`intro plays once across renders and reconnects with ${gesture}`, async ({ playwright, demo }) => {
    test.setTimeout(45000);
    const policy = gesture === 'autoplay' ? 'no-user-gesture-required' : 'user-gesture-required';
    const chrome = '/usr/bin/google-chrome';
    const executablePath = existsSync(chrome) ? chrome : process.env.CHASSIS_CHROMIUM || '/usr/bin/chromium';
    const browser = await playwright.chromium.launch({
      executablePath,
      args: [`--autoplay-policy=${policy}`],
    });
    try {
      const device = gesture === 'tap' ? playwright.devices['Pixel 7'] : { viewport: { width: 1280, height: 800 } };
      const page = await browser.newPage(device);
      console.log(`I-002 ${gesture}: ${executablePath} ${browser.version()}, ${page.viewportSize().width}px`);
      const diagnostics = [];
      const media = [];
      const foreign = [];
      page.on('console', message => {
        if (['error', 'warning'].includes(message.type())) diagnostics.push([message.location().url, message.text()]);
      });
      page.on('pageerror', error => diagnostics.push(error.message));
      page.on('request', request => {
        if (new URL(request.url()).origin !== demo.origin) foreign.push(request.url());
        if (request.resourceType() === 'media') media.push(request.url());
      });
      const url = demo.origin + '/intro.mp3';
      await page.addInitScript(() => {
        window.introStarts = 0;
        document.addEventListener('playing', event => {
          if (event.target.id === 'canvas-intro') window.introStarts++;
        }, true);
      });
      const starts = () => page.evaluate(() => window.introStarts);
      await page.goto(demo.origin);
      await expect(page.getByText('Editing enabled')).toBeVisible();
      if (gesture !== 'autoplay') {
        expect(await starts()).toBe(0);
        if (gesture === 'click') await page.getByRole('heading', { level: 1 }).click();
        else if (gesture === 'tap') await page.getByRole('heading', { level: 1 }).tap();
        else await page.keyboard.press('Tab');
      }
      await expect.poll(starts).toBe(1);
      await page.waitForFunction(() => document.getElementById('canvas-intro').ended);
      await page.getByRole('button', { name: /^Theme:/ }).click();
      await page.route('**/api/version', route => route.fulfill({ status: 200, body: 'offline' }));
      await expect(page.getByText('EDITING PAUSED', { exact: true })).toBeVisible();
      await page.unroute('**/api/version');
      await expect(page.getByText('Editing enabled', { exact: true })).toBeVisible();
      await page.keyboard.press('Tab');
      expect(await starts()).toBe(1);
      expect(new Set(media)).toEqual(new Set([url]));
      if (gesture === 'autoplay') {
        await page.reload();
        await expect.poll(starts).toBe(1);
      }
      expect(foreign).toEqual([]);
      expect(diagnostics).toEqual([]);
    } finally {
      await browser.close();
    }
  });
}
