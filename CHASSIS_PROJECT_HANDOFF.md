# Chassis project handoff

**Checkpoint date: 2026-11-17. Step 7 F1-F6 and X1-X3 are on `cursor/step7-canvas-d0a6` (base `step7-c1-write` at `b54944d`). Main is still `42f0fa0`. C1/C2 are not merged and have no independent SecOps review.**
This file preserves the approved build decisions and evidence so each step can
continue in a separate chat. Read current repository HEAD before making changes.

## People, product, and purpose

Andy Patterson is the client and IP owner. Joe DeRomanis is leading the engagement.
**Chassis is the infrastructure. Homer is Andy's AI chief-of-staff agent persona.**
The current sample configuration uses agent ID `chief-of-staff`; no code rename
has been requested. Homer is intended to co-develop projects, not just summarize them.

Andy runs roughly seven parallel ventures and describes about 45 disconnected
AI chat threads plus siloed projects. He wants one agent that can read and write
across structured venture, initiative, and task state, with a zoomable visual view.
The access layer is the primary value. Joe's November 17 Step 7 instruction records
Andy's November 16 pivot to one zoomable card canvas over the same library and
neutral graph. Gated local edits and view layout are in scope. Miro is optional
export; the old five-screen dashboard and ask endpoint are superseded.

The broader engagement is paid discovery plus a working mock, with the full build
gated on the outcome. Its eventual demonstration on 1–2 real ventures is separate
from the approved **Increment 0: local execution and fictional data only**.
The Step 7 target is a fictional-data demo on Monday, November 23, 2026, morning
(America/Phoenix), replacing Friday, November 20. No price,
payment receipt, or full-build commercial approval is established by the supplied
references. Do not invent commercial commitments.

The broader discovery deliverables remain: a working mock on authorized real
ventures, a written store recommendation addressing concurrent human/agent
authorship, and an honest Miro write-fidelity assessment with a fallback if needed.
Andy reports a prior attempt removed text labels but left frames. That is client
context, not an observed API result from this build. The approved build order stays intact.

## Governing scope and sources

The approved Increment 0 architecture and C1–C7 below govern implementation.
The broader brief leaves the store open to recommendation; that earlier question
does not reopen the store choice already approved for this increment.
Current repository code and evidence establish what is implemented, not permission
to weaken a requirement. Resolve genuine contradictions with Joe before changing scope.

| Reference | What it contributes |
| :--- | :--- |
| Joe's approved build instructions and C1–C7 | Current scope, architecture, acceptance criteria, and delivery rules |
| `docs/STEP7-CANVAS-SCOPE.md` | Joe's complete Step 7 authorization, overrides, gates, and demo checks |
| `docs/PORTAL-ADR.md` | Updated canvas decision, API contract, unchanged health rules, and current limits |
| `evidence/SECOPS-CHECKPOINT-1.md` | Historical NO-GO at `384931f`; Step 6 implements its requested read controls, without granting real-data approval |
| Pasted Build Engagement brief | Business problem, discovery deliverables, ownership, future agent templates |
| `Re_ Chassis _ The build spec + Miro notes.msg`, 2026-11-16 | Andy emphasizes cross-project read/write and spatial navigation; Joe proposes plain files, optional Obsidian, search index, MCP, own-side layout, templates, and scoped access |
| `image(2).png` | Names Chassis as infrastructure and Homer as the chief-of-staff agent; provides the workshop/canvas reference |
| [Client Miro board](https://miro.com/app/board/uXjVENETjfI=/) | Reference board only; not designated scratch space or authorization to modify its existing items |

The screenshot shows example venture/work labels including HOA, Turns & Reno,
True Price Home Services, and Bodi Soap. These are context, not records to ingest.
The original attachments remain source artifacts; private email headers and
tokenized invitation/tracking links are not copied into the repository.

## Repository and implementation checkpoint

- Private repository: https://github.com/jderomanis1/chassis
- Published branch: `main`.
- Step 1 implementation baseline: `7274934ea722f1c6844f5b2bb24d539eb803b1ad`.
- Step 1's eleven development commits preserved the original repository commit.
- Migration commits `7773a87` and `f6b7ee6` added documentation only and remain
  preserved. Step 2 started from `f6b7ee6`; the uploaded handoff matched that state.
- Step 1 review fixes: `9f2dc28c369f66aa1ac9aaa3bbd910c57a83a463`, published
  separately before index work. S1 validates policy and known assigned agents;
  N1/N2 assert specific rejection causes and fields.
- Step 2 implementation: `39b5b2ee2efbdc272fdd33b479a4884c6b65cfc7`.
  Following commits document usage/findings (`28c0a57`) and evidence (`f0c6a82`).
  Inspect current HEAD and preserve all work; never reset to a remembered baseline.
- Step 3 started from accepted `main` at `f8856e757168cf55a1d522ada9077293b63d0be7`.
  The attached handoff was an older Step 1 snapshot; current repository evidence
  governed. Part A fixes were published separately as `cdc6532` before mutations.
- Step 3 implementation: `24ddcc790a228a822bb6b4b57829302116211811`.
  Documentation follows: usage/contracts `ba4aa1c`, acceptance proof `f7857c9`.
  Preserve all subsequent documentation and inspect current main before continuing.
- Fresh-checkout proof at the Step 3 implementation: `uv sync --locked`,
  **236 passing tests**, 13 valid records, and an installed CLI rebuild of 13 records.
  A separate temporary sample repo passed installed create/update/commit-human,
  stale/dirty refusal, attribution, record-only commits, and index checks.
  Earlier 72-test and 151-test baselines remain historical evidence.
- Joe accepted Step 3 at `9774ed4`: QE PASS, 236 tests, and a reported 20/20
  repeated real-process T1 races; Code Reviewer PASS WITH NITS. Step 4 started
  from that exact main. Its 236-test baseline was rerun successfully.
- Step 4 Part A fixes were published first, separately, as
  `9f0259917fedb3ed503e549e6da6975997497577`: Git flags, shared human hash/flag
  guard, authorization before body reads, and the explicit atomic replace assertion.
- Step 4 implementation: `176478a0ae56c718c2683fd5fb5f885a15554508`.
  Usage/contracts follow at `f035b6b`, the revised roadmap at `5cb6e6e`, and
  AC4 evidence/findings at `541abdf`. Preserve subsequent checkpoint documentation.
- Fresh-checkout Step 4 proof: `uv sync --locked`, **343 tests in 13.83s**,
  validation and rebuild of the original 13 records, and clean Git status.
  A separate installed CLI proof created an initiative and agent document with
  exactly one attributed commit each, refused writes as the new agent ID, and
  rebuilt all 15 temporary records after cache deletion. Original sample records,
  `agents.yaml`, dependency configuration, and lock remained unchanged.
- Implemented: strict schema, safe frontmatter parsing, body preservation,
  relationship/dependency and policy validation, fictional fixtures, the disposable
  SQLite index, automatic refresh/recovery, local reads, and versioned create/update
  with exact write grants, process locking, atomic writes, Git, and commit-human.
  Step 4 adds constrained templates, `create_from_template`, `chassis new`, and
  descriptive agent documents. Template creation uses the existing create transaction.
- `agents.yaml` has a strict Pydantic model. Only read/write scoped grants are
  allowed, policy ventures must exist, and unknown assignment IDs are rejected.
  Step 3 checks configured caller identity and old/new venture/type write grants.
- `src/chassis/graph.py` validates record relationships; it is not the future
  renderer-neutral JSON graph or layout planner.
- Joe accepted Step 4 at `a26a093`: QE PASS, 343 tests, Code Reviewer PASS WITH
  NITS. Step 5 began at that exact remote HEAD; its baseline was rerun successfully.
- Step 5 Part A: `c3cb10680a8853a8447ec3ba4df9dc427bcb7b7a`, separately pushed.
  Template owner/sensitivity/assignment reuse strict record constraints before
  expansion; FIXME/XXX and NFKC compatibility forms are rejected.
- Step 5 Part B: `42a80567a24cda55d4b19292800108851923e810`, separately pushed.
  Approved portal fields, blocker/date validation, schema-3 cache migration,
  filters, and derived Git activity are implemented. The only sample-record change
  is Ridgeview's blocker reason; `agents.yaml` is unchanged.
- Step 5 runtime/test checkpoint: `6ab3b14a759e1e3d5f8e9beae08bf8943b7c8d5d`.
  Prior increments are handlers `959f115`, stdio adapter `8faa3b0`, and real-session/
  refusal tests `3955eb6`. Connection docs/transcript follow at `b2fc347` and
  acceptance/findings at `ce52a0b`. Preserve subsequent handoff documentation.
- Fresh-checkout Step 5 proof: `uv sync --locked`, **431 tests in 29.94s**, all
  13 sample records validated/rebuilt, and empty Git status. Python 3.12.14 on Linux;
  official MCP SDK locked at 2.3.0. AC2 passed through actual stdio clients/processes.
  One client exercised all six tools and made exactly three attributed record-only
  commits. Two concurrent clients produced one winner/commit and one conflict.
- `evidence/mcp-session.jsonl` contains 25 actual protocol messages from the clean
  checkpoint. The capture test passed again in 1.56s. No environment secrets were
  recorded. Logs stayed on stderr; client closure ended processes and released locks.
- At the Step 5 checkpoint, the portal and health were pending. Joe subsequently
  approved the prototype and explicitly authorized Step 6's read security and P1–P4.
- Step 6 started from accepted `main` at `384931f23562bbf23b39451953874cb18d8df311`.
  Joe reported Code Reviewer PASS WITH NITS, QE PASS, 431 tests twice, and M9 20/20.
  Those review results are the accepted starting evidence, not a new Step 6 review.
- Required source notes were read before implementation. Joe's decision overrides
  the ADR's masking: unauthorized restricted records are absent from the library
  view, including rows, statuses, edges, counts, search, and health inputs.
- Step 6 commits, each published separately to private main: A `a02e37d`,
  S `f406487`, P1 `3ee59cb`, P2 `9a80d95`, P3 `82e4691`, P4 `bf270b3`.
  Final review found and fixed a hidden parser-cause leak in a separate security
  follow-up, `4854431`. P1's package static mount was completed in `7d152c5`,
  without frontend UI. Runtime/test checkpoint:
  **`7d152c51e8e123c860067e08e94e24c6bba5347f`**.
  Usage/architecture documentation is at `16192ab`; preserve later evidence
  and handoff commits and inspect current remote HEAD before new work.
- Three fresh detached checkouts passed locked installation and the full applicable
  suite: all extras **576 passed in 53.87s**; core only **499 passed, 8 optional
  modules skipped in 25.79s**; portal only **542 passed, 7 MCP modules skipped in
  29.43s**. The portal-only run has one development-only TestClient deprecation
  warning. Git status stayed empty and `uv.lock` unchanged in all three. A further
  `uv sync --locked --no-dev` passed core imports and missing-extra install messages
  with MCP, Starlette, uvicorn, anyio, httpx, and pytest all absent.
- A separate 47-test evidence run passed in 16.80s. Literal ripgrep over 25 captured
  CLI/MCP/portal output files found **0 matches** for restricted id/title/owner/body
  in raw or JSON-escaped form. No credentials or bodies enter the committed report.
- Normal sample viewers see 12 records, 7 tasks, and Acme progress total 2;
  restricted-clearance viewers with grants see 13 records and Acme task total 3.
  The restricted fixture's owner is now a unique fictional name for an unambiguous
  leak scan. No real data, frontend, ask endpoint, Miro call, or deployment was used.

## Step 7 canvas checkpoint: current

- Main remains `42f0fa00e521379bbcbeb2eaa36bf94b563ae3e8`. Do not merge C1/C2 or
  the canvas onto it before independent SecOps review.
- Continue from **`cursor/step7-canvas-d0a6`**, which starts at `step7-c1-write`
  `b54944d`. Canvas commits: font check `30d2ae5`, audit recovery `8033bf2`,
  layout-id cleanup `4f87fc3`, live canvas `60f91d1`. C1 guard remains `d3af932`,
  record PATCH `639d607`, layout store `1bcdf60`, and the earlier F1 scaffold
  `83b8d61`. Preserve this history.
- Playwright launched Chrome and the built portal. F1-F6 passed on a fictional
  `chassis demo-init` vault: seven tiles, zoom, drag persistence, gated edit,
  undo, conflict text, search, XSS, restricted-content absence, and a real stdio
  MCP status change that recoloured a card within the five-second poll.
  Screenshots are in `evidence/step7-ui/`. The working tree passed 696 tests.
  A second `npm run build` reproduced all 21 static files. Contrast stayed at
  0 failures. Production npm audit stayed at 0. This is not an independent review.
- X1 hide, X2 command bar, and X3 task links are implemented on this branch.
  Hover details are in a strip above the tiles. The camera fits once after fonts
  load. The venture arrangement is still a dagre graph, not the prototype lane
  drawing. Layout audit failure after a non-record write has no commit payload.

## Earlier Step 7 resume checkpoint

- Main was verified through connected GitHub at `42f0fa00e521379bbcbeb2eaa36bf94b563ae3e8`.
  It remains unchanged. All earlier runtime, evidence, and documentation commits
  are preserved. Native Git HTTPS authentication is unavailable; the connected
  GitHub API published each increment with an expected-parent check and no force.
  Remote tree and reconstructed commit hashes match the local Git objects.
- Work was on **`step7-c1-write`**, not main. C1 guard: `d3af932`; C1 record route:
  `639d607`; C2 layout: `1bcdf60`; partial F1/build checkpoint:
  **`83b8d61b06b7b6d04f44d1fcb42f13641b140f38`**. Preserve later docs commits.
- The supplied `step7-source-pack.zip` manifest and every listed hash were checked.
  Archive SHA-256: `dc36b4d0cfecd1e76f2d19663deca53c20192b75590792582fca8cabcc76e504`.
  The actual SecOps section 4, QE report, Andy direction, Step 6 report, canvas ADR,
  prototype HTML/README, tokens, screenshots, and capture/contrast helpers were read.
  The complete source pack is copied unchanged into `docs/reference/step7/`,
  including the original screenshots/media and capture helpers. Exact tokens and
  contrast script are also in `frontend/design/`. The reference prototype is not the app.
- C1: writes remain off by default. `--allow-writes` requires a separate proven
  normal editor and never uses the viewer credential or chief-of-staff. Shared
  guard checks local Host/Origin, mandatory same-origin fetch metadata, JSON,
  CSRF, 64 KiB request cap, audit, and 60 writes/minute. PATCH calls the existing
  library update transaction. Only title/status/next_step/blocker_reason/due_at
  are editable; body is not accepted. Existing target bodies above 64 KiB are
  refused. Explicit server-bound editor identity supplies Git attribution.
- C2: ignored per-viewer layout uses the existing vault lock and atomic writer.
  Credentials are rechecked under the lock. Invisible IDs are dropped before
  save and return. Missing/corrupt layout returns empty state; symlinks fail closed.
  A previously stored ID that becomes hidden is filtered on reads and removed
  from disk by the next layout save; direct disk access is outside API isolation.
- F1 is a **partial scaffold**, not a working canvas: exact React 18/React Flow v12/
  Vite pins, local fonts for the three approved families, generated themes, strict
  CSP-compatible prepaint script, API helper, theme toggle, and loading/empty/error
  shell. The compiled assets are committed. No venture tiles, drilldown, drag UI,
  edit UI, undo, search UI, or F6 live loop exists yet. F2-F6 and X1-X3 are unstarted.
- Four JavaScript checks pass. Both 64-pair theme contrast checks pass. `npm ci`
  plus build reproduces all 21 asset hashes. Production npm audit reports zero
  vulnerabilities; 30 production license entries and full notices are preserved.
- Chromium failed before page navigation: local Unix socket creation is denied
  (`socket() failed: Operation not permitted`). The execution policy automatically
  rejected elevated execution because sandbox approval requests are disabled.
  A safer Playwright headless-shell download also failed with an invalid/truncated
  archive. All five scaffold browser cases are BLOCKED, not passed. No screenshot,
  DOM leak, UI refresh, or MCP/canvas-loop verification is claimed.
- A real loopback HTTP smoke check used `chassis demo-init` for a separate 63-record
  vault, exercised eight GET routes plus PATCH/PUT, served all 21 static assets
  byte-identically, and observed one editor-authored record commit. Fourteen API/
  layout capture segments and the bundle had zero restricted-pattern matches;
  generated agent credentials were absent from assets. This is not browser proof.
- Final clean-install and leak results are in `evidence/step7-resume-verification.json`
  and the latest section of `evidence/acceptance.md`. Source fixtures, policy,
  pyproject.toml, and uv.lock remain unchanged from `523a8a5`.
- Stop reason is the genuine browser-execution/access blocker. No independent
  Step 7 SecOps, QE, or Code Reviewer verdict is claimed. C1/C2 cannot merge before
  independent SecOps review. Do not call Step 7 complete or demo-ready.

## Earlier Step 7 partial checkpoint: preserved history

- Start: verified current main 523a8a58b9a28c9d977d0512b14fc4b995ac5d21. The uploaded
  project handoff was an older Step 1 snapshot; this request and current repo govern.
- C-1: 45be7427780ed066cc47f9fbd200d51429cfc503. Bind override removed, viewer-only
  etags, unambiguous portal helpers, and generic MCP index errors. Eighteen checks
  failed first; one in-tree pytest run then passed 588 tests.
- C0: cb26ed926da7d670f1943c2128db55159f80097b. Session/version contracts and task
  next_step projection. Six checks failed first; all 50 portal tests passed.
- C3: 6e1ec10ced4688d98c40f9ec33661a17dbfcd9cd. demo-init creates 63 validated
  fictional records, three separate policy agents, and hashed local credentials.
  Four checks failed first; the full suite then passed 594 tests.
- Final test/evidence checkpoint: f297db302150cc2f991c84e97b0234ab2e9b0828. Partial
  body leak control, CSRF-safe evidence capture, and live demo API checks added.
  Clean installations passed 598 all-extras, 512 core, and 563 portal-only tests.
- Leak probe: 50 tests, 29 captured files / 198 output segments, zero literal
  matches for restricted id/title/owner/full body/partial body in raw or escaped form.
- Main contains no HTTP record-write route, layout store, frontend build, or
  Playwright evidence. Step 7 is incomplete. Required prototype/security sources
  were absent from main, available attachments, and the source search.
- Resume C1/C2/F1–F6 after those sources are supplied; the existing authorization
  remains valid. Keep the independent SecOps merge gate and fictional-data limit.

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md),
[acceptance evidence](evidence/acceptance.md), and [findings](FINDINGS.md).

## Approved architecture and record model

| Layer | Decision |
| :--- | :--- |
| Store | One Markdown file per record, YAML frontmatter, Git history; repository opens as an Obsidian vault, with no runtime dependency on Obsidian |
| Index | Disposable SQLite rebuilt from working-tree files, including uncommitted edits |
| Connector | Python 3.12, optional official MCP SDK, stdio; transport-agnostic handlers and no model-specific SDK dependency |
| MCP tools | `list_records(filters)`, `read_record(id)`, `search(query)`, `create_record(type, fields)`, `create_from_template(template, venture, fields)`, `update_record(id, changes, expected_version)` |
| Templates | `templates/initiative.md` and `templates/agent.md`; implemented in Step 4, AC4 passed |
| Graph/layout | Authorized neutral nodes/edges JSON exists; position and change planning remain later work |
| Portal | One local Python process; original seven GET routes plus layout GET; gated PATCH/PUT on the review branch |
| Canvas | React 18 + React Flow v12 + Vite canvas on the review branch; F1-F6 and X1-X3 exercised in Chrome |

Required fields: `id`, `type`, `title`, `status`, `owner`, `venture`, `parent`,
`next_step`, `updated_at`, `version`. Optional: `depends_on: []`,
`sensitivity: normal | restricted` (default normal), `assigned_agent` (default null).
Ventures/initiatives have optional `next_milestone` and `milestone_due_at`.
Tasks have optional `due_at` and `blocker_reason`; a blocked task requires a
nonempty reason, and other statuses require an empty/null reason. Dates are
strict ISO `YYYY-MM-DD`. Older records can omit optional fields, except legacy
blocked tasks must provide their reason. `last_activity_at` is derived in the
index from the latest touching commit's UTC committer timestamp, never stored
in source records. No history means null; uncommitted edits do not advance it.
Statuses: `planned`, `in_progress`, `blocked`, `done`. IDs and filenames are stable.
A venture references itself and has a null parent; initiatives parent to their
venture; tasks parent to an initiative in the same venture. An `agent` record is
a descriptive document parented to its venture. Dependencies may cross ventures
but cannot be missing, duplicated, self-referential, or cyclic.

`GTM_SECTIONS` fixes the exact ordered initiative headings: `Positioning`,
`Audience`, `Channels`, `Offer`, `Launch checklist`, `Success metrics`. Missing,
empty, markup-only, or placeholder sections are refused. The agent template takes
`Playbooks`, `Channels`, and `Data scope` and adds fixed read-only `Permissions`.
It neither registers a caller nor changes policy. Agent templates remain files;
no spawning is implemented or authorized in this build.

## C1–C7 implementation contracts

**C1, ownership and mapping:** Native tags on cards are approved. No visible
`chassis:` markers in frame titles or connector captions. Track
`render/miro/<board-id>.json` with IDs, fingerprints, format version, and operation
state only. Never store content, secrets, or full API payloads in the mapping.
Persist a pending entry before each create. Missing/mismatched mapped items stop
the run. Never adopt unmapped items. A create timeout without an item ID stays
unresolved; a fingerprint match cannot authorize adoption or a blind retry.

**C2, sensitivity and assignment:** Library reads hide unauthorized restricted
records, dependencies, and hidden-parent descendants completely. Restricted clearance
still requires a grant. Hidden children add no count, color, or reason. Assignment
is descriptive metadata. Future clients/exporters must remove previously visible
content after restriction; backend filtering alone does not erase an old board card.

**C3, permissions:** Reload/check policy and token hashes on every read/write and
under the lock. Grants are scoped by agent ID, venture, and type. Unknown/empty
agents, wrong/missing tokens, and invalid policy get no access. Clearance defaults
to normal. The server proves identity using CHASSIS_AGENT_TOKEN, not assignment.
Record tools cannot edit policy or provision credentials. These controls do not
restrict a process with direct filesystem/Git access.

**C4, neutral graph:** The planner emits renderer-neutral JSON. No Miro runtime
types above `src/chassis/render/miro/`. A future portal consumes the same graph.

**C5, transport:** Tool handlers are independent of MCP transport. Stdio only now.

**C6, human edits and concurrency:** Refuse dirty target writes, naming the file
and saying exactly `uncommitted human edit`. Step 3 supplies `chassis commit-human <path>`
using `CHASSIS_HUMAN_NAME` / `CHASSIS_HUMAN_EMAIL`. Reread and compare
`expected_version` under an interprocess lock; a stale update makes no file change
or commit. A successful update bumps version and creates a record-only commit
attributed to the agent. Ordinary editors do not honor the lock; Joe's client
email describes concurrent collaboration as a goal, not proof of unrestricted safe editing.

**C7, delivery:** Tests first, roughly 150-line increments, push each completed
increment to the private repo, preserve existing work/history, never force-push.
Keep `.env` ignored and secrets in environment variables. Report each increment
as **DELIVERED / VERIFIED / RISKS-OPEN / NEXT**.

## Sample data and acceptance status

| Fictional venture | Initiatives | Tasks | Dependency edges |
| :--- | ---: | ---: | ---: |
| Ridgeview HOA | 2 | 5 | 2 |
| Acme D2C | 1 | 3 | 0 |

The table is the complete fixture inventory. A normal viewer sees only 2 Acme
tasks; the restricted task contributes nothing to visible totals or health.
All Ridgeview records are normal. A Ridgeview render
should contain one venture frame, seven cards, and two dependency connectors.

| AC | Required evidence | Current status |
| :--- | :--- | :--- |
| 1 | Obsidian opens cleanly; every record validates | Schema/relationships pass; actual Obsidian UI check pending after a desktop launch problem |
| 2 | Real MCP client lists, reads, creates, updates | Passed Step 5 at `6ab3b14`: all six tools, three attributed commits, structured refusals, two-client race, clean protocol/shutdown, real transcript |
| 3 | Stale rejection; good version bump and attributed Git commit | Passed Step 3 at `24ddcc7`: two real processes, one winner/commit, structured conflict, and agent attribution |
| 4 | Initiative created from template with filled go-to-market sections | Passed Step 4 at `176478a`: six filled sections, one attributed commit, library and installed CLI proof |
| 5 | Scratch Miro frame, contained cards, colors, connectors | Pending live verification |
| 6 | MCP status change updates exactly one existing card | Pending live verification |
| 7 | Repeat render produces zero mutating Miro API calls | Pending live verification |
| 8 | Delete scratch frame; query child IDs; record actual survival | Not run; outcome unknown |
| 9 | Delete/rebuild SQLite; identical query results | Passed Step 2: 15 library queries and six CLI outputs are byte-identical |

Never delete groups. Update board items in place. Keep status out of layout/order
and parent rollups so a status change affects only that task. Bulk create is at
most 20 supported items; connectors are separate. Respect rate limits. Stop and
report unexpected API behavior. A supplied board link is not a token or scratch designation.
The token comes from the environment with only `boards:read` and `boards:write`.
Live business-account writes are out of scope; explicitly designated scratch Miro
operations are the authorized exception needed for this proof.

## Build order and one-chat workflow

| Step | Scope | State |
| :--- | :--- | :--- |
| 1 | Skeleton, schema, parser, relationships, sample records | Implemented; Obsidian demo gap remains |
| 2 | Disposable SQLite index and working-tree queries | Complete; AC9 passed |
| 3 | Create/update, policy enforcement, concurrency, Git, commit-human | Complete; AC3 passed |
| 4 | Initiative and agent templates | Complete; AC4 passed |
| 5 | MCP tools and real stdio client integration | Complete; AC2 passed |
| 6 | Read security and portal backend P1–P4 | Complete; Joe reports local/sample-only review GO |
| 7 | Live command canvas, gated edits, and per-viewer layout | F1-F6 and X1-X3 implemented on the review branch; C1/C2 still need independent SecOps review before main |
| 8 | Optional Miro export, including scratch contract/deletion probe before adapter and live proofs | Optional; existing C1–C7 still apply |
| 9 | Chat import as its own separately scoped step | Later |

The authorized canvas uses live venture tiles, drill-down, hover cards, dragging,
inline edits, conflict recovery, and undo. React Flow replaces the five dashboard
screens. No ask endpoint or model call is in Step 7. The optional deterministic
command bar is X2, after F1–F6 pass. Use the complete preserved Step 7 scope.

`read_model.neutral_graph()` and `RecordIndex.graph()` remain renderer-neutral.
C2 layout coordinates are view state, stored per viewer outside records and Git.
Keep library visibility before graph emission. Any optional Miro work still
requires the original ownership/reconciliation contracts and separate scope.

Joe approved and Step 5 implemented `next_milestone`, `milestone_due_at`, task
`due_at`/`blocker_reason`, and derived `last_activity_at`. Existing `status`, `owner`,
`next_step`, `parent`, and `depends_on` support basic summaries and drilldown.
The ADR's pure health rules are implemented with 3/7/14-day constants and an
injected Phoenix date; hidden children are excluded. Human commits preserve `updated_at`; the derived Git
timestamp includes them. Uncommitted edits remain readable but do not advance
committed activity. Preserve the approved health rules during the frontend port.

Step 2 indexes authoritative working-tree Markdown, including uncommitted edits.
`RecordIndex(root, agent=None, token=None)` exposes `list_records(filters)`,
`get_record(id)` / `read_record(id)`, `search(query)`, `graph()`, and `rebuild()`.
CLI commands are `chassis index rebuild`, `chassis list`,
`chassis get`, and `chassis search`; each accepts `--vault`. `validate [vault]`
retains its original positional path. Reads/rebuilds never mutate source records.

Filters combine exact matches on type, venture, status, parent, assigned_agent,
sensitivity, next_milestone, milestone_due_at, due_at, blocker_reason, and
last_activity_at. Null is supported for nullable fields. Results are ordered by
ID and include fields plus body/activity only for authorized visible records.
Search is a literal, Unicode-case-insensitive substring within title, next_step,
or body; blank and unmatched searches return `[]`. See the architecture for details.

Every read scans current source bytes, compares nanosecond mtime and SHA-256,
and validates the graph and policy before answering. Additions, edits, removals,
preserved-mtime edits, and invalid sources are covered. Missing/corrupt caches
rebuild; schema version 3, SQLite structure, and row-content digests are checked.
Git history is consulted at index time even when source bytes and mtime are unchanged.
`.chassis/index.sqlite` stays ignored. A lock/storage error is reported rather
than treated as corruption. No large-vault benchmark or atomic snapshot across
concurrent multi-file edits has been established. Public validation errors are
generic to avoid hidden filenames/bodies. Read controls are tested through CLI,
real stdio MCP, and portal JSON; these do not provide filesystem encryption.

## Current write contract and limits

`RecordStore(root)` exposes `update_record(id, changes, expected_version, agent)`,
`create_record(type, fields, agent)`, and `commit_human(path)`. CLI commands are
`chassis update ID --expected-version N --changes '<JSON>'`, `chassis create TYPE
--fields '<JSON>'`, and `chassis commit-human <path>`, each with optional `--vault`.
CLI caller ID is `CHASSIS_AGENT_ID`, proven with `CHASSIS_AGENT_TOKEN`; authors come
from `CHASSIS_AGENT_NAME` and `CHASSIS_AGENT_EMAIL`. Library calls need the same
credential, including explicit agent arguments. Assignment never supplies identity.

Unknown/nonwriting agents are denied after policy/credential reads. Scoped updates check
current/destination grants using frontmatter before reading a record body.
Template creates check the explicit venture/type grant before template/record I/O.
Denied scopes never access the lock, index, or Git.
Under `.chassis/write.lock`, policy and source are reread; version, dirtiness,
schema, references, assignments, and cycles are checked before replacement.
`atomic.write_atomic` is the only replacement primitive: sibling temp, fsync,
replace, directory fsync. Successful writes commit only the target, preserve
unrelated staging, refresh the index, and release the lock. Reads/rebuilds share it.

Updates reject supplied id/version/updated_at; creates require id and generate
version 1/time. Type cannot change the stable path. Stale conflicts include the
current version, change no source/cache or history, and use CLI exit 3. Other
write refusals use exit 1; usage errors use 2. Success includes record plus commit.
Git failure restores the old source when safe; post-commit index failure reports
`committed: true`, the SHA, and current version. Rebuild without blindly retrying.

`commit-human` requires the configured agent's token, grant, and clearance. It
preserves manual file bytes and their version, commits as the human,
and refreshes the index. It cannot commit policy/nonrecord paths. Reread after that
handoff. Both agent and human paths reject `S` or any lowercase `git ls-files -v`
tag even if the file is unchanged; uppercase `H` is normal. They share the content
hash check as well. A2 requires known
ventures in policy, so humans provision new venture scopes; agent record tools
cannot grant themselves access.

`create_from_template(template, venture, fields, agent)` is also a `RecordStore`
method. CLI: `chassis new initiative|agent --venture ID --fields '<JSON>' [--vault PATH]`.
Fields require `id`, `title`, `owner`, `next_step`, and an exact-name `sections`
object; status defaults to `planned`. The call controls type, venture, parent,
and body. Version/time remain generated by `create_record`. Templates must be
present under the selected vault's `templates/` directory. See README for a full example.

Agent documents live under `records/agents/`, share existing record validation,
queries, update, and human-commit behavior, and grant nothing. To author one, a
human must explicitly grant the existing writer `agent: write` for that venture.
The new document ID gets no access until a human supplies policy grants and a
token; assignment still requires a known policy ID. The fixed template notice
does not itself grant read permission.

The lock is POSIX and was verified on Linux. Ordinary editors/external Git do not
honor it. A hard exit after replace but before commit can leave a complete dirty
record needing explicit recovery; a pre-replace crash can leave an unused temp.
Do not unlink a live lock. No unrestricted concurrent manual-editing or filesystem
isolation claim is made. Template validation checks structure and explicit markers,
not business quality. Obsidian UI, desktop MCP-client UI, portal frontend, and live
Miro remain unverified. The backend has actual loopback HTTP and ASGI contract checks.

## Current MCP contract

Install the optional `mcp` extra first. `chassis-mcp --vault PATH` uses official SDK
stdio. `CHASSIS_VAULT` is the fallback root; otherwise the working directory is
used. Configure `CHASSIS_AGENT_ID`, `CHASSIS_AGENT_TOKEN`, and write-author name/email
on the server. Tool schemas accept no caller identity arguments. `read_record`
wraps the library's existing `get_record`; the tool is `update_record`, never upsert.

`ToolHandlers` is independent of the MCP transport and delegates to the CLI's
existing library methods. The read-only portal calls those authorized library reads. Errors are
structured (`conflict` with current_version, unauthorized, dirty_record,
validation with field/reason, not_found). Git and post-commit failures retain their recovery codes; IndexFileError maps
to generic internal_error without absolute index paths. Committed/unknown
outcomes keep recovery metadata. Raw hook and
exception diagnostics go only to stderr. Stdout contains protocol traffic only.
The stable lock inode remains after clean process exit, but the kernel lock is
released; never unlink it to clear contention. Malformed JSON returns -32700;
requests above the configurable 1 MiB cap get a structured error. SIGTERM during
an active transaction leaves no orphan children and releases the kernel lock.

See README for a placeholder-only client configuration and the exact tool/result
shapes. Raw JSON-RPC and official SDK subprocess clients were verified; no Claude
Desktop UI or MCP HTTP transport pass is claimed.

## Current portal and SecOps boundary

`chassis portal [--port 8765]` binds only 127.0.0.1. The legacy remote override is
removed. The configured viewer defaults to reviewer via
CHASSIS_PORTAL_VIEWER_AGENT and uses CHASSIS_AGENT_TOKEN. Host/Origin, token,
grant, clearance, generic-error, and no-store controls remain in force.

The original seven GET contracts remain. Layout adds an eighth GET route;
PATCH `/api/records/{id}` and PUT `/api/layout` use the shared local write guard.
Session returns the actual writes_enabled flag and an in-memory per-launch CSRF.
No credentials enter the bundle, Git, audit, or screenshots. Default read-only
method behavior is preserved. Counts, health, versions, and viewer-only etags
retain the existing library protections.

C1/C2 are available only on `step7-c1-write` pending independent SecOps review.
The supplied Step 6 SecOps and QE documents are now preserved as dated evidence.
Their local/sample-only Step 6 verdicts are not approval of these new writes.
Real Andy data and agent-to-agent channels remain NO-GO. The vault, Git history,
and cache remain plaintext. The canvas browser checks are recorded in the current checkpoint.

Use [project instructions and the next-step prompt](docs/PROJECT_CHAT_SETUP.md).
At each step's end, update this checkpoint, acceptance evidence, and findings with
the implementation commit, executed checks, open gaps, and next chat's prompt.
An uploaded copy is a snapshot; the next chat must read current repo guidance.
Do not assume a prior scratch filesystem, installed app, or credential persists.

## Next chat starting prompt

```text
Continue the authorized Step 7 command canvas from cursor/step7-canvas-d0a6.
Do not touch main. Main is 42f0fa0. The PR base is step7-c1-write. C1/C2 and the
canvas stay off main until independent SecOps review. Read AGENTS.md,
CHASSIS_PROJECT_HANDOFF.md, docs/ARCHITECTURE.md, docs/PORTAL-ADR.md,
docs/STEP7-CANVAS-SCOPE.md, evidence/acceptance.md, and FINDINGS.md.

F1-F6 and X1-X3 are implemented on cursor/step7-canvas-d0a6. Playwright's 13
canvas tests passed, including the six command-bar phrases and task linking.
Screenshots are in evidence/step7-ui/. Do not claim SecOps, QE, or Code Reviewer
approval. Do not merge to main.

A fresh locked checkout of 1cb92f4 passed: all-extras 698, core 513 passed
and 8 skipped, portal 663 passed, 7 skipped, and 1 warning. npm test was 14
passed. Contrast and the production audit were clean. Two builds matched the
committed 21 files. Playwright alone passed 13 tests. The venture graph is
dagre, not the prototype lanes.
No real data, ask/model, Miro, gateway, hosting, deployment, or secrets in code.
Demo target remains Monday, November 23, 2026, morning, America/Phoenix.
```
