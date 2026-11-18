// A wide search must stay in the overlay column: capped, scrollable, and dismissible.
import { spawnSync } from 'node:child_process';
import { test, expect, CLI } from './harness.mjs';

function edit(vault, token, id, version, changes) {
  const result = spawnSync(CLI, ['update', id, '--vault', vault, '--expected-version', String(version), '--changes', JSON.stringify(changes)], {
    encoding: 'utf8', env: { ...process.env, CHASSIS_AGENT_ID: 'canvas-editor', CHASSIS_AGENT_TOKEN: token,
      CHASSIS_AGENT_NAME: 'canvas-editor', CHASSIS_AGENT_EMAIL: 'canvas-editor@chassis.local' } });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
}

function inside(box, size) {
  return box.x >= 0 && box.y >= 0 && box.x + box.width <= size.width + 1 && box.y + box.height <= size.height + 1;
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('sixty-two hits stay in view, scroll on their own, and dismiss', async ({ page, demo }) => {
      await page.goto(`${demo.origin}/#/v/venture-juniper`);
      const hidden = page.locator('[data-record-id="task-juniper-launch-3"]');
      const source = page.locator('[data-record-id="task-juniper-launch-2"]');
      const hid = page.waitForResponse(response => response.url().endsWith('/api/layout') && response.request().method() === 'PUT');
      await hidden.focus();
      await page.keyboard.press('h');
      expect((await hid).status()).toBe(200);
      await source.dblclick();
      await page.getByLabel('Title').fill('Juniper fictional hit list title');
      edit(demo.vault, demo.credentials['canvas-editor'], 'task-juniper-launch-2', 1, { next_step: 'Updated from another terminal.' });
      await page.getByRole('button', { name: 'Save', exact: true }).click();
      const reload = page.getByRole('button', { name: 'Reload' });
      const show = page.getByRole('button', { name: 'Show hidden (1)' });
      await expect(reload).toBeVisible();
      await page.getByLabel('Search records').fill('review');
      await page.getByRole('button', { name: 'Search', exact: true }).click();
      await expect(page.locator('.hits li')).toHaveCount(62);
      const size = page.viewportSize();
      for (const control of [reload, show]) {
        const box = await control.boundingBox();
        expect(inside(box, size)).toBe(true);
        const name = await control.innerText();
        const top = await page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest('button')?.textContent || '', {
          x: box.x + box.width / 2, y: box.y + box.height / 2 });
        expect(top).toContain(name.trim());
      }
      const list = page.locator('.hits');
      const metrics = await list.evaluate(node => ({ scroll: node.scrollHeight, client: node.clientHeight }));
      expect(metrics.scroll).toBeGreaterThan(metrics.client);
      const note = await page.locator('.hit-note').first().evaluate(node => {
        const css = getComputedStyle(node);
        return { border: css.borderTopWidth, background: css.backgroundColor };
      });
      expect(note.border).toBe('0px');
      expect(note.background).toBe('rgba(0, 0, 0, 0)');
      const before = await page.locator('.react-flow__viewport').evaluate(node => node.style.transform);
      const box = await list.boundingBox();
      await page.mouse.move(box.x + 24, box.y + 24);
      await page.mouse.wheel(0, 160);
      expect(await list.evaluate(node => node.scrollTop)).toBeGreaterThan(0);
      expect(await page.locator('.react-flow__viewport').evaluate(node => node.style.transform)).toBe(before);
      await expect(page.getByRole('button', { name: 'Close hits' })).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(list).toHaveCount(0);
      await reload.click();
      await expect(page.locator('p.attn')).toHaveCount(0);
    });
  });
}
