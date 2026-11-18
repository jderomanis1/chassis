// A non-conflict notice, search hits, and Show hidden share one column.
import { test, expect } from './harness.mjs';

function overlaps(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('a notice stays clear of the other overlays while reads are pending', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const hidden = page.locator('[data-record-id="task-juniper-launch-3"]');
      await expect(hidden).toBeVisible();
      const hid = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
      await hidden.focus();
      await page.keyboard.press('h');
      expect((await hid).status()).toBe(200);
      await expect(hidden).toHaveCount(0);
      await page.getByLabel('Search records').fill('Juniper');
      await page.getByRole('button', { name: 'Search', exact: true }).click();
      const hits = page.locator('.hits li');
      await expect(hits).not.toHaveCount(0);
      await page.route('**/api/search**', route => route.fulfill({
        status: 500, contentType: 'application/json',
        body: JSON.stringify({ error: { message: 'Search is unavailable.' } }),
      }));
      await page.getByRole('button', { name: 'Search', exact: true }).click();
      await expect(page.locator('p.attn')).toContainText('Search is unavailable.');
      let release = () => {};
      const gate = new Promise(resolve => { release = resolve; });
      await page.route(/\/api\/(ventures|initiatives|graph)/, async route => { await gate; await route.continue(); });
      try {
        const overlays = [page.locator('p.attn'), page.locator('.hits'), page.locator('.show-hidden')];
        const boxes = [];
        for (const overlay of overlays) boxes.push(await overlay.boundingBox());
        expect(boxes.every(Boolean)).toBe(true);
        for (let i = 0; i < boxes.length; i += 1) {
          for (let j = i + 1; j < boxes.length; j += 1) expect(overlaps(boxes[i], boxes[j])).toBe(false);
        }
        const noticeBox = boxes[0];
        await expect.poll(() => page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest('p.attn')?.textContent || '', {
          x: noticeBox.x + 12, y: noticeBox.y + noticeBox.height / 2 })).toContain('Search is unavailable.');
        const shown = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
        await page.getByRole('button', { name: 'Show hidden (1)' }).click();
        expect((await shown).status()).toBe(200);
        await expect(hidden).toBeVisible();
        await expect(page.locator('p.attn')).toContainText('Search is unavailable.');
      } finally { release(); }
    });
  });
}
