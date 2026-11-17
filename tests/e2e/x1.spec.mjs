import { join } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { test, expect, ROOT, git } from './harness.mjs';

async function shot(page, name) {
  await mkdir(join(ROOT, 'evidence/step7-ui'), { recursive: true });
  await page.screenshot({ path: join(ROOT, 'evidence/step7-ui', name), animations: 'disabled' });
}

test('H and a flick hide a card without deleting it', async ({ page, demo }) => {
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  const before = git(demo.vault, 'rev-parse', 'HEAD');
  await page.getByRole('button', { name: 'Juniper Events', exact: true }).focus();
  await page.keyboard.press('h');
  await expect(page.getByRole('button', { name: 'Show hidden (1)' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Juniper Events', exact: true })).toHaveCount(0);
  expect(git(demo.vault, 'rev-parse', 'HEAD')).toBe(before);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Juniper Events', exact: true })).toHaveCount(0);
  const tile = page.locator('[data-record-id="venture-cedar"]');
  const box = await tile.boundingBox();
  const pane = await page.locator('.react-flow').boundingBox();
  const saved = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
  await page.mouse.move(box.x + box.width / 2, box.y + 40);
  await page.mouse.down();
  await page.mouse.move(Math.max(0, pane.x - 20), Math.min(pane.y + pane.height - 30, box.y + 40), { steps: 12 });
  await page.mouse.up();
  await saved;
  await expect(page.getByRole('button', { name: 'Show hidden (2)' })).toBeVisible();
  await expect(tile).toHaveCount(0);
  await shot(page, 'dark-x1-hidden.png');
  await page.getByRole('button', { name: /Switch to light/ }).click();
  await shot(page, 'light-x1-hidden.png');
  await page.getByRole('button', { name: 'Show hidden (2)' }).click();
  await expect(page.getByRole('button', { name: 'Juniper Events', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cedar Rentals', exact: true })).toBeVisible();
  expect(git(demo.vault, 'rev-parse', 'HEAD')).toBe(before);
});
