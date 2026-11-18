import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { camerasClose } from '../../frontend/src/camera.js';
import { test, expect, CLI, git } from './harness.mjs';

const RESTRICTED = ['task-launch-budget', 'Review the private fictional budget', 'Fictional Private Steward',
  'Fictional private budget planning note'];

async function hidden(page) {
  const html = await page.content();
  const text = await page.locator('body').innerText();
  for (const secret of RESTRICTED) {
    expect(html).not.toContain(secret);
    expect(text).not.toContain(secret);
  }
}

test('seven live venture tiles use health colors, controls, and inert text', async ({ page, demo }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('dialog', () => { throw new Error('Unexpected script dialog'); });
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await expect.poll(async () => {
    const box = await page.locator('[data-record-id="venture-ridgeview"]').boundingBox();
    const pane = await page.locator('.react-flow').boundingBox();
    return Boolean(box && pane && box.y >= pane.y - 1 && box.y + box.height <= pane.y + pane.height + 1);
  }).toBe(true);
  for (const title of ['Ridgeview HOA', 'Acme D2C', 'Cedar Rentals', 'Lumen Skincare', 'Atlas Trades', 'Northwind Reno', 'Juniper Events'])
    await expect(page.getByRole('button', { name: title, exact: true })).toBeVisible();
  await expect(page.locator('[data-record-id="venture-ridgeview"]')).toHaveAttribute('data-health', /green|yellow|red|unknown/);
  await expect(page.getByRole('button', { name: 'Zoom In' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Zoom Out' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Fit View' })).toBeVisible();
  await expect(page.locator('.react-flow__minimap')).toBeVisible();
  await page.getByRole('button', { name: 'Ridgeview HOA', exact: true }).focus();
  await expect(page.getByRole('tooltip')).toContainText('Review the fictional delivery plan');
  const tooltip = await page.getByRole('tooltip').boundingBox();
  for (const id of ['venture-ridgeview', 'venture-acme', 'venture-cedar']) {
    const tile = await page.locator(`[data-record-id="${id}"]`).boundingBox();
    const separated = tooltip.y + tooltip.height <= tile.y || tile.y + tile.height <= tooltip.y
      || tooltip.x + tooltip.width <= tile.x || tile.x + tile.width <= tooltip.x;
    expect(separated, id).toBe(true);
  }
  await page.evaluate(() => document.fonts.ready);
  const viewport = page.locator('.react-flow__viewport');
  await expect.poll(async () => {
    const first = await viewport.evaluate(node => node.style.transform);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    return camerasClose(first, await viewport.evaluate(node => node.style.transform));
  }).toBe(true);
  const path = join(demo.vault, 'records/ventures/venture-acme.md');
  const original = await readFile(path, 'utf8');
  await writeFile(path, original.replace('title: Acme D2C', 'title: "Acme <img src=x onerror=alert(1)>"'));
  git(demo.vault, 'add', 'records/ventures/venture-acme.md');
  git(demo.vault, 'commit', '-qm', 'retitle fictional venture');
  const injected = page.getByRole('button', { name: 'Acme <img src=x onerror=alert(1)>', exact: true });
  await expect(injected).toBeVisible({ timeout: 12000 });
  await expect(page.locator('img')).toHaveCount(0);
  expect(errors).toEqual([]);
  await hidden(page);
});

test('venture zoom shows links, blocks a restricted record, and restores overview', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  await expect(page.getByRole('button', { name: 'Back to all' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true })).toHaveAttribute('data-health', 'red');
  await expect(page.getByText('BLOCKING', { exact: true }).first()).toBeVisible();
  await expect(page.locator('.react-flow__edge')).not.toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await page.goto(`${demo.origin}/#/v/venture-acme`);
  await hidden(page);
  const layout = await readFile(join(demo.vault, '.chassis/layout/reviewer.json'), 'utf8').catch(() => '');
  for (const secret of RESTRICTED) expect(layout).not.toContain(secret);
});

test('drag persists across reload and a live refresh keeps the camera still', async ({ page, demo }) => {
  await page.goto(demo.origin);
  const tile = page.locator('[data-record-id="venture-cedar"]');
  await expect(tile).toBeVisible();
  await page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT').catch(() => {});
  const box = await tile.boundingBox();
  const saved = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
  await page.mouse.move(box.x + 30, box.y + 30);
  await page.mouse.down();
  await page.mouse.move(box.x + 240, box.y + 180, { steps: 12 });
  await page.mouse.up();
  const response = await saved;
  const layout = await response.json();
  expect(layout.positions['venture-cedar']).toBeTruthy();
  const camera = await page.locator('.react-flow__viewport').evaluate(node => node.style.transform);
  expect(camera).toContain('translate');
  const path = join(demo.vault, 'records/ventures/venture-juniper.md');
  const original = await readFile(path, 'utf8');
  await writeFile(path, original.replace('title: Juniper Events', 'title: Juniper Events West'));
  git(demo.vault, 'add', 'records/ventures/venture-juniper.md');
  git(demo.vault, 'commit', '-qm', 'rename fictional venture');
  await expect(page.getByRole('button', { name: 'Juniper Events West', exact: true })).toBeVisible({ timeout: 12000 });
  expect(camerasClose(camera, await page.locator('.react-flow__viewport').evaluate(node => node.style.transform))).toBe(true);
  await page.reload();
  await expect(page.locator('[data-record-id="venture-cedar"]')).toBeVisible();
  const again = await page.evaluate(async () => (await fetch('/api/layout')).json());
  expect(again.positions['venture-cedar']).toEqual(layout.positions['venture-cedar']);
});

function edit(vault, token, id, version, changes) {
  const result = spawnSync(CLI, ['update', id, '--vault', vault, '--expected-version', String(version), '--changes', JSON.stringify(changes)], {
    encoding: 'utf8', env: { ...process.env, CHASSIS_AGENT_ID: 'canvas-editor', CHASSIS_AGENT_TOKEN: token,
      CHASSIS_AGENT_NAME: 'canvas-editor', CHASSIS_AGENT_EMAIL: 'canvas-editor@chassis.local' } });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
}

test('two undos of one card stay in version order', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  const card = page.getByRole('button', { name: 'Ridgeview HOA: launch review 3', exact: true });
  await expect(card).toBeVisible();
  const start = Number(git(demo.vault, 'rev-list', '--count', 'HEAD'));
  for (const step of ['First fictional step.', 'Second fictional step.']) {
    await card.dblclick();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByLabel('Next step').fill(step);
    const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
    const refreshed = page.waitForResponse(response => response.url().includes('/api/graph?venture=') && response.ok());
    await page.getByRole('button', { name: 'Save' }).click();
    expect((await saved).status()).toBe(200);
    await refreshed;
    await expect(page.getByRole('dialog')).toHaveCount(0);
  }
  for (let time = 0; time < 2; time += 1) {
    const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
    await page.getByRole('button', { name: 'Undo', exact: true }).click();
    expect((await saved).status()).toBe(200);
  }
  await expect.poll(() => Number(git(demo.vault, 'rev-list', '--count', 'HEAD'))).toBe(start + 4);
  await expect(page.getByText('nothing to undo')).toHaveCount(0);
  await expect(page.getByText('Your edit was not saved')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Undo', exact: true })).toBeDisabled();
});

test('gated edit, undo, conflict, and hidden controls', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  const blocked = page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true });
  await expect(blocked).toHaveAttribute('data-status', 'blocked');
  await blocked.dblclick();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Status').selectOption('in_progress');
  const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await page.getByRole('button', { name: 'Save' }).click();
  const response = await saved;
  expect(response.status(), await response.text()).toBe(200);
  await expect(blocked).toHaveAttribute('data-status', 'in_progress', { timeout: 10000 });
  expect(git(demo.vault, 'log', '-1', '--format=%an <%ae>')).toBe('canvas-editor <canvas-editor@chassis.local>');
  await page.getByRole('button', { name: 'Undo', exact: true }).click();
  await expect(blocked).toHaveAttribute('data-status', 'blocked', { timeout: 10000 });
  expect(git(demo.vault, 'log', '-2', '--format=%s')).toContain('update');
  await blocked.dblclick();
  await page.getByLabel('Title').fill('Ridgeview conflict attempt');
  edit(demo.vault, demo.credentials['canvas-editor'], 'task-ridgeview-launch-2', 3, { next_step: 'Updated from another terminal.' });
  const conflicted = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await page.getByRole('button', { name: 'Save' }).click();
  expect((await conflicted).status()).toBe(409);
  await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeVisible();
  await expect(page.getByLabel('Title')).toHaveValue('Ridgeview conflict attempt');
  await expect(page.getByRole('button', { name: 'Ridgeview conflict attempt' })).toHaveCount(0);
  await page.route('**/api/session', async route => {
    const response = await route.fetch();
    await route.fulfill({ json: { ...(await response.json()), writes_enabled: false } });
  });
  await page.reload();
  await expect(page.getByText('Read only · editing is off', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Edit', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Undo', exact: true })).toHaveCount(0);
});
