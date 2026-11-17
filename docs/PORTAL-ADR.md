# Portal ADR: local command canvas

Updated 2026-11-17 from [Joe's Step 7 authorization](STEP7-CANVAS-SCOPE.md).
The client selected a zoomable card canvas on 2026-11-16. This supersedes the
original five-screen dashboard, vanilla-JS/no-npm choice, and stub ask endpoint.
The approved prototype remains the visual source. C-1, C0, and C3 are implemented;
C1/C2 and F1–F6 remain open. See the [handoff](../CHASSIS_PROJECT_HANDOFF.md).

## 1. Stack and visual source

Runtime remains one local Python process: Starlette and uvicorn serve JSON and
package-owned static assets. The authorized frontend is React 18 with React Flow
v12 (`@xyflow/react`, MIT core only) built by Vite. Node/npm is for development
and CI. Commit the built output under `src/chassis/portal/static/`; require exact
pins, package-lock.json, reproducible builds, a license list, and an npm audit
with no high/critical production-dependency findings.

The approved `portal-prototype/index.html`, `README.md`, `tokens.json`, and
`screens/` are required before F1. Preserve its colors, typography, glow, tile
tilt, hover cards, status pulse, theme key `chassis-theme`, and no-flash head
script. Generate tokens.css from the supplied JSON, self-host the fonts, honor
reduced motion, and retain keyboard access. These assets were not available at
this checkpoint. The static mount currently contains no built frontend.

## 2. Local HTTP and the write gate

The server binds only `127.0.0.1`; `localhost` is normalized to that address.
The previous `CHASSIS_PORTAL_ALLOW_REMOTE` bypass has been removed. Every GET
checks the exact configured Host, permits absent Origin or the matching local
Origin, rechecks the configured viewer, and returns private, no-store responses.
There is no CORS response and no browser-selected viewer or clearance.

C1 will add one record PATCH through the existing library `update_record`, and
C2 will add view layout. They are authorized but not implemented here. Read
`SECOPS-STEP6.md` section 4 before implementing them; that required source was
not supplied. Push C1 and dependent work to `step7-c1-write`. Independent SecOps
review of C1/C2 is required before any merge to main.

The shared planned write guard must enforce exact Host/Origin, mandatory Origin,
Sec-Fetch-Site same-origin, JSON only, constant-time session-CSRF comparison,
a 64 KiB body limit, server-selected proven editor identity, field allowlists,
record version checks, body-free audit, and 60 writes/minute/process. Writes are
off by default. The future `--allow-writes` option requires a separate normal
editor agent/token, never the viewer credential or chief-of-staff. Missing,
hidden, and ungranted targets share 404; stale versions return 409 without a
file change or commit. See the full C1 contract in the preserved scope.

## 3. Visibility

Library token, grant, and clearance checks govern every projection. Unauthorized
restricted rows, hidden-parent descendants, identifying edges, search hits, and
counts are absent. Hidden children cannot affect health. No masked placeholders
are emitted. Visible-to-restricted transitions must remove old frontend nodes
on refresh. Future layout storage must drop invisible IDs on write and read.

## 4. Health

The existing pure health implementation and frozen-clock tests remain unchanged.
Phoenix is the default calendar. Tasks use first-match priority: done, blocked,
overdue, due within 3 days, activity older than 14 days, no signal, then on track.
A visible unfinished dependency adds waiting_on without changing the color.
Parents use their own milestone date and visible children: overdue is red, a
milestone within 7 days is at least yellow, and the worst active known child
wins. All active unknown children yield unknown; all completed children yield
green. No children and no milestone yield unknown. Hidden children contribute
neither a color nor a reason. See [health.py](../src/chassis/portal/health.py).

## 5. Current API contract

| GET route | Response |
| :--- | :--- |
| `/api/session` | `{csrf, writes_enabled:false, viewer}`; fresh token per launch, memory only |
| `/api/version` | `{etag}`; SHA-256 over the configured viewer's visible records and derived activity |
| `/api/snapshot` | `{etag, generated_at, ventures}`; cards include id, title, version, health, milestone fields, visible counts, and last_activity_at |
| `/api/ventures/{id}` | Full visible venture and initiatives, including versions, health, progress, and GTM sections |
| `/api/initiatives/{id}` | Full visible initiative and task projections with id, title, version, owner, status, next_step, due_at, blocker_reason, depends_on, health, last_activity_at |
| `/api/graph?venture=` | Neutral nodes with id/type/parent/status/version/health and visible dependency edges; no coordinates |
| `/api/search?q=` | Visible hits with id/type/title |

The etag no longer includes global Git HEAD, hidden records, or unrelated files.
Snapshot reads retain concurrent-change retry behavior. The planned canvas polls
`/api/version` every five seconds and preserves layout/viewport during refresh.
Errors use `{error:{code,message}}`, with no internal paths or stack traces.
All current endpoints remain GET-only. CSRF is neither logged nor persisted;
evidence captures redact it after checking the in-memory response for leaks.

## 6. Canvas, layout, and demo

F1–F6 deliver one live canvas with venture overview, drill-down, hover details,
zoom/pan/minimap, drag persistence, inline editing, conflict recovery, and ten
versioned undo operations. All record content must render as escaped text; any
Markdown needs sanitization. A strict CSP, empty/loading/error states, and
Playwright checks are required. Every card must come from the live API.

C2 layout is per viewer in ignored `.chassis/layout/<viewer>.json`, protected by
the same write guard, vault lock, and atomic writer. It is view state, not a
record. Missing/corrupt files return empty layout. Invisible IDs never persist
or return. C2 is not implemented at this checkpoint.

C3 is implemented: `chassis demo-init <new-directory>` creates 7 ventures,
14 initiatives, 42 tasks, 29 dependencies, one restricted task, and separate
reviewer/editor/chief identities. Normal viewers see 62 records and 41 tasks.
Existing fixtures are unchanged. Tokens print once and only hashes persist.

## 7. Remaining gates

Obtain the prototype package, `SECOPS-STEP6.md`, `ANDY-CHECK-02.md`, and
`CODEX_STEP6_REPORT.md`. The embedded QE criteria are preserved in the scope;
provide the standalone `QE-STEP6.md` if it adds requirements. No new review
verdict is inferred from engineering tests.

C1/C2 require SecOps before merge; F6 requires the real MCP/canvas loop, both-theme
screenshots, reproducible bundle, zero API/DOM/layout/bundle leaks, and independent
QE review. None of those UI/build checks has run. X1 hiding, X2 deterministic
commands, and X3 task links are stretch work only after F1–F6 pass. No ask endpoint,
model call, Miro, hosted gateway, deployment, or real Andy data belongs here.
