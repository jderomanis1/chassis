import test from 'node:test';
import assert from 'node:assert/strict';
import { api, bindSessionRefresh, bindWriteRetry, mergeSession } from '../src/api.js';

function json(body, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

test('a 403 is retried once when the record version is unchanged', { timeout: 2000 }, async () => {
  const writes = [];
  global.fetch = async (path, options = {}) => {
    const method = options.method || 'GET';
    const csrf = options.headers?.['X-Chassis-CSRF'];
    if (String(path).endsWith('/api/graph')) return json({ nodes: [{ id: 'task-a', version: 2 }] });
    if (method === 'PATCH') {
      writes.push(csrf);
      if (csrf === 'stale') return json({ error: { message: 'Write not permitted' } }, 403);
      return json({ record: { id: 'task-a', version: 3 } });
    }
    return json({});
  };
  bindSessionRefresh(async () => ({ csrf: 'fresh' }));
  bindWriteRetry(() => true);
  const result = await api('/api/records/task-a', { method: 'PATCH', csrf: 'stale', data: { expected_version: 2, changes: { title: 'x' } } });
  assert.deepEqual(writes, ['stale', 'fresh']);
  assert.equal(result.record.version, 3);
});

test('a 403 is not retried when the record version changed', async () => {
  const writes = [];
  global.fetch = async (path, options = {}) => {
    const method = options.method || 'GET';
    if (String(path).endsWith('/api/graph')) return json({ nodes: [{ id: 'task-a', version: 4 }] });
    if (method === 'PATCH') {
      writes.push(options.headers?.['X-Chassis-CSRF']);
      return json({ error: { message: 'Write not permitted' } }, 403);
    }
    return json({});
  };
  bindSessionRefresh(async () => ({ csrf: 'fresh' }));
  bindWriteRetry(() => true);
  await assert.rejects(
    () => api('/api/records/task-a', { method: 'PATCH', csrf: 'stale', data: { expected_version: 2, changes: { title: 'x' } } }),
    error => error.status === 409 && error.code === 'conflict');
  assert.deepEqual(writes, ['stale']);
});

test('a second 403 does not retry again', async () => {
  const writes = [];
  global.fetch = async (path, options = {}) => {
    const method = options.method || 'GET';
    if (String(path).endsWith('/api/graph')) return json({ nodes: [{ id: 'task-a', version: 2 }] });
    if (method === 'PATCH') {
      if (writes.length >= 2) throw new Error('retried more than once');
      writes.push(options.headers?.['X-Chassis-CSRF']);
      return json({ error: { message: 'Write not permitted' } }, 403);
    }
    return json({});
  };
  bindSessionRefresh(async () => ({ csrf: 'fresh' }));
  bindWriteRetry(() => true);
  await assert.rejects(
    () => api('/api/records/task-a', { method: 'PATCH', csrf: 'stale', data: { expected_version: 2, changes: { title: 'x' } } }),
    error => error.status === 403);
  assert.deepEqual(writes, ['stale', 'fresh']);
});

test('a session refresh keeps identity fields and replaces only the token', () => {
  const current = { csrf: 'old', writes_enabled: true, viewer: 'reviewer', editor: 'canvas-editor' };
  const next = mergeSession(current, { csrf: 'new', writes_enabled: false, viewer: 'someone-else' });
  assert.equal(next.csrf, 'new');
  assert.equal(next.writes_enabled, false);
  assert.equal(next.viewer, 'reviewer');
  assert.equal(next.editor, 'canvas-editor');
});

test('a 403 is not retried when the link drops before the retry', async () => {
  const writes = [];
  global.fetch = async (path, options = {}) => {
    const method = options.method || 'GET';
    if (String(path).endsWith('/api/graph')) return json({ nodes: [{ id: 'task-a', version: 2 }] });
    if (method === 'PATCH') {
      writes.push(options.headers?.['X-Chassis-CSRF']);
      return json({ error: { message: 'Write not permitted' } }, 403);
    }
    return json({});
  };
  bindSessionRefresh(async () => ({ csrf: 'fresh', writes_enabled: true, viewer: 'intruder' }));
  bindWriteRetry(() => false);
  await assert.rejects(
    () => api('/api/records/task-a', { method: 'PATCH', csrf: 'stale', data: { expected_version: 2, changes: { title: 'x' } } }),
    error => error.status === 403);
  assert.deepEqual(writes, ['stale']);
});
