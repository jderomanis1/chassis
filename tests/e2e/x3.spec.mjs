import { join } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { test, expect, ROOT, git } from './harness.mjs';

test('dragging between tasks links them and a cycle is shown', async ({ page, demo }) => {
  await mkdir(join(ROOT, 'evidence/step7-ui'), { recursive: true });
  await page.goto(`${demo.origin}/#/v/venture-ridgeview`);
  const dependent = page.locator('[data-record-id="task-ridgeview-operations-1"] .react-flow__handle-left');
  await expect(dependent).toBeVisible();
  await page.locator('[data-record-id="task-ridgeview-launch-1"] .react-flow__handle-right').dragTo(dependent);
  await expect.poll(() => git(demo.vault, 'log', '-1', '--format=%s')).toContain('task-ridgeview-operations-1');
  expect(git(demo.vault, 'log', '-1', '--format=%an <%ae>')).toBe('canvas-editor <canvas-editor@chassis.local>');
  const before = git(demo.vault, 'rev-parse', 'HEAD');
  await page.locator('[data-record-id="task-ridgeview-launch-2"] .react-flow__handle-right').dragTo(
    page.locator('[data-record-id="task-ridgeview-launch-1"] .react-flow__handle-left'));
  await expect(page.locator('.attn')).toContainText(/cycle|depend on itself|must be a task|already linked/);
  expect(git(demo.vault, 'rev-parse', 'HEAD')).toBe(before);
  await page.screenshot({ path: join(ROOT, 'evidence/step7-ui/dark-x3-link.png'), animations: 'disabled' });
  await page.getByRole('button', { name: /Switch to light/ }).click();
  await page.screenshot({ path: join(ROOT, 'evidence/step7-ui/light-x3-link.png'), animations: 'disabled' });
});
