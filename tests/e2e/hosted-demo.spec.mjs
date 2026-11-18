// Rehearse the deploy image with local TLS termination, as on Render.
import { execFileSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { connect } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:tls';
import { test, expect, ROOT } from './harness.mjs';

test('the demo image shares one vault across two browsers and the operator CLI', async ({ browser, playwright }) => {
  test.skip(!process.env.CI && !process.env.CHASSIS_TEST_DOCKER, 'Run with Docker available');
  test.setTimeout(480000);
  const temp = mkdtempSync(join(tmpdir(), 'chassis-tls-'));
  const tag = 'chassis-rehearsal:' + randomBytes(8).toString('hex');
  const password = randomBytes(32).toString('base64url');
  let tls, container, secondBrowser, upstreamPort;
  const docker = (...args) => execFileSync('docker', args, { cwd: ROOT, encoding: 'utf8',
    env: { ...process.env, DEMO_PASSWORD: password } }).trim();
  try {
    docker('build', '--quiet', '-f', 'deploy/Dockerfile', '-t', tag, '.');
    const key = join(temp, 'key.pem'), cert = join(temp, 'cert.pem');
    execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
      '-subj', '/CN=localhost', '-keyout', key, '-out', cert], { stdio: 'ignore' });
    tls = createServer({ key: readFileSync(key), cert: readFileSync(cert) }, client => {
      const upstream = connect(upstreamPort, '127.0.0.1');
      client.on('error', () => upstream.destroy());
      client.on('close', () => upstream.destroy());
      upstream.on('error', () => client.destroy());
      upstream.on('close', () => client.destroy());
      client.pipe(upstream).pipe(client);
    });
    await new Promise(resolve => tls.listen(0, '127.0.0.1', resolve));
    const origin = 'https://127.0.0.1:' + tls.address().port;
    container = docker('run', '-d', '-e', 'DEMO_PASSWORD', '-e', 'PUBLIC_ORIGIN=' + origin,
      '-e', 'PORT=10000', '-p', '127.0.0.1::10000', tag);
    upstreamPort = Number(docker('port', container, '10000/tcp').split(':').pop());
    const direct = await playwright.request.newContext({ ignoreHTTPSErrors: true });
    const basic = value => 'Basic ' + Buffer.from('demo:' + value).toString('base64');
    await expect.poll(async () => {
      try {
        return (await direct.get(origin + '/api/session', { headers: { authorization: basic('wrong') } })).status();
      } catch { return 0; }
    }, { timeout: 30000 }).toBe(401);
    secondBrowser = await playwright.chromium.launch({ executablePath: process.env.CHASSIS_CHROMIUM });
    const options = { ignoreHTTPSErrors: true, viewport: { width: 1440, height: 900 },
      httpCredentials: { username: 'demo', password, origin } };
    const pages = await Promise.all([browser, secondBrowser].map(async b =>
      (await b.newContext(options)).newPage()));
    const [editor, observer] = pages;
    const url = origin + '/#/v/venture-acme';
    const oldTitle = 'Acme D2C: launch review 1', title = 'Acme fictional review confirmed';
    for (const page of pages) {
      await page.goto(url);
      await expect(page.getByRole('button', { name: oldTitle, exact: true })).toBeVisible();
    }
    const navigation = await observer.evaluate(() => performance.timeOrigin);
    await editor.getByRole('button', { name: oldTitle, exact: true }).dblclick();
    await editor.getByLabel('Title', { exact: true }).fill(title);
    const saved = editor.waitForResponse(r => r.request().method() === 'PATCH');
    await editor.getByRole('button', { name: 'Save', exact: true }).click();
    expect((await saved).status()).toBe(200);
    await expect(observer.getByRole('button', { name: title, exact: true })).toBeVisible({ timeout: 15000 });
    expect(await observer.evaluate(() => performance.timeOrigin)).toBe(navigation);

    const git = (...args) => docker('exec', container, 'git', '-C', '/run/chassis-demo/current', ...args);
    const editorHead = git('rev-parse', 'HEAD');
    expect(git('log', '-1', '--format=%an <%ae>', '--name-only')).toContain('canvas-editor <canvas-editor@chassis.local>');
    expect(git('rev-list', '--count', 'HEAD')).toBe('2');
    const authorization = basic(password);
    const session = await direct.get(origin + '/api/session', { headers: { authorization } });
    const { csrf } = await session.json();
    const refused = await direct.patch(origin + '/api/records/task-acme-launch-1', {
      headers: { authorization, origin: 'https://elsewhere.invalid', 'sec-fetch-site': 'cross-site', 'x-chassis-csrf': csrf },
      data: { expected_version: 2, changes: { title: 'Wrong origin' } } });
    expect(refused.status()).toBe(403);
    expect(git('rev-parse', 'HEAD')).toBe(editorHead);
    const meeting = command => docker('exec', container, '/app/.venv/bin/python', '/app/deploy/meeting.py', command);
    expect(meeting('chief-write')).toContain('task-cedar-launch-2  v2');
    const history = meeting('history');
    expect(history).toContain('chief-of-staff <chief-of-staff@chassis.local>');
    expect(history).toContain('records/tasks/task-cedar-launch-2.md');
    expect(history).toContain('records/tasks/task-acme-launch-1.md');
    expect(history).toContain('Chassis Demo <demo@chassis.local>');
    expect(git('rev-list', '--count', 'HEAD')).toBe('3');
    await direct.dispose();
  } finally {
    if (secondBrowser) await secondBrowser.close();
    tls?.close();
    if (container) docker('rm', '-f', container);
    rmSync(temp, { recursive: true, force: true });
  }
});
