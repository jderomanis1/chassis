// One user action must send one PATCH, even when the click is repeated in the same tick.
import { test, expect } from './harness.mjs';

async function openTask(page, demo) {
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  const card = page.locator('[data-record-id="task-juniper-launch-2"]');
  await expect(card).toBeVisible();
  await card.dblclick();
  await expect(page.getByRole('dialog')).toBeVisible();
}

async function onePatch(page, fire) {
  let release = () => {};
  const gate = new Promise(resolve => { release = resolve; });
  let patches = 0;
  await page.route('**/api/records/**', async route => {
    if (route.request().method() !== 'PATCH') return route.continue();
    patches += 1;
    await gate;
    await route.fallback();
  });
  await fire();
  await page.waitForTimeout(500);
  const count = patches;
  release();
  await page.unroute('**/api/records/**');
  expect(count).toBe(1);
}

test('repeated submits in one tick send a single PATCH', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  await page.locator('#edit-title').fill('One patch from two submits');
  await onePatch(page, () => page.locator('form.editor-form').evaluate(form => {
    form.requestSubmit();
    form.requestSubmit();
  }));

  await openTask(page, demo);
  await page.locator('#edit-title').fill('One patch from five clicks');
  await onePatch(page, () => page.locator('form.editor-form').evaluate(form => {
    const save = form.querySelector('button[type="submit"]');
    for (let i = 0; i < 5; i += 1) save.click();
  }));

  await openTask(page, demo);
  await page.locator('#edit-title').fill('One patch from enter and click');
  await onePatch(page, () => page.locator('form.editor-form').evaluate(form => {
    form.requestSubmit();
    form.querySelector('button[type="submit"]').click();
  }));

  await openTask(page, demo);
  await page.locator('#edit-title').fill('Conflict then one keep');
  await page.route('**/api/records/**', route => {
    if (route.request().method() !== 'PATCH') return route.continue();
    return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
      code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) });
  });
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Keep mine and save again' })).toBeVisible();
  await page.unroute('**/api/records/**');
  await onePatch(page, () => page.getByRole('button', { name: 'Keep mine and save again' }).evaluate(button => {
    button.click();
    button.click();
  }));
});
