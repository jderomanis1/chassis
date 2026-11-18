// A saved viewport zoom must not win over fit(). Test only.
import { test, expect } from './harness.mjs';

async function saveZoom(page, zoom) {
  const session = await page.evaluate(async () => (await fetch('/api/session')).json());
  const layout = await page.evaluate(async () => (await fetch('/api/layout')).json());
  layout.viewport = { x: layout.viewport?.x || 0, y: layout.viewport?.y || 0, zoom };
  const ok = await page.evaluate(async ({ csrf, body }) => {
    const response = await fetch('/api/layout', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Chassis-CSRF': csrf },
      body: JSON.stringify(body),
    });
    return response.ok;
  }, { csrf: session.csrf, body: layout });
  expect(ok).toBe(true);
}

async function fittedScale(page) {
  await page.evaluate(() => document.fonts.ready);
  let previous = null;
  let scale = 0;
  for (let i = 0; i < 30; i += 1) {
    scale = await page.locator('.react-flow__viewport').evaluate(node => {
      const raw = node.style.transform || getComputedStyle(node).transform;
      const match = /scale\(([^)]+)\)/.exec(raw);
      return match ? Number(match[1]) : new DOMMatrix(raw).a;
    });
    if (previous !== null && Math.abs(scale - previous) < 0.001) return scale;
    previous = scale;
    await page.waitForTimeout(40);
  }
  return scale;
}

test('saved zoom does not replace fit', async ({ page, demo }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  const scales = [];
  for (const zoom of [0.22, 1]) {
    await page.goto(demo.origin);
    await expect(page.locator('[data-kind="venture"]').first()).toBeVisible();
    await saveZoom(page, zoom);
    await page.goto(`${demo.origin}/#/v/venture-juniper`);
    await expect(page.locator('.react-flow__viewport')).toBeVisible();
    const scale = await fittedScale(page);
    scales.push(scale);
    expect(scale).toBeGreaterThanOrEqual(0.1);
    expect(scale).toBeLessThanOrEqual(0.9);
  }
  expect(Math.abs(scales[0] - scales[1])).toBeLessThanOrEqual(0.01);
});
