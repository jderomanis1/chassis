// Regression for UAT-W0 re-run blocker 1: wrong card's editor opens after a long-title save.
// Drop into tests/e2e/ (uses the existing harness.mjs demo fixture: fictional demo-init vault, loopback portal).
// Invariant 1: the record id the editor PATCHes equals the id of the card that was double-clicked.
// Invariant 2: changing what the details strip shows must not move the canvas (root cause).
import { test, expect } from './harness.mjs';

const LONG = 'N'.repeat(200); // 200 chars, under the 240 max, no spaces: wraps to several lines in the strip

async function paneTop(page) {
  return page.locator('.react-flow').evaluate(node => Math.round(node.getBoundingClientRect().top));
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('after a long-title save, double-clicking another card edits that card', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const source = page.locator('[data-record-id="task-juniper-launch-2"]');
      const target = page.locator('[data-record-id="task-juniper-launch-3"]');
      await expect(target).toBeVisible();
      await source.dblclick();
      await page.getByLabel('Title').fill(LONG);
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(source).toBeFocused(); // focus returns to the saved card, so the strip shows the long title

      // Press where the target card is on screen right now, like a person would.
      const box = await target.boundingBox();
      const targetTitle = await target.getAttribute('aria-label');
      await page.mouse.dblclick(box.x + box.width / 2, box.y + box.height / 2);
      const dialog = page.getByRole('dialog');
      await expect(dialog).toHaveAttribute('aria-label', `Edit ${targetTitle}`);

      await page.getByLabel('Title').fill('Juniper fictional regression title');
      const saved = page.waitForResponse(r => r.url().includes('/api/records/') && r.request().method() === 'PATCH');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      const response = await saved;
      expect(decodeURIComponent(new URL(response.url()).pathname.split('/').pop())).toBe('task-juniper-launch-3');
      expect((await response.json()).record.id).toBe('task-juniper-launch-3');
    });

    test('the details strip never moves the canvas', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const source = page.locator('[data-record-id="task-juniper-launch-2"]');
      await expect(source).toBeVisible();
      const idle = await paneTop(page);
      await source.dblclick();
      await page.getByLabel('Title').fill(LONG);
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(page.locator('.hover-slot h4')).toHaveText(LONG); // strip is showing the long title
      expect(await paneTop(page)).toBe(idle);
      await page.locator('[data-record-id="task-juniper-launch-3"]').focus();
      expect(await paneTop(page)).toBe(idle);
    });
  });
}
