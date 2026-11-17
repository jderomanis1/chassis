export class ApiError extends Error {
  constructor(status, error) { super(error.message || 'Request failed'); Object.assign(this, error, { status }); }
}
export async function api(path, { method = 'GET', data, csrf, signal } = {}) {
  let response, value;
  try {
    response = await fetch(path, { method, credentials: 'same-origin', cache: 'no-store', signal,
      headers: data === undefined ? {} : { 'Content-Type': 'application/json', 'X-Chassis-CSRF': csrf },
      body: data === undefined ? undefined : JSON.stringify(data) });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, { code: 'network', message: 'Cannot reach the local canvas. Check that Chassis is running.' });
  }
  try { value = await response.json(); } catch { throw new ApiError(response.status, { code: 'response', message: 'Invalid response from Chassis.' }); }
  if (!response.ok) throw new ApiError(response.status, value.error || { message: 'Request failed' });
  return value;
}
