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

    test('an outage sends no writes, and editing works again after', async ({ page, demo }) => {
      await page.clock.install();
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      await page.clock.fastForward(300);
      const card = page.locator('[data-record-id="task-juniper-launch-2"]');
      await expect(card).toBeVisible();
      await card.dblclick();
      await page.getByLabel('Title').fill('Juniper outage undo title');
      const first = page.waitForResponse(response => response.request().method() === 'PATCH');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      expect((await first).ok()).toBeTruthy();
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await card.dblclick();
      const next = page.getByLabel('Next step');
      await next.fill('Hold this fictional step during the outage');
      const writes = [];
      page.on('request', request => {
        if (['PATCH', 'POST', 'PUT'].includes(request.method())) writes.push(request.method());
      });
      let blocked = true;
      await page.route('**/api/version', route => blocked ? route.abort() : route.continue());
      await page.clock.fastForward(3500);
      await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
      await next.press('Enter');
      await page.clock.fastForward(500);
      expect(writes, 'Enter in Next step').toEqual([]);
      await expect(next).toHaveValue('Hold this fictional step during the outage');
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await card.dblclick();
      await page.clock.fastForward(300);
      expect(writes, 'double-click').toEqual([]);
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await page.keyboard.press('Control+z');
      await page.clock.fastForward(500);
      expect(writes, 'undo').toEqual([]);
      const box = await card.boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 36, box.y + box.height / 2, { steps: 6 });
      await page.mouse.up();
      await page.clock.fastForward(500);
      expect(writes, 'drag').toEqual([]);
      const from = page.locator('[data-record-id="task-juniper-launch-1"] .react-flow__handle-right');
      const to = page.locator('[data-record-id="task-juniper-operations-1"] .react-flow__handle-left');
      await from.dragTo(to);
      await page.clock.fastForward(500);
      expect(writes, 'link').toEqual([]);
      blocked = false;
      await page.clock.fastForward(2000);
      await expect(page.getByText('Live store', { exact: true })).toBeVisible();
      await card.dblclick();
      await page.getByLabel('Title').fill('Juniper recovered title');
      const again = page.waitForResponse(response => response.request().method() === 'PATCH');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      expect((await again).ok()).toBeTruthy();
    });
  });
}

test('a hung version check turns amber after three polls', async ({ page, demo }) => {
  await page.clock.install();
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]').first()).toBeVisible();
  await page.route('**/api/version', () => {});
  await page.clock.fastForward(10000);
  await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
  await expect(page.locator('.react-flow')).toBeVisible();
});

test.describe('at 375px', () => {
  test.use({ viewport: { width: 375, height: 700 } });
  test('a phone press does not open the editor while offline', async ({ page, demo }) => {
  await page.clock.install();
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  await page.clock.fastForward(300);
  const card = page.locator('[data-record-id="task-juniper-launch-3"]');
  await expect(card).toBeVisible();
  let blocked = true;
  await page.route('**/api/version', route => blocked ? route.abort() : route.continue());
  await page.clock.fastForward(3500);
  await expect(page.locator('.react-flow')).toBeVisible();
  await card.dispatchEvent('pointerdown', { bubbles: true, button: 0 });
  await expect(page.getByRole('dialog')).toHaveCount(0);
  });
});
