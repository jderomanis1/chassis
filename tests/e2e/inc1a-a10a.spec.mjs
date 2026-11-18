// Offline cards stay put, and a press-and-move pans instead of dragging.
import { test, expect } from './harness.mjs';

test('an offline drag does not move the card', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.clock.install();
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  const card = page.locator('[data-record-id="task-juniper-launch-2"]');
  await expect(card).toBeVisible();
  const place = () => card.evaluate(node => node.closest('.react-flow__node').style.transform);
  const before = await place();
  const paneBefore = await page.locator('.react-flow__viewport').evaluate(node => node.style.transform);
  let puts = 0;
  page.on('request', request => {
    if (request.method() === 'PUT' && request.url().includes('/api/layout')) puts += 1;
  });
  await page.route('**/api/version', route => route.abort());
  await page.clock.fastForward(4000);
  await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
  expect(await card.evaluate(node => getComputedStyle(node).cursor)).toBe('default');
  const box = await card.boundingBox();
  await page.mouse.move(box.x + 40, box.y + 24);
  await page.mouse.down();
  await page.mouse.move(box.x + 140, box.y + 24, { steps: 8 });
  await page.mouse.up();
  expect(await place()).toBe(before);
  expect(puts).toBe(0);
  const paneAfter = await page.locator('.react-flow__viewport').evaluate(node => node.style.transform);
  expect(paneAfter).not.toBe(paneBefore);
  await page.unroute('**/api/version');
  await page.clock.fastForward(2000);
  await expect(page.getByText('Live store', { exact: true })).toBeVisible();
  expect(await place()).toBe(before);
  expect(puts).toBe(0);
});
