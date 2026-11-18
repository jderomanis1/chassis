// A reload must not be counted as missed version checks, and a failed reload must run again.
import { test, expect } from './harness.mjs';

test('a slow reload does not show Reconnecting', async ({ page, demo }) => {
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]').first()).toBeVisible();
  let hold = false;
  await page.route('**/api/version', route => hold
    ? route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ etag: 'fictional-etag-change' }), headers: { ETag: '"fictional-etag-change"' } })
    : route.continue());
  await page.route('**/api/snapshot', async route => {
    if (hold) await new Promise(resolve => setTimeout(resolve, 3500));
    await route.continue();
  });
  hold = true;
  let saw = false;
  const watch = setInterval(async () => {
    const text = await page.locator('.live').textContent().catch(() => '');
    if (text === 'Reconnecting') saw = true;
  }, 100);
  await page.waitForTimeout(5000);
  clearInterval(watch);
  expect(saw, 'a reload in flight was counted as a missed poll').toBe(false);
});

test('a failed reload during an outage runs again when the store returns', async ({ page, demo }) => {
  await page.clock.install();
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  await expect(page.locator('[data-record-id="task-juniper-launch-2"]')).toBeVisible();
  let down = true;
  await page.route('**/api/**', route => {
    const url = route.request().url();
    if (!down) return route.continue();
    if (/\/api\/(version|snapshot|ventures|initiatives|graph|layout|undo)/.test(url)) return route.abort();
    return route.continue();
  });
  await page.evaluate(() => { location.hash = '#/v/venture-ridgeview'; });
  await page.clock.fastForward(1500);
  await expect(page.locator('[data-record-id="task-juniper-launch-2"]')).toBeVisible();
  down = false;
  await page.clock.fastForward(2500);
  await expect(page.locator('[data-record-id="task-ridgeview-launch-2"]')).toBeVisible();
});
