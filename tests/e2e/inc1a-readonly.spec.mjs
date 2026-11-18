// Read-only keeps its chip and does not announce a paused move.
import { test, expect } from './harness.mjs';

const MESSAGE = 'Moving cards is paused until the live store reconnects.';
const CHIP = 'Read only · editing is off';

async function drag(page) {
  const card = page.locator('[data-record-id="task-juniper-launch-2"]');
  const box = await card.boundingBox();
  await page.mouse.move(box.x + 40, box.y + 24);
  await page.mouse.down();
  await page.mouse.move(box.x + 140, box.y + 24, { steps: 6 });
  await page.mouse.up();
}

test('read-only does not change the chip or announce a move', async ({ page, demo }) => {
  await page.route('**/api/session', async route => {
    const response = await route.fetch();
    const body = await response.json();
    body.writes_enabled = false;
    await route.fulfill({ response, json: body });
  });
  await page.clock.install();
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  await expect(page.locator('.mode')).toHaveText(CHIP);
  await page.route('**/api/version', route => route.abort());
  await page.clock.fastForward(4000);
  await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
  await expect(page.locator('.mode')).toHaveText(CHIP);
  await drag(page);
  await expect(page.getByText(MESSAGE)).toHaveCount(0);
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page.locator('.mode')).toHaveText(CHIP);
  await drag(page);
  await expect(page.getByText(MESSAGE)).toHaveCount(0);
  await page.clock.fastForward(36000);
  await expect(page.getByText('Offline', { exact: true })).toBeVisible();
  await expect(page.locator('.mode')).toHaveText(CHIP);
  await page.unroute('**/api/version');
  await page.clock.fastForward(2000);
  await expect(page.getByText('Live store', { exact: true })).toBeVisible();
  await expect(page.locator('.mode')).toHaveText(CHIP);
});
