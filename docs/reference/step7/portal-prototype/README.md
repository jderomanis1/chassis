# Chassis portal: clickable vibe prototype

Look-and-feel prototype. Joe approved the look on 2026-11-16. This file plus `tokens.json` is the visual source of truth for the portal build. It is not portal code. No build step.

## Open
Open `index.html` in a browser (double-click, or `python3 -m http.server` in this folder and visit http://localhost:8000). Needs internet only for Google Fonts; falls back to system fonts offline.

URL parameters (put them before the `#`, e.g. `index.html?static&theme=light#/map`):
- `?static` freezes all motion, same as prefers-reduced-motion (used for screenshots).
- `?theme=light` or `?theme=dark` forces a theme for this page load only. It never writes localStorage.
- `?tilt=force` turns tile tilt on where the device reports no fine pointer (headless capture/testing only).

## Screens
1. Overview `#/`: summary strip, blocked alert, venture health tiles.
2. Venture `#/v/venture-ridgeview`, `#/v/venture-acme`: initiatives, progress, GTM stepper.
3. Initiative `#/i/<initiative-id>`: tasks with owner, status, depends-on. Click a row for the task panel; hover or focus a row for a hover card.
4. Dependency map `#/map`: tasks across both record ventures, depends_on edges, blocking edge in red, minimap. Drag to pan, scroll or +/- to zoom. Hover or focus a node to trace its chain. Click for detail.
5. Ask bar on every screen. Any question returns one canned answer, labeled "Example answer (prototype)".
Deep links: `#/?ask=...` opens the answer, `#/i/<id>?task=<task-id>` opens a task panel.

## Theme (light / dark)
- Toggle in the header (sun/moon button). Its accessible name states the current and next mode, e.g. "Theme: dark. Switch to light mode".
- The choice is saved in localStorage under `chassis-theme`.
- With nothing saved, it follows the OS `prefers-color-scheme` and updates live when the OS setting changes.
- A tiny inline script in `<head>` sets `data-theme` before first paint, so there is no flash.
- Both themes use the same CSS variable names: `:root[data-theme="dark"]` and `:root[data-theme="light"]`. `tokens.json` holds `themes.dark` and `themes.light` with hex values and computed contrast ratios.
- `python3 tools/contrast.py` recomputes every text/status pair and fails if any pair misses WCAG AA. Add `--write` to refresh `tokens.json`. Lowest pair: dark 5.11:1, light 4.74:1.

## Motion layer
Only transform, opacity and filter animate. Pointer tracking runs in requestAnimationFrame. will-change is set only on the tile being hovered. Under prefers-reduced-motion or `?static`, all of it is off and state changes are instant.
- Tiles tilt (up to about 6 degrees) and lift on hover, with a glow that follows the cursor. They settle smoothly on leave. Off for touch and coarse pointers.
- Progress bars grow in and counters count up on load and on every route change, staggered.
- Blocked pills pulse with a slow 2.6s glow ring.
- Map: hover or keyboard focus on a node lights its full upstream and downstream chain and dims the rest to 25%. Edges flow (moving dash), blocked edges flow in red.
- Page transitions use the View Transitions API. On drill-down the clicked tile or initiative card morphs into the page header. Where the API is missing, a crossfade/slide runs instead.
- Ask bar gets a focus glow ring. The answer shows a short "thinking" shimmer, then types in word by word with a shimmer sweep.
- Hover cards on task rows and map nodes show owner, due date, and blocker (any depends_on task that is not done). The records have no due-date field, so every card says "No due date set". The restricted task's card says only "Restricted record. Requires access."

## Keyboard
- Ctrl+K (Cmd+K on Mac): focus the ask bar.
- Esc: close the side panel or hover card.
- Tab through tiles, rows and map nodes; Enter or Space opens. Focusing a row or node also shows its hover card and, on the map, the chain highlight.
- Visible focus ring in both themes.

## Data
- Source: `/workspace/chassis-qe-s3/records/{ventures,initiatives,tasks}/*.md`, pulled from commit 9774ed4cbdca94f6a9724318b733a08cd9ff88f0 (see `/workspace/chassis-qe-s3/QE_SOURCE.txt`). It is not a git clone.
- Ridgeview HOA: 2 initiatives, 5 tasks, 2 depends_on edges. Acme D2C: 1 initiative, 3 tasks.
- One Acme task is `sensitivity: restricted`. It renders as "Restricted record" with a lock. Its id, title, owner and body are not in this file. Only its status and parent are used.
- Placeholders: the 5 tiles marked "Sample" are invented and have no drill-down. The "last activity" lines and the "Agent writes today" count are prototype values derived from record updated_at and version, not a real activity log.
- No client data, no emails.

## Files
- `index.html`: the prototype. Tokens are at the top of the style block, with computed contrast ratios for both themes.
- `tokens.json`: shared tokens plus `themes.dark` and `themes.light`.
- `tools/contrast.py`: contrast check.
- `tools/capture/*.mjs`: puppeteer-core scripts used for screenshots, the perf sample, the demo video and functional checks. They need `npm i puppeteer-core` and run against `/usr/bin/google-chrome`.
- `screens/`: 1440x900 headless Chrome captures (01-06 dark, 07-09 light, 10-14 hover and ask states), plus `wow-demo.mp4` and `wow-demo.gif`.
