// After a save the editor closes before reload. Rebuilding nodes without their
// measured size hides every card for a frame, so the next double-click can miss.
// The hide is one frame and shows up at both 1280 and 768, so this samples
// visibility on every animation frame instead of waiting on a slow click.
import { test, expect } from './harness.mjs';

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('cards stay visible after a save and the next card still opens', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const source = page.locator('[data-record-id="task-juniper-launch-2"]');
      const target = page.locator('[data-record-id="task-juniper-launch-3"]');
      await expect(source).toBeVisible();
      await expect(target).toBeVisible();
      await page.evaluate(() => {
        window.__hiddenFrames = 0;
        const scan = () => {
          for (const node of document.querySelectorAll('.react-flow__node')) {
            if (getComputedStyle(node).visibility === 'hidden') window.__hiddenFrames += 1;
          }
        };
        const pane = document.querySelector('.react-flow');
        window.__hideObserver = new MutationObserver(scan);
        window.__hideObserver.observe(pane, { attributes: true, attributeFilter: ['style'], childList: true, subtree: true });
        const watch = () => {
          scan();
          window.__hideWatch = requestAnimationFrame(watch);
        };
        watch();
      });
      await source.dblclick();
      await page.getByLabel('Title').fill('Juniper fictional measured title');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const hidden = await page.evaluate(() => window.__hiddenFrames);
      expect(hidden, 'cards were visibility:hidden during the save').toBe(0);
      const title = await target.getAttribute('aria-label');
      const box = await target.boundingBox();
      await page.mouse.dblclick(box.x + box.width / 2, box.y + box.height / 2);
      await expect(page.getByRole('dialog')).toHaveAttribute('aria-label', `Edit ${title}`);
    });
  });
}
