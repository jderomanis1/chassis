// Nothing above the canvas may change height: save, focus, hover, a poll, and search.
import { test, expect } from './harness.mjs';

async function paneTop(page) {
  return page.locator('.react-flow').evaluate(node => Math.round(node.getBoundingClientRect().top));
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('the canvas top stays put across save, focus, hover, poll, and search', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const saved = page.locator('[data-record-id="task-juniper-launch-2"]');
      const other = page.locator('[data-record-id="task-juniper-launch-3"]');
      await expect(saved).toBeVisible();
      const idle = await paneTop(page);
      await saved.dblclick();
      await page.getByLabel('Title').fill('Juniper fictional geometry title');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(saved).toBeFocused();
      expect(await paneTop(page), 'after save and focus return').toBe(idle);
      await other.hover();
      expect(await paneTop(page), 'after hover').toBe(idle);
      await page.waitForTimeout(1200);
      expect(await paneTop(page), 'after a poll').toBe(idle);
      await page.getByLabel('Search records').fill('Juniper');
      await page.getByRole('button', { name: 'Search', exact: true }).click();
      await expect(page.locator('.hits')).toBeVisible();
      expect(await paneTop(page), 'after search').toBe(idle);
    });
  });
}
