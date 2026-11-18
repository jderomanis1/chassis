import test from 'node:test';
import assert from 'node:assert/strict';
import { camerasClose } from '../src/camera.js';
import { POLL_MS, freshnessWorstCaseMs } from '../src/poll.js';
import { readVersion } from '../src/api.js';

test('a version poll stays under a 3 second worst case', () => {
  assert.equal(POLL_MS, 1000);
  assert.ok(freshnessWorstCaseMs() < 3000);
});

test('version checks send If-None-Match and treat 304 as unchanged', async () => {
  const original = globalThis.fetch;
  let seen;
  globalThis.fetch = async (path, options) => {
    seen = { path, ...options };
    return { status: 304, ok: false, json: async () => { throw new Error('no body'); } };
  };
  try {
    const result = await readVersion('abc123');
    assert.equal(seen.headers['If-None-Match'], '"abc123"');
    assert.deepEqual(result, { changed: false, etag: 'abc123' });
  } finally { globalThis.fetch = original; }
});

test('camera equality allows a fraction of a pixel', () => {
  assert.equal(camerasClose('translate(10px, 20px) scale(0.8)', 'translate(10.4px, 19.7px) scale(0.801)'), true);
  assert.equal(camerasClose('translate(10px, 20px) scale(0.8)', 'translate(18px, 20px) scale(0.8)'), false);
});
