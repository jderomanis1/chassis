// Notice, search hits, Show hidden, and Reload share one column. None may cover another.
import { spawnSync } from 'node:child_process';
import { test, expect, CLI } from './harness.mjs';

function edit(vault, token, id, version, changes) {
  const result = spawnSync(CLI, ['update', id, '--vault', vault, '--expected-version', String(version), '--changes', JSON.stringify(changes)], {
    encoding: 'utf8', env: { ...process.env, CHASSIS_AGENT_ID: 'canvas-editor', CHASSIS_AGENT_TOKEN: token,
      CHASSIS_AGENT_NAME: 'canvas-editor', CHASSIS_AGENT_EMAIL: 'canvas-editor@chassis.local' } });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
}

function overlaps(a, b) {
  return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('overlays stack without covering each other, and Show hidden survives a conflict', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const hidden = page.locator('[data-record-id="task-juniper-launch-3"]');
      const source = page.locator('[data-record-id="task-juniper-launch-2"]');
      await expect(hidden).toBeVisible();
      const hid = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
      await hidden.focus();
      await page.keyboard.press('h');
      expect((await hid).status()).toBe(200);
      await expect(hidden).toHaveCount(0);
      let release = () => {};
      const gate = new Promise(resolve => { release = resolve; });
      await page.route(/\/api\/(ventures|initiatives|graph)/, async route => { await gate; await route.continue(); });
      try {
        await source.dblclick();
        await page.getByLabel('Title').fill('Juniper fictional overlay title');
        edit(demo.vault, demo.credentials['canvas-editor'], 'task-juniper-launch-2', 1, { next_step: 'Updated from another terminal.' });
        await page.getByRole('button', { name: 'Save', exact: true }).click();
        await expect(page.locator('p.attn')).toContainText('Your edit was not saved');
        await page.getByLabel('Search records').fill('Juniper');
        await page.getByRole('button', { name: 'Search', exact: true }).click();
        const hits = page.locator('.hits li');
        await expect(hits).not.toHaveCount(0);
        const overlays = [page.locator('.attn'), page.locator('.hits'), page.locator('.show-hidden')];
        const boxes = [];
        for (const overlay of overlays) boxes.push(await overlay.boundingBox());
        expect(boxes.every(Boolean)).toBe(true);
        for (let i = 0; i < boxes.length; i += 1) {
          for (let j = i + 1; j < boxes.length; j += 1) expect(overlaps(boxes[i], boxes[j])).toBe(false);
        }
        const reload = page.getByRole('button', { name: 'Reload' });
        const reloadBox = await reload.boundingBox();
        await expect.poll(() => page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest('button')?.textContent || '', {
          x: reloadBox.x + reloadBox.width / 2, y: reloadBox.y + reloadBox.height / 2 })).toBe('Reload');
        const count = await hits.count();
        for (let index = 0; index < count; index += 1) {
          const box = await hits.nth(index).boundingBox();
          const owned = await page.evaluate(({ x, y }) => {
            const node = document.elementFromPoint(x, y);
            return Boolean(node?.closest('.hits li'));
          }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
          expect(owned).toBe(true);
        }
        const shown = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
        await page.getByRole('button', { name: 'Show hidden (1)' }).click();
        expect((await shown).status()).toBe(200);
        const graph = page.waitForResponse(response => response.url().includes('/api/graph'));
        release();
        await graph;
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await expect(hidden).toBeVisible();
        await expect(page.getByRole('button', { name: 'Reload' })).toBeVisible();
      } finally { release(); }
    });
  });
}
