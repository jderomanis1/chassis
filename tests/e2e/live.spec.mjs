import { spawn } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { test, expect, PYTHON, ROOT, git } from './harness.mjs';

const RESTRICTED = ['task-launch-budget', 'Review the private fictional budget', 'Fictional Private Steward',
  'Fictional private budget planning note'];
const SHOTS = join(ROOT, 'evidence/step7-ui');

function mcpUpdate(vault, token, id, changes) {
  const child = spawn(PYTHON, ['-m', 'chassis.mcp_server', '--vault', vault], {
    stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, CHASSIS_AGENT_ID: 'chief-of-staff', CHASSIS_AGENT_TOKEN: token,
      CHASSIS_AGENT_NAME: 'chief-of-staff', CHASSIS_AGENT_EMAIL: 'chief-of-staff@chassis.local' } });
  let buffer = '', stderr = '';
  const pending = new Map();
  let sequence = 0;
  child.stderr.on('data', chunk => { stderr += chunk; });
  function send(method, params, note = false) {
    const message = { jsonrpc: '2.0', method };
    if (!note) message.id = ++sequence;
    if (params) message.params = params;
    child.stdin.write(`${JSON.stringify(message)}\n`);
    return message.id;
  }
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { child.kill('SIGKILL'); reject(new Error(`MCP timed out\n${stderr}`)); }, 45000);
    child.stdout.on('data', chunk => {
      buffer += chunk;
      const lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines.filter(Boolean)) {
        const message = JSON.parse(line);
        pending.get(message.id)?.(message);
      }
    });
    pending.set(send('initialize', { protocolVersion: '2025-11-25', capabilities: {},
      clientInfo: { name: 'chassis-canvas', version: '1' } }), () => {
      send('notifications/initialized', undefined, true);
      pending.set(send('tools/call', { name: 'update_record', arguments: { id, expected_version: 1, changes } }), message => {
        clearTimeout(timer); child.stdin.end();
        if (message.error) reject(new Error(JSON.stringify(message.error)));
        else resolve(message.result);
      });
    });
  });
}

async function shot(page, name) {
  await mkdir(SHOTS, { recursive: true });
  await page.screenshot({ path: join(SHOTS, name), animations: 'disabled' });
}

test('stdio MCP update reaches the canvas and both themes capture the demo states', async ({ page, demo }) => {
  test.setTimeout(60000);
  await page.goto(`${demo.origin}/#/v/venture-lumen`);
  const card = page.locator('[data-record-id="task-lumen-launch-2"]');
  await expect(card).toBeVisible();
  await expect(card).not.toHaveAttribute('data-health', 'red');
  const result = await mcpUpdate(demo.vault, demo.credentials['chief-of-staff'], 'task-lumen-launch-2',
    { status: 'blocked', blocker_reason: 'Waiting for a fictional supplier.' });
  const payload = result.structuredContent || JSON.parse(result.content[0].text);
  expect(payload.record.version).toBe(2);
  await expect(card).toHaveAttribute('data-health', 'red', { timeout: 12000 });
  expect(git(demo.vault, 'log', '-1', '--format=%an <%ae>')).toBe('chief-of-staff <chief-of-staff@chassis.local>');
  await page.getByRole('textbox', { name: 'Search records' }).fill('private fictional budget');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  const text = await page.locator('body').innerText();
  for (const secret of RESTRICTED) expect(text).not.toContain(secret);

  await page.goto(demo.origin);
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await expect.poll(async () => {
    const box = await page.locator('[data-record-id="venture-ridgeview"]').boundingBox();
    const pane = await page.locator('.react-flow').boundingBox();
    return Boolean(box && pane && box.y + box.height <= pane.y + pane.height + 1);
  }).toBe(true);
  await page.getByRole('button', { name: 'Acme D2C', exact: true }).focus();
  await expect(page.getByRole('tooltip')).toBeVisible();
  await shot(page, 'dark-overview-hover.png');
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  await expect(page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true })).toBeVisible();
  await shot(page, 'dark-venture.png');
  await page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true }).dblclick();
  await expect(page.getByRole('dialog')).toBeVisible();
  await shot(page, 'dark-edit.png');
  await page.getByLabel('Title').fill('Should not stick');
  await page.route('**/api/records/**', route => route.fulfill({ status: 409, json: { error: {
    code: 'conflict', message: 'This record changed before the save landed. Your edit was not saved. Reload to see the latest version.', current_version: 4 } } }));
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.locator('p.attn')).toContainText('Your edit was not saved');
  await expect(page.getByRole('button', { name: 'Reload' })).toBeVisible();
  await shot(page, 'dark-conflict.png');

  await page.unroute('**/api/records/**');
  await page.goto(`${demo.origin}/?theme=light`);
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await expect(page.locator('[data-kind="venture"]')).toHaveCount(7);
  await expect.poll(async () => {
    const box = await page.locator('[data-record-id="venture-ridgeview"]').boundingBox();
    const pane = await page.locator('.react-flow').boundingBox();
    return Boolean(box && pane && box.y + box.height <= pane.y + pane.height + 1);
  }).toBe(true);
  await page.getByRole('button', { name: 'Acme D2C', exact: true }).focus();
  await shot(page, 'light-overview-hover.png');
  await page.goto(`${demo.origin}/?theme=light#/v/venture-ridgeview`);
  await expect(page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true })).toBeVisible();
  await shot(page, 'light-venture.png');
  await page.getByRole('button', { name: 'Ridgeview HOA: launch review 2', exact: true }).dblclick();
  await shot(page, 'light-edit.png');
  await page.getByLabel('Title').fill('Should not stick');
  await page.route('**/api/records/**', route => route.fulfill({ status: 409, json: { error: {
    code: 'conflict', message: 'This record changed before the save landed. Your edit was not saved. Reload to see the latest version.', current_version: 4 } } }));
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.locator('p.attn')).toContainText('Your edit was not saved');
  await expect(page.getByRole('button', { name: 'Reload' })).toBeVisible();
  await shot(page, 'light-conflict.png');
});
