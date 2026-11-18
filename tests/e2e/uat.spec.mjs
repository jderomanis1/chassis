import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { test, expect, git } from './harness.mjs';

test('a disk edit reaches the canvas in under 3 seconds', async ({ page, demo }) => {
  await page.goto(demo.origin);
  await expect(page.getByRole('button', { name: 'Cedar Rentals', exact: true })).toBeVisible();
  const path = join(demo.vault, 'records/ventures/venture-cedar.md');
  const original = await readFile(path, 'utf8');
  const started = Date.now();
  await writeFile(path, original.replace('title: Cedar Rentals', 'title: Cedar Rentals North'));
  git(demo.vault, 'add', 'records/ventures/venture-cedar.md');
  git(demo.vault, 'commit', '-qm', 'rename fictional venture');
  await expect(page.getByRole('button', { name: 'Cedar Rentals North', exact: true })).toBeVisible({ timeout: 3000 });
  expect(Date.now() - started).toBeLessThan(3000);
});

test('undo after reload is a second commit', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-acme`);
  const card = page.getByRole('button', { name: 'Acme D2C: launch review 1', exact: true });
  await expect(card).toBeVisible();
  const before = git(demo.vault, 'rev-parse', 'HEAD');
  await card.dblclick();
  await page.getByLabel('Title').fill('Acme fictional rename');
  const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await page.getByRole('button', { name: 'Save' }).click();
  expect((await saved).status()).toBe(200);
  const edited = git(demo.vault, 'rev-parse', 'HEAD');
  await page.reload();
  const undo = page.getByRole('button', { name: 'Undo', exact: true });
  await expect(undo).toBeEnabled();
  const undone = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await undo.click();
  expect((await undone).status()).toBe(200);
  await expect(card).toBeVisible();
  expect(git(demo.vault, 'rev-parse', 'HEAD^')).toBe(edited);
  expect(git(demo.vault, 'rev-list', '--count', `${before}..HEAD`)).toBe('2');
});

test('acme counts ignore the restricted task', async ({ page, demo }) => {
  await page.goto(demo.origin);
  const tile = page.locator('[data-record-id="venture-acme"]');
  await expect(tile).toContainText('2 initiatives · 5 tasks');
  await expect(tile).toHaveAttribute('data-task-count', '5');
  await page.goto(`${demo.origin}/#/v/venture-acme`);
  await expect(page.locator('[data-kind="task"]')).toHaveCount(5);
  await expect(page.getByTestId('command-canvas')).toHaveAttribute('data-task-count', '5');
  const body = await page.evaluate(async () => (await fetch('/api/ventures/venture-acme')).json());
  const total = body.initiatives.reduce((sum, initiative) => sum + initiative.progress.total, 0);
  expect(total).toBe(5);
  await expect(page.locator('body')).not.toContainText('Review the private fictional budget');
});

test('editor focus returns to the card and connectors are not tab stops', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  const card = page.locator('[data-record-id="task-ridgeview-launch-2"]');
  await card.dblclick();
  await expect(page.getByLabel('Title')).toBeFocused();
  await page.getByRole('button', { name: 'Close editor' }).click();
  await expect(card).toBeFocused();
  await card.dblclick();
  await page.getByLabel('Next step').fill('Fictional focus check.');
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(card).toBeFocused();
  const stops = await page.locator('.react-flow__handle, .react-flow, .react-flow__attribution, .react-flow__attribution a').evaluateAll(nodes => nodes.map(node => node.tabIndex));
  expect(stops.length).toBeGreaterThan(0);
  expect(stops.every(index => index < 0)).toBe(true);
  await card.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('Title')).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(card).toBeFocused();
  await card.focus();
  await page.keyboard.press('Enter');
  await page.getByLabel('Next step').fill('Fictional enter submit.');
  const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await page.getByLabel('Next step').press('Enter');
  expect((await saved).status()).toBe(200);
  await expect(card).toBeFocused();
  await page.evaluate(() => document.body.focus());
  const ring = await page.evaluate(() => getComputedStyle(document.body).outlineStyle);
  expect(ring).not.toBe('none');
});

test('primary controls are at least 44 pixels', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(demo.origin);
  for (const name of ['Zoom In', 'Zoom Out', 'Fit View', 'Search', 'Undo']) {
    const box = await page.getByRole('button', { name, exact: true }).first().boundingBox();
    expect(box.width, name).toBeGreaterThanOrEqual(44);
    expect(box.height, name).toBeGreaterThanOrEqual(44);
  }
  const theme = await page.getByRole('button', { name: /Theme:/ }).boundingBox();
  expect(theme.width).toBeGreaterThanOrEqual(44);
  expect(theme.height).toBeGreaterThanOrEqual(44);
  await page.locator('.skip').focus();
  const skip = await page.locator('.skip').boundingBox();
  expect(skip.width).toBeGreaterThanOrEqual(44);
  expect(skip.height).toBeGreaterThanOrEqual(44);
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  await page.locator('[data-record-id="task-ridgeview-launch-1"]').dblclick();
  for (const name of ['Close editor', 'Save']) {
    const box = await page.getByRole('button', { name, exact: true }).boundingBox();
    expect(box.width, name).toBeGreaterThanOrEqual(44);
    expect(box.height, name).toBeGreaterThanOrEqual(44);
  }
  await page.keyboard.press('Escape');
  for (const name of ['Edit', 'Back to all']) {
    const box = await page.getByRole('button', { name, exact: true }).first().boundingBox();
    expect(box.width, name).toBeGreaterThanOrEqual(44);
    expect(box.height, name).toBeGreaterThanOrEqual(44);
  }
});

async function overlaps(page) {
  const mini = await page.locator('.react-flow__minimap').boundingBox();
  const cards = page.locator('[data-record-id]');
  const count = await cards.count();
  for (let index = 0; index < count; index += 1) {
    const box = await cards.nth(index).boundingBox();
    const hit = box && mini && box.x < mini.x + mini.width - 2 && box.x + box.width > mini.x + 2
      && box.y < mini.y + mini.height - 2 && box.y + box.height > mini.y + 2;
    expect(hit, await cards.nth(index).getAttribute('data-record-id')).toBeFalsy();
  }
}

test('the minimap stays off the cards at 1280 and after zoom and resize', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await page.waitForTimeout(600);
  await overlaps(page);
  await page.getByRole('button', { name: 'Ridgeview HOA', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Back to all' })).toBeVisible();
  await page.waitForTimeout(600);
  await overlaps(page);
  await page.getByRole('button', { name: 'Back to all' }).click();
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await page.waitForTimeout(600);
  await overlaps(page);
  await page.setViewportSize({ width: 1100, height: 700 });
  await page.waitForTimeout(400);
  await overlaps(page);
});

test('a long unbroken title stays inside the card', async ({ page, demo }) => {
  const title = 'A'.repeat(80);
  const path = join(demo.vault, 'records/ventures/venture-cedar.md');
  const original = await readFile(path, 'utf8');
  await writeFile(path, original.replace('title: Cedar Rentals', `title: ${title}`));
  git(demo.vault, 'add', 'records/ventures/venture-cedar.md');
  git(demo.vault, 'commit', '-qm', 'lengthen fictional title');
  await page.goto(demo.origin);
  const heading = page.locator('[data-record-id="venture-cedar"] h3');
  await expect(heading).toHaveText(title);
  const inside = await heading.evaluate(node => node.scrollWidth <= node.clientWidth + 1);
  expect(inside).toBe(true);
});

test('a save during typing commits the full title once', async ({ page, demo }) => {
  await page.goto(`${demo.origin}/#/v/venture-acme`);
  const card = page.getByRole('button', { name: 'Acme D2C: launch review 1', exact: true });
  await card.dblclick();
  const input = page.getByLabel('Title');
  await input.fill('UA');
  const patches = [];
  page.on('response', response => {
    if (response.url().includes('/api/records/') && response.request().method() === 'PATCH') patches.push(response.status());
  });
  const before = Number(git(demo.vault, 'rev-list', '--count', 'HEAD'));
  const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await input.evaluate(node => {
    const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    set.call(node, 'UAT canvas title');
    node.addEventListener('input', () => {
      node.form.requestSubmit();
      node.form.requestSubmit();
    });
    node.dispatchEvent(new Event('input', { bubbles: true }));
  });
  expect((await saved).status()).toBe(200);
  await expect(page.getByRole('button', { name: 'UAT canvas title', exact: true })).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);
  expect(patches).toEqual([200]);
  expect(Number(git(demo.vault, 'rev-list', '--count', 'HEAD'))).toBe(before + 1);
  const text = await readFile(join(demo.vault, 'records/tasks/task-acme-launch-1.md'), 'utf8');
  expect(text).toContain('title: UAT canvas title');
  expect(text).not.toContain('title: UA\n');
});
