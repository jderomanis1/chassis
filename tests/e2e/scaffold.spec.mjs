import { test, expect } from './harness.mjs';

test('served build loads only local assets and persists the accessible theme', async ({ page, demo }) => {
  const foreign = [], errors = [];
  page.on('request', request => { if (!request.url().startsWith(demo.origin)) foreign.push(request.url()); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(demo.origin);
  await expect(page.getByRole('heading', { name: /Every venture/ })).toBeVisible();
  await expect(page.getByText('Editing enabled', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Theme: dark. Switch to light mode' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  expect(foreign).toEqual([]);
  expect(errors).toEqual([]);
  const fonts = await page.evaluate(async () => {
    const specs = ['500 16px "Chakra Petch"', '400 16px "IBM Plex Sans"', '400 16px "JetBrains Mono"'];
    await Promise.all(specs.map(spec => document.fonts.load(spec)));
    await document.fonts.ready;
    return specs.map(spec => document.fonts.check(spec));
  });
  expect(fonts).toEqual([true, true, true]);
});

test('loading and empty states', async ({ page, demo }) => {
  let release;
  const wait = new Promise(resolve => { release = resolve; });
  await page.route('**/api/snapshot', async route => { await wait; await route.fulfill({ json: { etag: 'empty', ventures: [] } }); });
  await page.goto(demo.origin);
  await expect(page.getByRole('status')).toContainText('Loading');
  release();
  await expect(page.getByText('No ventures yet', { exact: true })).toBeVisible();
});

for (const status of [404, 500]) test(`error state for HTTP ${status}`, async ({ page, demo }) => {
  await page.route('**/api/snapshot', route => route.fulfill({ status, json: { error: { code: 'test', message: 'Sample service unavailable' } } }));
  await page.goto(demo.origin);
  await expect(page.getByRole('alert')).toContainText("Couldn't load your ventures. The live store didn't answer.");
  await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
});

test('network failure and writes-disabled state are explicit', async ({ page, demo }) => {
  await page.route('**/api/snapshot', route => route.abort());
  await page.goto(demo.origin);
  await expect(page.getByRole('alert')).toContainText("Couldn't load your ventures. The live store didn't answer.");
  await page.unroute('**/api/snapshot');
  await page.route('**/api/session', async route => {
    const response = await route.fetch();
    await route.fulfill({ json: { ...(await response.json()), writes_enabled: false } });
  });
  await page.reload();
  await expect(page.getByText('Read only · editing is off', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Edit', exact: true })).toHaveCount(0);
});
