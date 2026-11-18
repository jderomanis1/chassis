// A 409 keeps the drawer and the typed values. Nothing is saved until Keep mine.
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { test, expect, CLI } from './harness.mjs';

function edit(vault, token, id, version, changes) {
  const result = spawnSync(CLI, ['update', id, '--vault', vault, '--expected-version', String(version), '--changes', JSON.stringify(changes)], {
    encoding: 'utf8', env: { ...process.env, CHASSIS_AGENT_ID: 'canvas-editor', CHASSIS_AGENT_TOKEN: token,
      CHASSIS_AGENT_NAME: 'canvas-editor', CHASSIS_AGENT_EMAIL: 'canvas-editor@chassis.local' } });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
}

async function openTask(page, demo) {
  await page.goto(`${demo.origin}/#/v/venture-juniper`);
  const card = page.locator('[data-record-id="task-juniper-launch-2"]');
  await expect(card).toBeVisible();
  await card.dblclick();
  await expect(page.getByRole('dialog')).toBeVisible();
  return card;
}

async function conflict(page, demo, title) {
  const typed = title || `Kept ${'title '.repeat(8)}`.slice(0, 200);
  await page.getByLabel('Title').fill(typed);
  edit(demo.vault, demo.credentials['canvas-editor'], 'task-juniper-launch-2', 1, { next_step: 'Updated from another terminal.' });
  const denied = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  expect((await denied).status()).toBe(409);
  await expect(page.locator('.conflict')).toHaveAttribute('role', 'alert');
  await expect(page.getByRole('button', { name: 'Keep mine and save again' })).toHaveClass(/btn/);
  await expect(page.getByRole('button', { name: 'Keep mine and save again' })).not.toHaveClass(/ghost/);
  await expect(page.getByRole('button', { name: 'Use latest' })).toHaveClass(/ghost/);
  await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeFocused();
  await expect(page.getByLabel('Title')).toHaveValue(typed);
  return typed;
}

async function settled(page) {
  await page.waitForTimeout(400);
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('a 409 keeps the typed title and Keep mine uses the latest version', async ({ page, demo }) => {
      await openTask(page, demo);
      const typed = await conflict(page, demo, 'A'.repeat(200));
      await expect(page.getByText('Latest: Updated from another terminal.')).toBeVisible();
      await expect(page.getByText(`Yours: ${typed}`)).toBeVisible();
      let patches = 0;
      page.on('request', request => {
        if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
      });
      const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
      await page.getByRole('button', { name: 'Keep mine and save again' }).click();
      const response = await saved;
      expect(response.status()).toBe(200);
      expect(JSON.parse(response.request().postData()).expected_version).toBe(2);
      await settled(page);
      expect(patches).toBe(1);
      const text = await readFile(join(demo.vault, 'records/tasks/task-juniper-launch-2.md'), 'utf8');
      expect(text).toContain('Updated from another terminal.');
      expect(text).toContain(`title: ${typed}`);
      await expect(page.getByRole('dialog')).toHaveCount(0);
    });

    test('Use latest sends no write and drops the typed title', async ({ page, demo }) => {
      await openTask(page, demo);
      const original = await page.getByLabel('Title').inputValue();
      await conflict(page, demo);
      let patches = 0;
      page.on('request', request => {
        if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
      });
      await page.getByRole('button', { name: 'Use latest' }).click();
      await expect(page.getByLabel('Title')).toHaveValue(original);
      await expect(page.getByLabel('Next step')).toHaveValue('Updated from another terminal.');
      await settled(page);
      expect(patches).toBe(0);
    });

    test('Escape after a 409 asks before discarding', async ({ page, demo }) => {
      await openTask(page, demo);
      await conflict(page, demo);
      await page.keyboard.press('Escape');
      await expect(page.getByText('Discard your changes?', { exact: true })).toBeVisible();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.getByRole('button', { name: 'Keep editing' }).click();
      await expect(page.getByText('Discard your changes?', { exact: true })).toHaveCount(0);
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.getByRole('button', { name: 'Close editor' }).click();
      await page.getByRole('button', { name: 'Discard' }).click();
      await expect(page.getByRole('dialog')).toHaveCount(0);
    });

    test('Escape closes an edit with no conflict at once', async ({ page, demo }) => {
      await openTask(page, demo);
      await page.locator('#edit-title').fill('Typed with no conflict');
      await page.keyboard.press('Escape');
      await expect(page.getByText('Discard your changes?', { exact: true })).toHaveCount(0);
      await expect(page.getByRole('dialog')).toHaveCount(0);
    });

    test('Save shows Saving and locks the fields until the response', async ({ page, demo }) => {
      await openTask(page, demo);
      await page.route('**/api/records/**', async route => {
        if (route.request().method() === 'PATCH') await new Promise(resolve => setTimeout(resolve, 600));
        await route.continue();
      });
      await page.getByLabel('Title').fill('Saving lock title');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      const saving = page.getByRole('button', { name: 'Saving...' });
      await expect(saving).toBeDisabled();
      await expect(page.locator('#edit-title')).toHaveJSProperty('readOnly', true);
      await expect(page.getByLabel('Status')).toBeDisabled();
      await expect(page.locator('input[name="next_step"]')).toHaveJSProperty('readOnly', true);
      await expect(page.getByRole('dialog')).toHaveCount(0);
    });

    test('only the conflict buttons look clickable', async ({ page, demo }) => {
      await openTask(page, demo);
      await conflict(page, demo);
      const panel = page.locator('.conflict');
      const cursors = await panel.locator('*').evaluateAll(nodes => nodes.filter(node => !['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(node.tagName))
        .map(node => getComputedStyle(node).cursor));
      expect(cursors.length).toBeGreaterThan(0);
      expect(cursors.every(cursor => cursor !== 'pointer')).toBe(true);
      for (const name of ['Keep mine and save again', 'Use latest']) {
        const box = await page.getByRole('button', { name }).boundingBox();
        expect(box.height).toBeGreaterThanOrEqual(44);
        expect(box.width).toBeGreaterThanOrEqual(44);
      }
    });

    test('Keep mine is not editable while the link is down', async ({ page, demo }) => {
      await page.clock.install();
      await openTask(page, demo);
      await page.route('**/api/records/**', route => route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
        code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) }));
      await page.getByLabel('Title').fill('Offline keep');
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeVisible();
      await page.route('**/api/version', route => route.abort());
      await page.clock.fastForward(4000);
      await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
      await page.clock.fastForward(40000);
      const keep = page.getByRole('button', { name: 'Keep mine and save again' });
      await expect(page.getByText('Offline', { exact: true })).toBeVisible();
      await expect(keep).toHaveAttribute('aria-disabled', 'true');
      await expect(keep).toHaveAttribute('title', 'Reconnect to edit');
      let patches = 0;
      page.on('request', request => {
        if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
      });
      await keep.click({ force: true });
      await settled(page);
      expect(patches).toBe(0);
      await expect(page.getByLabel('Title')).toHaveValue('Offline keep');
    });

    test('a refused retry with a changed version stays in the drawer', async ({ page, demo }) => {
      await openTask(page, demo);
      await page.getByLabel('Title').fill('Retry conflict title');
      await page.route('**/api/records/**', route => {
        if (route.request().method() === 'PATCH') return route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ error: { message: 'Write not permitted' } }) });
        return route.continue();
      });
      await page.route('**/api/graph**', route => route.fulfill({ json: { nodes: [{ id: 'task-juniper-launch-2', version: 9 }] } }));
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeVisible();
      await expect(page.getByLabel('Title')).toHaveValue('Retry conflict title');
    });
  });
}

test('a failed latest read does not blank the fields', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  const card = await openTask(page, demo);
  const status = await page.getByLabel('Status').inputValue();
  const title = await page.locator('#edit-title').inputValue();
  await page.locator('#edit-title').fill('Kept after a failed read');
  await page.route('**/api/records/**', route => {
    if (route.request().method() === 'PATCH') {
      return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
        code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) });
    }
    return route.continue();
  });
  await page.route('**/api/initiatives/**', route => route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: { message: 'unavailable' } }) }));
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText("Couldn't load the latest version")).toBeVisible();
  const blankLatest = await page.locator('.conflict').evaluate(node => [...node.querySelectorAll('p')].some(item => {
    const text = item.textContent || '';
    if (!text.includes('Latest:')) return false;
    return text.split('Yours:')[0].replace('Latest:', '').trim() === '';
  }));
  expect(blankLatest).toBe(false);
  let patches = 0;
  page.on('request', request => {
    if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
  });
  await page.getByRole('button', { name: 'Use latest' }).click();
  await settled(page);
  expect(patches).toBe(0);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(card).toContainText(title);
  await expect(card).toHaveAttribute('data-status', status);
});

test('Enter does not save while the discard prompt is open', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  const typed = await conflict(page, demo, 'Enter must not save');
  await page.locator('#edit-title').click();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('alertdialog', { name: 'Discard your changes?' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Keep editing' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('alertdialog')).toHaveCount(0);
  await expect(page.locator('#edit-title')).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('alertdialog')).toBeVisible();
  let patches = 0;
  page.on('request', request => {
    if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
  });
  await page.keyboard.press('Enter');
  await settled(page);
  expect(patches).toBe(0);
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('#edit-title')).toHaveValue(typed);
});

test('a hanging latest read does not stay on Saving', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  await page.locator('#edit-title').fill('Held through a hang');
  let release = () => {};
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/records/**', route => {
    if (route.request().method() === 'PATCH') {
      return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
        code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) });
    }
    return route.continue();
  });
  await page.route('**/api/initiatives/**', () => gate);
  try {
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByText("Couldn't load the latest version")).toBeVisible({ timeout: 8000 });
    await expect(page.getByRole('button', { name: 'Saving...' })).toHaveCount(0);
    await expect(page.locator('#edit-title')).toHaveValue('Held through a hang');
  } finally {
    release();
  }
});

test('Escape during a save does not drop a later conflict', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  let release = () => {};
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/records/**', async route => {
    if (route.request().method() !== 'PATCH') return route.continue();
    await gate;
    await route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
      code: 'conflict', message: 'This record changed before the save landed.', current_version: 4 } }) });
  });
  await page.locator('#edit-title').fill('Held during save');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Saving...' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toBeVisible();
  release();
  await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeVisible();
  await expect(page.locator('#edit-title')).toHaveValue('Held during save');
});

test('Save and Enter do not overwrite after a 409', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  const typed = await conflict(page, demo, 'Do not overwrite');
  let patches = 0;
  page.on('request', request => {
    if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
  });
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await page.waitForTimeout(400);
  expect(patches).toBe(0);
  await page.locator('#edit-title').press('Enter');
  await page.waitForTimeout(400);
  expect(patches).toBe(0);
  await expect(page.locator('#edit-title')).toHaveValue(typed);
  await expect(page.getByRole('heading', { name: 'Your edit was not saved' })).toBeVisible();
});

test('Keep mine is hidden when the latest version did not load', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  await page.locator('#edit-title').fill('No blind overwrite');
  await page.route('**/api/records/**', route => {
    if (route.request().method() === 'PATCH') {
      return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: {
        code: 'conflict', message: 'This record changed before the save landed.', current_version: 9 } }) });
    }
    return route.continue();
  });
  await page.route('**/api/initiatives/**', route => route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: { message: 'unavailable' } }) }));
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText("Couldn't load the latest version")).toBeVisible();
  await expect(page.getByRole('button', { name: 'Keep mine and save again' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Use latest' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close editor' })).toBeVisible();
  let patches = 0;
  page.on('request', request => {
    if (request.method() === 'PATCH' && request.url().includes('/api/records/')) patches += 1;
  });
  await page.locator('#edit-title').press('Enter');
  await settled(page);
  expect(patches).toBe(0);
  await expect(page.locator('#edit-title')).toHaveValue('No blind overwrite');
});

test('Use latest and Discard do nothing while Keep mine is saving', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  await conflict(page, demo, 'Held keep');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Discard' })).toBeVisible();
  let release = () => {};
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/records/**', async route => {
    if (route.request().method() !== 'PATCH') return route.continue();
    await gate;
    await route.fallback();
  });
  try {
    await page.getByRole('button', { name: 'Keep mine and save again' }).click();
    await expect(page.getByRole('button', { name: 'Saving...' })).toBeVisible();
    await page.getByRole('button', { name: 'Use latest' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.locator('#edit-title')).toHaveValue('Held keep');
    await expect(page.getByRole('button', { name: 'Discard' })).toBeVisible();
    await page.getByRole('button', { name: 'Discard' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Saving...' })).toBeVisible();
    await expect(page.locator('#edit-title')).toHaveValue('Held keep');
  } finally {
    release();
  }
});

test('a hung save ends in a failure and the drawer can close', async ({ page, demo }) => {
  test.setTimeout(30000);
  await page.setViewportSize({ width: 1280, height: 800 });
  await openTask(page, demo);
  await page.locator('#edit-title').fill('Hung save title');
  let patches = 0;
  await page.route('**/api/records/**', route => {
    if (route.request().method() !== 'PATCH') return route.continue();
    patches += 1;
    return new Promise(() => {});
  });
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Saving...' })).toBeVisible();
  await expect(page.locator('form.editor-form p[role="alert"]')).toBeVisible({ timeout: 15000 });
  await settled(page);
  expect(patches).toBe(1);
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Close editor' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Hung save title' })).toHaveCount(0);
});
