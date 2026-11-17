import { join } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { test, expect, ROOT } from './harness.mjs';

async function run(page, command) {
  await page.keyboard.press('Control+k');
  const dialog = page.getByRole('dialog', { name: 'Command' });
  await expect(dialog).toBeVisible();
  await page.getByRole('textbox', { name: 'Command' }).fill(command);
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  return dialog;
}

test('the command bar runs the six view commands', async ({ page, demo }) => {
  await mkdir(join(ROOT, 'evidence/step7-ui'), { recursive: true });
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await run(page, 'show only blocked');
  await expect(page.getByRole('button', { name: 'Cedar Rentals', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Ridgeview HOA', exact: true })).toBeVisible();
  await page.waitForTimeout(400);
  await page.screenshot({ path: join(ROOT, 'evidence/step7-ui/dark-x2-command.png'), animations: 'disabled' });
  await page.getByRole('button', { name: /Switch to light/ }).click();
  await page.screenshot({ path: join(ROOT, 'evidence/step7-ui/light-x2-command.png'), animations: 'disabled' });
  const dialog = await run(page, 'make it pop');
  await expect(dialog).toContainText('zoom into <venture>');
  await expect(dialog).toContainText('clear all but active');
  await page.getByRole('textbox', { name: 'Command' }).fill('show all');
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await run(page, 'zoom into atlas');
  await expect(page).toHaveURL(/#\/v\/venture-atlas$/);
  await expect(page.getByRole('button', { name: 'Atlas Trades: launch review 3', exact: true })).toBeVisible();
  await run(page, 'clear all but active');
  await expect(page.getByRole('button', { name: 'Atlas Trades: launch review 1', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Atlas Trades: launch review 3', exact: true })).toBeVisible();
  await run(page, 'back');
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await run(page, 'fit');
  await expect(page.locator('[data-record-id="venture-ridgeview"]')).toBeVisible();
});
