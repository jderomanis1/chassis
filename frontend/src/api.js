const CONFLICT = 'This record changed before the save landed. Your edit was not saved. Reload to see the latest version.';
let refreshSession = async () => null;
export function bindSessionRefresh(fn) { refreshSession = fn; }

export class ApiError extends Error {
  constructor(status, error) { super(error.message || 'Request failed'); Object.assign(this, error, { status }); }
}
async function perform(path, method, data, csrf, signal) {
  const response = await fetch(path, { method, credentials: 'same-origin', cache: 'no-store', signal,
    headers: data === undefined ? {} : { 'Content-Type': 'application/json', 'X-Chassis-CSRF': csrf },
    body: data === undefined ? undefined : JSON.stringify(data) });
  let value = null;
  try { value = await response.json(); } catch { value = null; }
  return { response, value };
}
export async function api(path, { method = 'GET', data, csrf, signal } = {}, retried = false) {
  let response, value;
  try {
    ({ response, value } = await perform(path, method, data, csrf, signal));
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, { code: 'network', message: 'Cannot reach the local canvas. Check that Chassis is running.' });
  }
  const error = value?.error || { message: response.ok ? '' : 'Request failed' };
  const denied = response.status === 403 && error.message === 'Write not permitted';
  if (denied && !retried && method !== 'GET') {
    const session = await refreshSession();
    if (session?.csrf) {
      const expected = data?.expected_version;
      if (Number.isInteger(expected)) {
        const id = decodeURIComponent(path.split('/').filter(Boolean).pop());
        const graph = await api('/api/graph');
        const node = (graph.nodes || []).find(item => item.id === id);
        if (!node || node.version !== expected) {
          throw new ApiError(409, { code: 'conflict', message: CONFLICT, current_version: node?.version });
        }
      }
      return api(path, { method, data, csrf: session.csrf, signal }, true);
    }
  }
  if (!response.ok) throw new ApiError(response.status, error);
  if (value == null) throw new ApiError(response.status, { code: 'response', message: 'Invalid response from Chassis.' });
  return value;
}

export async function readVersion(etag, signal) {
  let response;
  try {
    response = await fetch('/api/version', {
      method: 'GET', credentials: 'same-origin', cache: 'no-store', signal,
      headers: etag ? { 'If-None-Match': `"${etag}"` } : {},
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, { code: 'network', message: 'Cannot reach the local canvas. Check that Chassis is running.' });
  }
  if (response.status === 304) return { changed: false, etag };
  let value;
  try { value = await response.json(); }
  catch { throw new ApiError(response.status, { code: 'response', message: 'Invalid response from Chassis.' }); }
  if (!response.ok) throw new ApiError(response.status, value.error || { message: 'Request failed' });
  return { changed: value.etag !== etag, etag: value.etag };
}
