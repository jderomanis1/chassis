// A failed poll must leave the cards and the camera where they are.
import { test, expect } from './harness.mjs';

async function paneTop(page) {
  return page.locator('.react-flow').evaluate(node => Math.round(node.getBoundingClientRect().top));
}

test('the first load failure uses plain words and focuses Try again', async ({ page, demo }) => {
  await page.route('**/api/**', route => route.abort());
  await page.goto(demo.origin);
  const alert = page.getByRole('alert');
  await expect(alert).toContainText("Couldn't load your ventures. The live store didn't answer.");
  await expect(alert).not.toContainText('Cannot reach');
  await expect(page.getByRole('button', { name: 'Try again' })).toBeFocused();
});

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('a version outage keeps the cards, then recovers', async ({ page, demo }) => {
      await page.clock.install();
      await page.goto(demo.origin);
      const card = page.locator('[data-kind="venture"]').first();
      await expect(card).toBeVisible();
      await page.clock.fastForward(300);
      await page.getByRole('button', { name: 'Edit', exact: true }).first().click();
      const title = page.getByLabel('Title');
      await expect(title).toBeFocused();
      const top = await paneTop(page);
      let blocked = true;
      await page.route('**/api/version', route => blocked ? route.abort() : route.continue());
      await page.clock.fastForward(3500);
      await expect(page.locator('.react-flow')).toBeVisible();
      await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Edit', exact: true }).first()).toBeDisabled();
      await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
      await expect(page.getByRole('button', { name: 'Save', exact: true })).toHaveAttribute('title', 'Reconnect to edit');
      expect(await paneTop(page)).toBe(top);
      await expect(title).toBeFocused();
      await page.clock.fastForward(37000);
      await expect(page.getByText('Offline', { exact: true })).toBeVisible();
      await expect(page.locator('.react-flow')).toBeVisible();
      expect(await paneTop(page)).toBe(top);
      blocked = false;
      await page.clock.fastForward(2000);
      await expect(page.getByText('Live store', { exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
      expect(await paneTop(page)).toBe(top);
      await expect(title).toBeFocused();
    });
  });
}
