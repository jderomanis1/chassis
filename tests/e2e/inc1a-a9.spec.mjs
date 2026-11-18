// Paused write controls must describe why, in the accessibility tree.
import { test, expect } from './harness.mjs';

const SENTENCE = 'Editing paused until the live store reconnects.';

async function described(locator) {
  return locator.evaluate(node => {
    const id = node.getAttribute('aria-describedby');
    if (!id) return '';
    return document.getElementById(id)?.textContent?.trim() || '';
  });
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test(`paused controls announce the pause at ${viewport.width}`, async ({ page, demo }) => {
    await page.setViewportSize(viewport);
    await page.clock.install();
    await page.goto(demo.origin);
    await expect(page.locator('[data-kind="venture"]').first()).toBeVisible();
    await page.route('**/api/version', route => route.abort());
    await page.clock.fastForward(4000);
    await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
    await page.goto(`${demo.origin}/#/v/venture-juniper`);
    const card = page.locator('[data-record-id="task-juniper-launch-2"]');
    await expect(card).toBeVisible();
    await card.dblclick();
    await page.locator('#edit-title').fill('Paused save');
    await page.route('**/api/records/**', route => {
      if (route.request().method() !== 'PATCH') return route.continue();
      return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
        code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) });
    });
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Keep mine and save again' })).toBeVisible();
    const chip = page.getByText('EDITING PAUSED', { exact: true });
    const box = await chip.boundingBox();
    expect(box.width).toBeGreaterThan(0);
    expect(box.height).toBeGreaterThan(0);
    const names = ['Undo', 'Edit', 'Save', 'Keep mine and save again'];
    for (const name of names) {
      const control = page.getByRole('button', { name, exact: true }).first();
      await expect(control).toHaveAttribute('aria-disabled', 'true');
      expect(await described(control)).toBe(SENTENCE);
    }
    await page.keyboard.press('Tab');
    const reached = new Set();
    for (let i = 0; i < 40; i += 1) {
      const name = await page.evaluate(() => document.activeElement?.textContent?.trim() || '');
      if (names.includes(name)) reached.add(name);
      await page.keyboard.press('Tab');
    }
    expect([...reached].sort()).toEqual([...names].sort());
    await page.unroute('**/api/version');
    await page.clock.fastForward(2000);
    await expect(page.getByText('Live store', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Save', exact: true })).not.toHaveAttribute('aria-describedby', /.+/);
  });
}
