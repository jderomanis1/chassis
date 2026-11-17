import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { api, ApiError } from '../src/api.js';

test('toolchain uses exact approved major versions', async () => {
  const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url)));
  for (const version of Object.values({ ...pkg.dependencies, ...pkg.devDependencies }))
    assert.match(version, /^\d+\.\d+\.\d+$/);
  assert.match(pkg.dependencies.react, /^18\./);
  assert.match(pkg.dependencies['@xyflow/react'], /^12\./);
});

test('API uses same-origin JSON, ephemeral CSRF, and the server error envelope', async () => {
  let seen;
  const original = globalThis.fetch;
  globalThis.fetch = async (path, options) => {
    seen = { path, ...options };
    return { ok: false, status: 409, json: async () => ({ error: {
      code: 'conflict', message: 'Changed elsewhere', current_version: 2 } }) };
  };
  try {
    await assert.rejects(api('/api/records/task-sample', { method: 'PATCH', csrf: 'ephemeral',
      data: { changes: { title: 'Sample' }, expected_version: 1 } }), error =>
      error instanceof ApiError && error.code === 'conflict' && error.current_version === 2);
    assert.equal(seen.credentials, 'same-origin');
    assert.equal(seen.headers['Content-Type'], 'application/json');
    assert.equal(seen.headers['X-Chassis-CSRF'], 'ephemeral');
    assert.equal(JSON.parse(seen.body).expected_version, 1);
  } finally { globalThis.fetch = original; }
});

test('network and invalid response failures remain actionable', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new Error('transport detail'); };
    await assert.rejects(api('/api/snapshot'), /Cannot reach the local canvas/);
    globalThis.fetch = async () => ({ ok: true, json: async () => { throw new Error('bad JSON'); } });
    await assert.rejects(api('/api/snapshot'), /Invalid response/);
  } finally { globalThis.fetch = original; }
});

test('generated themes preserve the approved tokens and no CDN', async () => {
  const tokens = JSON.parse(await readFile(new URL('../design/tokens.json', import.meta.url)));
  const css = await readFile(new URL('../src/tokens.css', import.meta.url), 'utf8');
  for (const theme of ['dark', 'light'])
    for (const [name, value] of Object.entries(tokens.themes[theme].color)) assert.ok(css.includes(`--${name}:${value}`));
  const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  assert.ok(html.includes('src="/theme.js"'));
  assert.doesNotMatch(html, /fonts\.google|https?:\/\//);
});
