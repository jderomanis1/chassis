// The mode chip must follow the connection, at both widths.
import { test, expect } from './harness.mjs';

async function pair(page) {
  return page.evaluate(() => ({
    chip: (document.querySelector('.mode')?.innerText || '').replace(/\s+/g, ' ').trim(),
    status: (document.querySelector('.live')?.innerText || '').trim(),
  }));
}

async function sample(page, steps) {
  const bad = [];
  const before = await page.locator('.react-flow').boundingBox();
  for (let i = 0; i < steps; i += 1) {
    await page.clock.fastForward(100);
    const { chip, status } = await pair(page);
    const paused = status === 'Reconnecting' || status === 'Offline';
    if (paused && (chip === 'Editing enabled' || chip.startsWith('EDITING ENABLED'))) bad.push(status);
  }
  const after = await page.locator('.react-flow').boundingBox();
  return { bad, dy: Math.round(after.y - before.y) };
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 768, height: 1024 }]) {
  test(`the chip matches the connection at ${viewport.width}`, async ({ page, demo }) => {
    await page.setViewportSize(viewport);
    const theme = viewport.width === 1280 ? 'dark' : 'light';
    const text3 = theme === 'dark' ? 'rgb(125, 146, 169)' : 'rgb(79, 96, 119)';
    await page.emulateMedia({ reducedMotion: 'reduce', colorScheme: theme });
    await page.clock.install();
    await page.goto(`${demo.origin}/#/v/venture-juniper`);
    await expect(page.locator('.mode')).toHaveText('Editing enabled');
    await expect(page.getByText('Live store', { exact: true })).toBeVisible();
    await page.clock.fastForward(500);
    await expect(page.locator('.mode')).toHaveCSS('color', text3);
    await page.route('**/api/version', route => route.abort());
    const reconnecting = await sample(page, 50);
    await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible();
    await expect(page.getByText('EDITING PAUSED', { exact: true })).toBeVisible();
    await expect(page.locator('.mode')).toHaveCSS('color', text3);
    expect(reconnecting.bad).toEqual([]);
    expect(reconnecting.dy).toBe(0);
    const offline = await sample(page, 400);
    await expect(page.getByText('Offline', { exact: true })).toBeVisible();
    expect(offline.bad).toEqual([]);
    expect(offline.dy).toBe(0);
    await expect(page.locator('.mode')).toHaveCSS('color', text3);
    expect(await page.locator('.mode').evaluate(node => getComputedStyle(node).whiteSpace)).toBe('nowrap');
  });
}
