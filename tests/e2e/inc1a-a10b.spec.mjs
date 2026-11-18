// The first paused drag explains itself, and a second drag does not repeat it.
import { test, expect } from './harness.mjs';

const MESSAGE = 'Moving cards is paused until the live store reconnects.';

async function drag(page, card) {
  const box = await card.boundingBox();
  await page.mouse.move(box.x + 40, box.y + 24);
  await page.mouse.down();
  await page.mouse.move(box.x + 140, box.y + 24, { steps: 6 });
  await page.mouse.up();
}

test('the paused-move message is shown once', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.clock.install();
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  const card = page.locator('[data-record-id="task-juniper-launch-2"]');
  await expect(card).toBeVisible();
  await page.route('**/api/version', route => route.abort());
  await page.clock.fastForward(4000);
  await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
  await drag(page, card);
  await expect(page.locator('p.attn')).toContainText(MESSAGE);
  await drag(page, card);
  await expect(page.getByText(MESSAGE)).toHaveCount(1);
});
