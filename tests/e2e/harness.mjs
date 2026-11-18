import { test as base, expect } from '../../frontend/node_modules/@playwright/test/index.mjs';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:net';
import { setTimeout as delay } from 'node:timers/promises';

const ROOT = resolve(import.meta.dirname, '../..');
export const PYTHON = join(ROOT, '.venv/bin/python');
export const CLI = join(ROOT, '.venv/bin/chassis');
export { expect, ROOT };
export function git(root, ...args) {
  const r = spawnSync('git', ['-C', root, ...args], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error(r.stderr);
  return r.stdout.trim();
}
async function unusedPort() {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
export const test = base.extend({
  demo: async ({}, use) => {
    const parent = await mkdtemp(join(tmpdir(), 'chassis-canvas-'));
    const vault = join(parent, 'vault');
    const init = spawnSync(CLI, ['demo-init', vault], { cwd: ROOT, encoding: 'utf8' });
    if (init.status !== 0) throw new Error('Fictional demo initialization failed');
    const credentials = JSON.parse(init.stdout).credentials;
    const port = await unusedPort(), origin = `http://127.0.0.1:${port}`;
    const env = { ...process.env, CHASSIS_AGENT_TOKEN: credentials.reviewer,
      CHASSIS_PORTAL_VIEWER_AGENT: 'reviewer', CHASSIS_PORTAL_EDITOR_AGENT: 'canvas-editor',
      CHASSIS_PORTAL_EDITOR_TOKEN: credentials['canvas-editor'] };
    const server = spawn(CLI, ['portal', '--vault', vault, '--port', String(port), '--allow-writes'],
      { cwd: ROOT, env, stdio: ['ignore', 'ignore', 'pipe'] });
    let startup = '';
    server.stderr.on('data', part => { startup += part; });
    try {
      for (let attempt = 0; ; attempt++) {
        try { if ((await fetch(`${origin}/api/version`)).ok) break; } catch {}
        if (attempt > 100 || server.exitCode !== null) throw new Error(`Portal startup failed: ${startup}`);
        await delay(100);
      }
      await use({ vault, origin, credentials, env, server });
    } finally {
      if (server.exitCode === null) server.kill('SIGTERM');
      await Promise.race([
        new Promise(resolve => server.exitCode !== null ? resolve() : server.once('exit', resolve)),
        delay(2000),
      ]);
      await rm(parent, { recursive: true, force: true });
    }
  },
});
