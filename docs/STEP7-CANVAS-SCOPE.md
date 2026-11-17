# Step 7 authorization: command canvas

Source: Joe's build instructions supplied on 2026-11-17. This scope supersedes
the older P5-P8 dashboard plan. Read the handoff for implementation status.

Step 6 is closed on main at 523a8a5 (runtime checkpoint 7d152c5): S1-S6 read security, portal back end P1-P4, 576 / 499 / 542 tests, leak probe 0 matches. Independent Code Reviewer, QE and SecOps reviews of Step 6 are still owed and run in parallel with this step (see REVIEWS below). Start Step 7: the command CANVAS front end on the existing back end and static mount. Work from main at 523a8a5. Sample data only. Keep all tests green. Stop when Step 7 is done.

WHY THIS CHANGED (read first) The client (Andy) decided on 11/16: his primary interface is an agent-rendered, zoomable CARD CANVAS ("React Flow-class"): drag and rearrange, click to zoom, flick cards off view, edit in place, parent/child and card-to-card links, reconfigure by prompt ("zoom into a venture", "clear all but active"). Miro is now an optional export and its test is not load-bearing. No internet-facing gateway for the MVP. His named fail is "a beautiful static mockup", so every card must come from the live store through the API. Demo is Friday Nov 20.

This SUPERSEDES your handoff's NEXT (P5-P8 dashboard port) and parts of docs/PORTAL-ADR.md:

- KEEP from your P5-P8 plan: escape all record content (XSS), designed empty / loading / error states, Playwright tests, tokens.css from tokens.json, light/dark theme (same `chassis-theme` localStorage key and no-flash head script as the prototype), self-hosted fonts (no Google CDN), /api/version etag poll every 5 s, hover cards, keyboard access, prefers-reduced-motion.
- REPLACE: the five dashboard screens (overview, venture, initiative, map, ask) become ONE canvas with zoom levels. The approved prototype (portal-prototype/index.html + tokens.json) is the VISUAL source (colors, fonts, glow, tile tilt, hover cards, status pulse), not the code base.
- DEFER: P8 `POST /api/ask` and any model call. A deterministic command bar (stretch X2) takes its place.
- OVERRIDE "read-only portal": add ONE minimal, gated, local-only write path (C1) so edits on the canvas go through the existing library `update_record` (version check, lock, attributed commit). Flag it for SecOps.
- OVERRIDE "no npm" (ADR section 1): use a dev-time Vite build (below). Runtime stays one Python process.

LIBRARY CHOICE (decided) React 18 + @xyflow/react (React Flow v12, MIT core only, no Pro features), built with Vite. Commit the built output into src/chassis/portal/static/ so `chassis portal` needs no Node at runtime. Node/npm is dev and CI only: exact pinned versions, package-lock.json committed, `npm ci`, `npm audit --omit=dev` clean of high/critical, license list in docs. No CDN. Why not extend the prototype's vanilla map: it already has pan/zoom/minimap, but drag with persistence, node-internal editing, edge creation, animated fitView to a subtree, and selection would all be hand-built. React Flow gives those tested, and it is the exact class Andy named. Fallback: if React Flow integration is not rendering live tiles by end of Wed Nov 18 (AZ), stop and report; CoS will decide whether to fall back to the vanilla prototype map.

SOURCE NOTES (Joe will paste or attach): ANDY-CHECK-02.md, PORTAL-ADR.md, portal-prototype/README.md, tokens.json, screens/, CODEX_STEP6_REPORT.md.

PART C: back end, one commit each, tests first. Each increment <=150 LOC of new code, tests separate. C-1. SecOps should-fix items from the step 6 review (do these first, tests first, before C0): (a) Remove CHASSIS_PORTAL_ALLOW_REMOTE (src/chassis/portal/config.py:21-29). The portal binds 127.0.0.1 only. If remote bind is ever kept, it must require an explicit bearer and log a loud warning; default is remove. (b) Compute version_etag over visible records only, per viewer (src/chassis/portal/config.py:49-61), so edits to hidden records do not change what a viewer sees. Add a test: editing a restricted record leaves a normal viewer's etag unchanged. (c) Code Reviewer S3: tests/portal/conftest.py:7 imports conftest from itself, so the 46 portal tests do not collect in-tree. Move `issue` into tests/portal/helpers.py and confirm a single pytest run collects all \~579 tests. (d) Code Reviewer S1: the 4854431 leak fix is incomplete on the MCP side. IndexFileError still returns the absolute index path (reproduced via symlink). Map it to the generic internal_error as the portal does, and add a test asserting no absolute path appears in any MCP error. Acceptance: all four fixed with regression tests; one pytest run collects and passes the full suite.

C0. Contract additions for editing.

1. Add `version` to venture, initiative and task objects in /api/snapshot, /api/ventures/{id}, /api/initiatives/{id} and graph nodes.
2. Add `GET /api/session` returning `{csrf, writes_enabled, viewer}`. `csrf` is a per-process random token (secrets.token_urlsafe(32)), never logged, never written to disk.
3. Contract tests for every endpoint updated; the Step 6 leak grep still finds 0 hits. C1. Minimal local write endpoint. FLAG FOR SECOPS. It must meet SECOPS-STEP6.md section 4 in full: bind 127.0.0.1 with a Host allowlist; exact Origin match, reject a POST/PATCH with missing Origin, require Sec-Fetch-Site same-origin; CSRF token tied to a per-launch secret; application/json only, no CORS; identity from the S1-S5 seam, never the body, authz through the library; Pydantic field allowlists and size limits (including a record body size cap); etag/version concurrency plus id and path checks; restricted hide applies to canvas reads; audit and rate-limit every write; negative tests for cross-origin POST, form POST, wrong Host, and missing token. Implement these as one shared write guard (Host check in middleware before routing, exact same-origin Origin with missing Origin rejected, X-Chassis-CSRF header/token, JSON only, body cap, server-side identity, existing store transaction with expected_version), with a test for each rejection. In the canvas: render with textContent, sanitize any markdown, and ship a strict CSP. Do not merge to main until SecOps has reviewed this commit; push it on a branch `step7-c1-write` and continue the F increments against it.
4. `PATCH /api/records/{id}` with JSON `{changes, expected_version}`. It calls the same library `update_record` the MCP tool uses. No new persistence code.
5. Writes are OFF by default. Enabled only with `chassis portal --allow-writes`, which also requires CHASSIS_PORTAL_EDITOR_AGENT and CHASSIS_PORTAL_EDITOR_TOKEN in the environment. The editor is a separate policy agent (e.g. `canvas-editor`, clearance normal, write grants on the sample ventures only) proven through S5. Never the viewer token. Never `chief-of-staff`.
6. Every non-GET request must pass ALL of: loopback bind (unchanged), exact Host, Origin present and exactly `http://<bind>:<port>`, `Content-Type: application/json`, header `X-Chassis-CSRF` equal to the session token (constant-time compare), body <= 64 KiB. Anything else: 403 with the error envelope and no library call.
7. Field allowlist for `changes`: `title`, `status`, `next_step`, `blocker_reason`, `due_at` (plus `depends_on` only if X3 ships). Anything else: 400 validation, nothing written.
8. Stale `expected_version`: 409 `{error:{code:"conflict", message, current_version}}`, no file change, no commit.
9. Unknown id, hidden restricted id, or no write grant: 404 not_found, identical to a missing id. Audit records the outcome (body-free).
10. Simple rate limit: 60 writes per minute per process, then 429.
11. Tests: cross-origin, missing Origin, wrong Content-Type, missing or wrong CSRF, oversize body, disallowed field, writes disabled by default, stale version (no commit), hidden restricted id returns 404 with 0 leak hits, success creates exactly one record-only commit authored by the editor agent, then /api/version etag changes. C2. Layout store (positions are view state, not records).
12. `GET /api/layout` and `PUT /api/layout` with `{positions:{id:{x,y}}, collapsed:[ids], hidden:[ids], viewport:{x,y,zoom}}`. Same write gate as C1.
13. Stored per viewer at `.chassis/layout/<viewer>.json` (gitignored), written with `write_atomic` under the vault lock.
14. Ids not visible to the viewer are dropped silently on write and never returned. A layout file must never contain a restricted id written by a normal viewer (test it).
15. Missing or corrupt layout file returns an empty layout, not an error. C3. Demo vault, fictional only.
16. `chassis demo-init <dir>` creates a temporary git vault for the Friday demo with 7 fictional ventures (keep Ridgeview HOA and Acme D2C, add 5 more fictional ones, e.g. Cedar Rentals, Lumen Skincare, Atlas Trades, Northwind Reno, Juniper Events), 2-4 initiatives and 3-6 tasks each, a mix of done/in_progress/blocked/planned, a few depends_on edges including one cross-venture edge, one restricted task, and the agents for viewer, editor and chief-of-staff (token hashes generated locally, printed once, never committed).
17. It must not change the existing test fixtures or golden lists.
18. Every generated record passes `chassis validate`. No real names, emails, or client data.

PART F: canvas front end, one commit each, tests first (Playwright against `chassis portal` on the demo vault; plus unit tests for pure JS). Same <=150 LOC rule for hand-written code; built bundles and copied prototype CSS do not count. F1. Scaffold. `frontend/` (Vite + React + @xyflow/react), build to `src/chassis/portal/static/`. tokens.css generated from tokens.json. Theme toggle with accessible name. `api.js`: fetch with the error envelope, etag poll. Self-hosted fonts.

1. `chassis portal` serves the built canvas at `/`.
2. Loading state, empty state ("No ventures yet"), and error state (API down, 404, 500) each render and have a Playwright test.
3. Light and dark both pass the existing contrast check. F2. Overview canvas.
4. One tile per venture from /api/snapshot. Nothing hardcoded: a Playwright test edits a fixture title on disk, commits, and sees the tile change within 5 s.
5. Status colors from `health.color` (green / yellow / red / unknown) using prototype tokens. Blocked pulses.
6. Pan, scroll zoom, +/- buttons, fit to view, minimap.
7. Hover or focus a tile shows a hover card (next milestone, counts, last activity). All text inserted as text, never as HTML; an XSS test with `<img onerror>` in a title renders inert. F3. Zoom into a venture.
8. Click (or Enter) on a tile animates the viewport into that venture's initiatives and tasks, loaded from /api/ventures/{id}, /api/initiatives/{id} and /api/graph?venture=.
9. Parent/child edges, depends_on edges, blocking edges in red.
10. Esc or "Back to all" zooms out. Deep link `#/v/<id>` opens zoomed in.
11. Restricted items never appear for the normal viewer: no node, no edge, no count (Playwright DOM grep for the restricted id/title/owner finds 0). F4. Drag and persist.
12. Drag any card. On drop, PUT /api/layout (debounced).
13. Reload keeps positions. A live etag refresh keeps positions and does not jump the viewport.
14. New cards with no saved position get an automatic layout (dagre or elkjs, pinned version) and are not stacked. F5. Edit in place.
15. Double-click or Enter on a card opens inline edit for title, status, next_step, blocker_reason (required when status is blocked, matching the library rule), due_at.
16. Save sends PATCH with `expected_version`. Optimistic UI; on 409 roll back, refetch, and show "Changed elsewhere. Reloaded the latest." On 400 show the validation message inline.
17. Undo: Ctrl+Z / Cmd+Z and an Undo button revert the last 10 canvas edits by sending the prior values with the new version. Each undo is its own attributed commit. Label it "Undo" in the UI; do not git revert.
18. With writes disabled, edit controls are hidden and the session says so. No silent failure. F6. Live loop evidence.
19. A real stdio MCP client (chief-of-staff) updates a task status; the canvas card changes color within 5 s with no reload (headless check).
20. A canvas edit appears in `git log` with the editor agent as author and is readable over MCP.
21. Screenshots in both themes at 1440x900: overview, zoomed venture, hover card, edit in progress, conflict message.
22. evidence/acceptance.md gets a Step 7 section. Update CHASSIS_PROJECT_HANDOFF.md, README and docs/PORTAL-ADR.md to record the canvas pivot.

STRETCH (only after F1-F6 are green, in this order) X1. Flick off view: drag a card to the canvas edge or press H to hide it from this view (layout `hidden`), with a "Show hidden (n)" chip. Never deletes a record. X2. Command bar (precursor to voice). Ctrl/Cmd+K. Deterministic local parser, no model, no network beyond existing GET/PUT: `zoom into <venture>`, `show only blocked`, `show all`, `clear all but active`, `fit`, `back`. Fuzzy-match venture names. Unknown command shows the supported list. Unit tests per command. X3. Link cards: drag from a card handle to another to add `depends_on` through PATCH. Library validation must reject cycles and cross-type errors; show the message. Only task-to-task in this step.

CONSTRAINTS

- Sample and fictional data only. No real Andy data. No Miro, no gateway, no hosted anything, no Grok or any remote MCP connector, no model calls, no ask endpoint.
- Bind 127.0.0.1 only. No CORS headers. No secrets in code, git, tests, logs, screenshots, or the built bundle (grep the bundle for token patterns in a test).
- Restricted stays hidden end to end. The front end never relies on its own filtering.
- Do not weaken any Step 6 test or guard. GET routes keep their current Host/Origin rules.
- Tests first for every increment. Push each completed increment. Never force-push. Preserve history.
- Pin every new dependency. New Python deps: none expected.

FRIDAY DEMO SCRIPT (what Andy will see; also the Playwright acceptance walk-through `tests/e2e/demo.spec`)

1. `chassis demo-init /tmp/demo` then `chassis portal --allow-writes`. Canvas opens in dark mode on 7 venture tiles, colored by health.
2. Hover Acme D2C: card shows next milestone and counts. No trace of the restricted task.
3. Click Ridgeview HOA: the view zooms into its initiatives and tasks; the blocked task is red and its blocking edge glows.
4. Drag two cards into a new arrangement. Reload the page: the arrangement holds.
5. Double-click the blocked task, change status to in progress, save. The card turns green. Show `git log -1`: one commit by the editor agent.
6. Press Undo: the card goes back to blocked, with a second commit.
7. In a terminal, the chief-of-staff agent updates another task over MCP. Within 5 s the canvas card changes with no reload. That is read, write, render on one store.
8. Toggle light mode. Press Esc to zoom out to all 7.
9. (If X2 shipped) Ctrl+K: "show only blocked", then "zoom into Atlas Trades".

SCHEDULE TARGETS (America/Phoenix)

- Wed Nov 18 end of day: C0, C3, F1, F2, F3 pushed. C1 on its branch.
- Thu Nov 19 end of day: C1, C2, F4, F5, F6 pushed (C1 merged only after SecOps).
- Fri Nov 20 morning: stretch X1-X3 if green; otherwise stop and report.

REVIEWS (independent, owed, run in parallel, not by Codex)

- Step 6: Code Reviewer (384931f..523a8a5), QE fresh rerun of 576/499/542 and the leak probe, SecOps checkpoint 2 on S1-S6 and 4854431.
- Step 7: SecOps on C1 and C2 before merge; QE on F6 evidence; Code Reviewer per increment.

COMMITS Conventional message with scope, e.g. `feat(portal): add gated local record PATCH [Codex]`, `feat(canvas): venture tiles from live snapshot [Codex]`, `test(canvas): playwright demo walk-through [Codex]`. Include `Co-authored-by: Codex <codex@openai.com>`.

DONE WHEN

- Full suite green from a clean checkout with `uv sync --locked`, with and without extras; `npm ci && npm run build` reproduces the committed bundle byte for byte (or a documented, checked hash); Playwright suite green including the demo walk-through.
- Leak grep (API outputs, DOM snapshots, layout files, built bundle) finds 0 hits for the restricted record.
- Evidence and docs updated as in F6.
- Report: DELIVERED, VERIFIED (a table), RISKS-OPEN, NEXT, with commit links. Then stop.

QE Playwright acceptance criteria for the canvas (QE-STEP6.md; every one needs a test, QE reviews the tests):

1. XSS: title, owner, body, blocker, search results, and health text are escaped (render with textContent).
2. Empty, loading, and error states for every view.
3. Restricted records fully hidden in the UI (S2).
4. A stale-version conflict is shown to the user and nothing is overwritten.
5. Canvas writes go only through the library's update_record.
6. Unproven viewers are denied; a hidden record looks the same as a missing one.
7. Snapshot and drill-down show visible counts only.
8. Health is computed from visible children with 3/7/14-day thresholds.
9. The graph comes from /api/graph with no restricted edges.
10. Search comes from /api/search with no restricted hits.
11. Host and Origin rules enforced once the write endpoint exists. Also: extend the leak probe to catch a partial body sentence, not just a full planted body.

Independent review status at handoff (2026-11-17 AM AZ): Code Reviewer PASS WITH NITS; QE PASS; SecOps: GO on S1-S6 for the local back end with sample data only. NO-GO on real Andy data, on merging the canvas write route until the SecOps PR gate, and on any Grok-app bot (not approved, design review item). Also noted, not blocking this step: agent-token create runs unauthenticated; restricted files are plaintext on disk, in git, and in Obsidian.