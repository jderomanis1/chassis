import { test, expect } from './harness.mjs';

// A short silent PCM fixture exercises Chromium's media pipeline without shipping a demo voice.
const wavHeader = Buffer.from('UklGRuQGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YcAGAAA=', 'base64');
const silence = Buffer.concat([wavHeader, Buffer.alloc(1728, 128)]);
for (const gesture of ['autoplay', 'click', 'keydown']) {
  test(`intro plays once across renders and reconnects with ${gesture}`, async ({ playwright, demo }) => {
    const policy = gesture === 'autoplay' ? 'no-user-gesture-required' : 'user-gesture-required';
    const browser = await playwright.chromium.launch({
      executablePath: process.env.CHASSIS_CHROMIUM || '/usr/bin/chromium',
      args: [`--autoplay-policy=${policy}`],
    });
    try {
      const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
      const diagnostics = [];
      const media = [];
      page.on('console', message => {
        if (['error', 'warning'].includes(message.type())) diagnostics.push(message.text());
      });
      page.on('pageerror', error => diagnostics.push(error.message));
      page.on('request', request => {
        if (request.resourceType() === 'media') media.push(request.url());
      });
      await page.route(demo.origin + '/', async route => {
        const html = await route.fetch();
        const body = (await html.text()).replace(/<audio\b[^>]*\bid="canvas-intro"[^>]*>/,
          '<audio id="canvas-intro" preload="none" src="/test-intro.wav">');
        await route.fulfill({ response: html, body });
      });
      const url = demo.origin + '/test-intro.wav';
      await page.route(url, route => route.fulfill({ contentType: 'audio/wav', body: silence }));
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
        else await page.keyboard.press('Tab');
      }
      await expect.poll(starts).toBe(1);
      await page.getByRole('button', { name: /^Theme:/ }).click();
      await page.route('**/api/version', route => route.fulfill({ status: 200, body: 'offline' }));
      await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
      await page.unroute('**/api/version');
      await expect(page.getByText('Live store', { exact: true })).toBeVisible();
      await page.keyboard.press('Tab');
      expect(await starts()).toBe(1);
      expect(new Set(media)).toEqual(new Set([url]));
      expect(diagnostics).toEqual([]);
    } finally {
      await browser.close();
    }
  });
}
