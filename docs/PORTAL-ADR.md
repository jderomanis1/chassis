# Portal ADR: local command canvas

Updated November 17, 2026 from [Joe's Step 7 authorization](STEP7-CANVAS-SCOPE.md).
The client selected one zoomable card canvas. This replaces the five-screen port
and ask flow. The dated original canvas ADR is preserved under
[reference/step7](reference/step7/PORTAL-ADR.md). Current work is on `step7-c1-write`;
main stays unchanged until independent SecOps review of C1/C2.

## 1. Stack and visual source

Runtime remains one local Python process. Starlette/uvicorn serve JSON and built
package assets. React 18.3.1, React DOM 18.3.1, React Flow MIT core 12.12.1, and
Vite 8.3.8 are pinned exactly with package-lock.json. Node 24.22.1/npm 11.9.0 are
for development only. Built output is committed under `src/chassis/portal/static/`.

The supplied source pack was hash-checked. Original prototype HTML/README and
review notes are preserved in `docs/reference/step7/`. Its colors, typography,
glow, tilt, hover cards, and pulse are the visual source. The five-screen code is
not the application. Exact tokens and contrast helper are in `frontend/design/`.
Generated tokens.css, the `chassis-theme` preference, and a local prepaint theme
script are implemented. Chakra Petch, IBM Plex Sans, and JetBrains Mono are
self-hosted from pinned Fontsource packages. There is no Google font CDN request.

The canvas now draws live venture tiles, a venture graph, hover cards, search,
and the gated editor from the portal APIs. Playwright has launched Chrome against
the built assets. See the current handoff for the commits and the remaining X1-X3
work. This does not change the strict CSP or approve a merge.

## 2. Local HTTP and the write gate

The server binds 127.0.0.1 or ::1. localhost normalizes to 127.0.0.1. Other hosts,
including the unspecified addresses, are refused. GET retains exact Host
and absent-or-exact Origin checks, configured viewer authentication, and private,
no-store responses. There are no CORS headers or browser-selected identities.
The strict CSP permits same-origin scripts/styles/fonts/connects, no unsafe-inline
or unsafe-eval, no objects, no framing, no base URL, and no form submissions.

Writes default off. `--allow-writes` requires CHASSIS_PORTAL_EDITOR_AGENT and
CHASSIS_PORTAL_EDITOR_TOKEN. The normal editor must be separately authenticated,
different from the viewer, and never chief-of-staff. Its credential stays server
side. The existing library rechecks credentials, write grants, and required normal
clearance under the vault lock. Explicit server-side identity determines Git author.

The shared write guard checks exact Host, mandatory exact Origin, mandatory
Sec-Fetch-Site same-origin, exact application/json, constant-time session-CSRF
comparison, actual request bytes capped at 64 KiB, body-free audit, and a 60/minute
launch budget. Default read-only GET-method refusals retain their earlier contract.
The browser alone uses this path; local automation continues to use CLI/MCP.

PATCH accepts only title (240 characters), status, next_step (4096), blocker_reason
(4096), due_at, depends_on, and expected_version. Unknown fields and invalid IDs
are refused; body and owner edits are not allowed. An existing target body above
64 KiB is refused, and library create and update refuse a new body above 64 KiB.
An update that omits `depends_on` leaves the stored list unchanged and does not
check it again, so a title or other unrelated edit can save while a hidden link
remains. When `depends_on` is sent, only ids that are not already stored are
checked. A new id the writer cannot read and a new id that does not exist both
return the same `invalid dependency` error, do not write, and do not include
the id. The stored list is the caller's visible ids followed by hidden ids that
were already stored, so the caller cannot delete a link they cannot see. Update
responses and later reads still omit hidden ids. `RecordStore.update_record`
remains the only record transaction. A success
returns id/version/commit, with one record-only commit by the editor. Stale updates
return 409/current_version with no commit; missing/hidden/ungranted IDs share 404.
Dirty edits retain the actionable `uncommitted human edit` message.

C1/C2 are implemented on the review branch but are not independently accepted.
Review all exception/recovery paths before SecOps signoff or merge. A middleware
audit failure after a successful record commit does not reset HEAD. That commit
is already durable; resetting it can delete a newer commit, and a failed reset
would hide `committed`, `commit`, and `current_version`. The response keeps those
facts and uses HTTP 500.

## 3. Visibility and layout

The library filters every projection using token, venture/type grants, clearance,
and hidden-parent rules. Hidden records, edges, counts, search hits, and health
inputs are absent. The future frontend must remove previously visible content
when access changes; that transition has no UI proof yet.

GET/PUT `/api/layout` uses positions, collapsed/hidden IDs, and viewport. State is
stored per viewer in ignored `.chassis/layout/<viewer>.json` through the existing
vault lock and atomic writer. Viewer/editor credentials are checked again under
the lock. IDs outside the library-visible set are dropped before save and return.
Missing/corrupt files return empty state. Coordinates and zoom are bounded and
finite; unsafe symlink paths fail closed. Layout never changes a record or Git.
A previously saved ID that later becomes hidden is filtered on read and removed
from disk on the next save. Direct filesystem access is outside API isolation.

## 4. Health

The existing pure health implementation is unchanged. Phoenix is the calendar.
Task priority: done, blocked, overdue, due within 3 days, activity older than
14 days, no signal, then on track. Visible unfinished dependencies add waiting_on
without changing color. Parent milestone overdue is red; due within 7 days is
at least yellow; the worst known active visible child wins. All active unknown
children yield unknown; completed children yield green. No children/milestone
yields unknown. Hidden children contribute no color or reason.

## 5. API contract

| Method and route | Response |
| :--- | :--- |
| GET `/api/session` | `{csrf,writes_enabled,viewer}`; per-launch CSRF in memory only |
| GET `/api/version` | `{etag}` over visible records/activity only |
| GET `/api/snapshot` | Visible venture cards with versions, health, milestones, counts, activity |
| GET `/api/ventures/{id}` | Visible venture and initiatives with versions, progress, GTM |
| GET `/api/initiatives/{id}` | Visible initiative/tasks with version, owner, status, next step, due date, blockers, dependencies, health |
| GET `/api/graph?venture=` | Renderer-neutral visible nodes/edges; no coordinates |
| GET `/api/search?q=` | Visible id/type/title hits |
| PATCH `/api/records/{id}` | `{record:{id,version},commit}` through the library transaction |
| GET/PUT `/api/layout` | `{positions,collapsed,hidden,viewport}` |

Errors retain `{error:{code,message}}`, with current_version on conflict and
available recovery metadata on committed library failures. Etags omit hidden
records, global HEAD, and unrelated files. The canvas polls `/api/version` every five seconds. A Playwright check saw a
committed title change without a camera jump. A stdio MCP status change recolored
the open task card. A stale PATCH shows the conflict text and reloads.

## 6. Verification and remaining gates

The separate demo generator remains 7 ventures, 14 initiatives, 42 tasks, one
restricted task, and separate reviewer/editor/chief credentials. Original source
fixtures and Python dependency files are unchanged. Actual HTTP checks serve all
21 compiled assets, exercise eight GET routes plus PATCH/PUT, and observe one
editor-attributed commit. This does not prove a canvas interaction.

The working tree passed 696 tests. Contrast, the production audit, and a second
production build stayed clean. Both-theme screenshots are in `evidence/step7-ui/`.
No independent Step 7 review verdict is inferred. X1-X3 remain unstarted.
Working demo: Monday, November 23 morning, America/Phoenix.
No ask/model, real data, Miro, gateway, hosting, deployment, or agent spawning.
