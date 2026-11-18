// A restarted portal mints a new CSRF token. The next save must still land.
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { test, expect, CLI, ROOT } from './harness.mjs';

async function restartPortal(demo) {
  const { server, env, origin, vault } = demo;
  server.kill('SIGTERM');
  await new Promise(resolve => server.exitCode != null ? resolve() : server.once('exit', resolve));
  const port = new URL(origin).port;
  const next = spawn(CLI, ['portal', '--vault', vault, '--port', port, '--allow-writes'], {
    cwd: ROOT, env, stdio: ['ignore', 'ignore', 'pipe'],
  });
  let startup = '';
  next.stderr.on('data', part => { startup += part; });
  for (let attempt = 0; ; attempt += 1) {
    try { if ((await fetch(`${origin}/api/version`)).ok) break; } catch { /* process is still binding */ }
    if (attempt > 100 || next.exitCode != null) throw new Error(`Portal restart failed: ${startup}`);
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  return next;
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test('a restarted portal still accepts the next save', async ({ page, demo }) => {
      let restarted;
      try {
        await page.goto(`${demo.origin}/#/v/venture-juniper`);
        const card = page.locator('[data-record-id="task-juniper-launch-2"]');
        await expect(card).toBeVisible();
        await expect(page.getByText('Live store', { exact: true })).toBeVisible();
        restarted = await restartPortal(demo);
        await expect(page.getByText('Live store', { exact: true })).toBeVisible();
        await card.dblclick();
        await page.locator('#edit-title').fill('Juniper restart title');
        const saved = page.waitForResponse(response => response.url().includes('/api/records/') && response.request().method() === 'PATCH');
        await page.getByRole('button', { name: 'Save', exact: true }).click();
        expect((await saved).status()).toBe(200);
        const text = await readFile(join(demo.vault, 'records/tasks/task-juniper-launch-2.md'), 'utf8');
        expect(text).toContain('title: Juniper restart title');
      } finally {
        if (restarted && restarted.exitCode == null) {
          restarted.kill('SIGKILL');
          await Promise.race([
            new Promise(resolve => restarted.once('exit', resolve)),
            new Promise(resolve => setTimeout(resolve, 1000)),
          ]);
        }
      }
    });
  });
}
