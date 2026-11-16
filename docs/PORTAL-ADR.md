# PORTAL-ADR: Chassis command-center portal (read-only)
Solution Architect, 2026-11-16. Input: STATE.md, portal-prototype v2 (index.html + tokens.json, approved), library at step 4 (a26a093, read in /workspace/chassis-qe-s4). Step 5 (384931f) was not on the box when I wrote this, so function names below come from a26a093. Codex should confirm them at 384931f.

## 1. Stack
Options:
- A. FastAPI + Vite/React frontend. Rejected: it adds npm, a build step and a second dev server for 5 screens that already exist as vanilla JS.
- B. Server-rendered Jinja. Rejected: the map, the hover cards and View Transitions are client logic already, so we would end up maintaining both.
- **C. CHOSEN: one Python process.** Starlette + uvicorn serve a read-only JSON API over the existing library and also serve the static frontend. The frontend is a port of the prototype into plain ES modules with no bundler and no npm.

Why C: fewest moving parts, one port, one `uv sync`. It reuses `Index.list_records/get_record/search` and `graph.validate_graph`. Starlette over FastAPI: we already have Pydantic models and don't need OpenAPI.
New deps: `starlette`, `uvicorn` only. Tests use `starlette.testclient` (httpx, dev group).
Cost later: if Andy wants a hosted multi-user portal, this gets auth in front of it (see 2). That would not be a rewrite.

Layout:
```
src/chassis/portal/{app.py, api.py, redact.py, health.py, ask.py, config.py}
src/chassis/portal/static/{index.html, css/tokens.css, css/app.css, js/{main,api,router,theme,overview,venture,initiative,map,ask,hovercard}.js, fonts/}
tests/portal/{test_api.py, test_redact.py, test_health.py, test_ask.py, test_bind.py}
```
CLI: `chassis portal [--port 8765]`. Fonts are self-hosted from Fontsource (OFL), with no Google CDN.

## 2. Local vs deployable
The demo is **local-only**: the server binds `127.0.0.1` by default. A non-loopback `--host` is refused at startup unless `CHASSIS_PORTAL_ALLOW_REMOTE=1` is set, and that path is out of scope for the demo. Every route is GET except `POST /api/ask`, which has no write path. That POST requires an `Origin` that matches the host, which stops cross-site posts from other tabs.
Deployable later is a separate ADR with SecOps: Tailscale or Cloudflare Access in front, plus a viewer identity that maps to clearance. Nothing in this design blocks that.

## 3. Restricted masking: server side only
- There is one choke point: `redact.py` `redact(record, viewer) -> dict`. Every API response and the ask context go through it. No route serializes a raw record.
- The demo viewer has clearance `normal`, set in config and never taken from the request.
- A masked record serializes as `{id: "masked-<n>", type, parent, status, health.color, masked: true}` and nothing else. The `n` is stable within a snapshot. Title, owner, body, blocker_reason, due dates and the real id are never sent.
- Edges to a masked node use its `masked-<n>` id.
- Search drops restricted hits entirely, because otherwise a hit count would leak body matches.
- The health reason on a masked record is the code `restricted` only.
- Leak test: render every endpoint for the sample vault, then grep the bodies for the restricted record's id, title, owner and body strings. It must find 0 hits. This lives in `test_redact.py` and SecOps can re-run it.

## 4. Health rules (pure function, `health.py`)
`health(record, children, today) -> {color: green|yellow|red|unknown, reasons: [code]}`. `today` is injected: Phoenix local by default, frozen in tests. Thresholds are constants in `config.py`.

Task, first match wins:
1. `done`: green, `done`.
2. `blocked`: red, `blocked` (blocker_reason is shown unless masked).
3. Not done and `due_at < today`: red, `overdue`.
4. Not done and `due_at` within 3 days: yellow, `due_soon`.
5. Not done and `last_activity_at` older than 14 days: yellow, `stale`.
6. No `due_at` and no `last_activity_at`: unknown, `no_signal`.
7. Otherwise green, `on_track`.
Additionally, any `depends_on` that is not done adds the reason `waiting_on`. That reason does not change the color.

Initiative and venture:
1. Own `milestone_due_at < today` with the record not done: red, `milestone_overdue`.
2. Own milestone within 7 days: at least yellow, `milestone_soon`.
3. Roll-up is the worst of the children that are not done, ordered red > yellow > green. Unknown children are ignored unless all children are unknown, in which case the result is unknown.
4. No children and no milestone: unknown, `no_signal`.
Restricted children count toward the color but contribute only the reason `restricted`.

These are table tests with a frozen clock, one row per rule plus roll-up edge cases.

## 5. Ask bar
- The `Answerer` interface is `answer(question, snapshot) -> {text, sources[ids], mode}`. `snapshot` is the redacted read model only, and the answerer gets no write tools.
- **Default: `stub`.** A deterministic local answerer that routes on keywords (blocked, overdue, due, a venture name, a summary request) and answers from the snapshot, citing record ids. The UI labels it "Rules-based answer". This costs nothing and needs no key.
- **Optional: `model`.** An OpenAI-compatible HTTP adapter, so it stays model-agnostic. It is enabled only when `CHASSIS_ASK_PROVIDER`, `_BASE_URL`, `_MODEL` and `_API_KEY` are set in the server env. The key never reaches the browser.
- Caps for the `model` mode:
  - Question up to 500 characters.
  - Up to 600 output tokens.
  - 30 asks per day.
  - A daily spend cap of $1.00, estimated from tokens using `CHASSIS_ASK_PRICE_IN/OUT`.
  - Every call is logged to `.chassis/ask-ledger.jsonl`.
  - When a cap is hit, the endpoint falls back to the stub and says so.
- The snapshot is sent as data inside fences, with a system instruction to answer from the data only.
- Gate: `model` mode ships disabled. Enabling it needs AI Engineer review plus Joe's OK, because it spends money and sends data to a provider. It must never be enabled on real Andy data before the SecOps checkpoint.

## 6. Data contract (API v1, JSON)
- `GET /api/snapshot` returns `{etag, generated_at, ventures:[VentureCard]}`. VentureCard is `{id, title, health, next_milestone, milestone_due_at, counts:{initiatives, tasks, blocked, done}, last_activity_at}`.
- `GET /api/ventures/{id}` returns `{venture, initiatives:[{..., health, progress:{done,total}, gtm}]}`.
- `GET /api/initiatives/{id}` returns `{initiative, tasks:[{id, title, owner, status, due_at, blocker_reason, depends_on, health, last_activity_at, masked?}]}`.
- `GET /api/graph?venture=` returns `{nodes:[{id, type, parent, status, health, masked?}], edges:[{from, to, blocking}]}`. This is the neutral graph from C4, with no layout coordinates. Layout stays client-side as in the prototype.
- `GET /api/search?q=` returns `{hits:[{id, type, title}]}`, with restricted records excluded.
- `GET /api/version` returns `{etag}`. The etag is the git HEAD plus a hash of the working tree. The frontend polls it every 5 seconds and refetches only when it changes, so MCP writes show up live. The index rebuilds when the etag changes.
- `POST /api/ask` takes `{question}` and returns `{text, sources, mode, capped?}`.
- Errors are `{error: {code, message}}` with codes `not_found|validation|capped|internal`. There are no stack traces.

## 7. Increments (each 150 lines of new code or less, tests separate)
Ported prototype CSS and markup are copied verbatim and don't count toward the limit, but each port increment carries its own JS logic only.

| # | Increment | Depends |
|---|---|---|
| P1 | `portal/app.py` + `config.py` + `chassis portal` CLI, loopback bind guard, static mount, `/api/version`. Tests: bind refusal, version etag changes after a commit. | step 5 |
| P2 | `redact.py` + `/api/snapshot`, `/api/ventures/{id}`, `/api/initiatives/{id}`. Leak test across all endpoints. | P1 |
| P3 | `health.py` pure rules + table tests, wired into the P2 responses. | P2 |
| P4 | `/api/graph` + `/api/search` (redacted), error envelope. | P2 |
| P5 | Frontend A: `index.html` shell, `tokens.css` generated from tokens.json, `theme.js`, `api.js` (fetch + etag poll), `router.js`, overview. Self-hosted fonts. | P3 |
| P6 | Frontend B: venture + initiative + task panel + hover cards on live API. | P5, P4 |
| P7 | Frontend C: dependency map from `/api/graph`, chain highlight, pan/zoom. | P6 |
| P8 | `ask.py` Answerer + stub + `/api/ask` with Origin check and caps scaffold, ask bar wired. | P4, P5 |
| P9 | (gated) `model` adapter + ledger + cap tests with a mock HTTP provider. Ships disabled. | P8, AI Engineer + Joe |
| P10 | Live-loop evidence: an MCP write via the stdio client appears in the portal within 5 seconds (headless check), screenshots both themes, `evidence/acceptance.md`. | P7, P8 |

Parallel seams: P3 and P4 can run side by side after P2. P8 can run beside P6 and P7. The frontend works only against the section 6 contract.

## Risks/open
- Library names (`Index.list_records`, `get_record`, `search`, `validate_graph`) are verified at a26a093 only. Re-check at 384931f.
- Whether restricted status may show at all is still a SecOps question. I chose to show status and color only.
- The 3-day, 7-day and 14-day thresholds are my defaults and can change in config. Joe can tune them.
- The 5-second poll is fine on loopback. Swap in SSE if it is ever hosted.
- The prototype's "Agent writes today" needs a git-log count by agent author. Codex should add it in P2 from commit authors, or drop the tile. Do not fake it.
