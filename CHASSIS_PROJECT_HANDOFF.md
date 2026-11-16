# Chassis project handoff

**Checkpoint date: 2026-11-16. Step 2 complete. Next build: Step 3, awaiting Joe's go.**
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
The access layer is the primary value. Miro is the initial visual window; a later
custom portal should reuse the same data and connector plumbing.

The broader engagement is paid discovery plus a working mock, with the full build
gated on the outcome. Its eventual demonstration on 1–2 real ventures is separate
from the approved **Increment 0: local execution and fictional data only**.
No price, delivery deadline, payment receipt, or full-build approval is established
by the supplied references. Do not invent commercial commitments.

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
- Clean-checkout proof at the implementation commit: `uv sync --locked`,
  **151 passing tests**, 13 valid records, and an installed CLI rebuild of 13 records.
  Step 1's earlier 72-test baseline is retained as historical evidence.
- Implemented: strict schema, safe frontmatter parsing, body preservation,
  relationship/dependency and policy validation, fictional fixtures, the disposable
  SQLite index, automatic refresh/recovery, and local validate/index/list/get/search.
- `agents.yaml` has a strict Pydantic model. Only read/write scoped grants are
  allowed and unknown assignment IDs are rejected. Write authorization is Step 3.
- `src/chassis/graph.py` validates record relationships; it is not the future
  renderer-neutral JSON graph or layout planner.
- MCP, record mutations, template expansion, and Miro rendering are pending.

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md),
[acceptance evidence](evidence/acceptance.md), and [findings](FINDINGS.md).

## Approved architecture and record model

| Layer | Decision |
| :--- | :--- |
| Store | One Markdown file per record, YAML frontmatter, Git history; repository opens as an Obsidian vault, with no runtime dependency on Obsidian |
| Index | Disposable SQLite rebuilt from working-tree files, including uncommitted edits |
| Connector | Python 3.12, official MCP SDK, stdio initially; transport-agnostic handlers and no model-specific SDK dependency |
| Tools | `list_records(filter)`, `get_record(id)`, `search(query)`, `create_record(type, fields, template?)`, `update_record(id, changes, expected_version)` |
| Templates | `templates/initiative.md` and `templates/agent.md`; planned in Step 4 |
| Graph/layout | Renderer-neutral JSON; coordinates and layout logic owned by Chassis |
| Canvas | Miro REST API v2 adapter now; custom portal such as React Flow later |

Required fields: `id`, `type`, `title`, `status`, `owner`, `venture`, `parent`,
`next_step`, `updated_at`, `version`. Optional: `depends_on: []`,
`sensitivity: normal | restricted` (default normal), `assigned_agent` (default null).
Statuses: `planned`, `in_progress`, `blocked`, `done`. IDs and filenames are stable.
A venture references itself and has a null parent; initiatives parent to their
venture; tasks parent to an initiative in the same venture. Dependencies may cross
ventures but cannot be missing, duplicated, self-referential, or cyclic.

The initiative template must populate positioning, audience, channels, offer,
launch checklist, and success metrics. Empty headings do not satisfy acceptance.
The agent template holds playbooks, channels, data scope, and permissions, with
read-only defaults. Agent templates are files only; no spawning in this build.

## C1–C7 implementation contracts

**C1, ownership and mapping:** Native tags on cards are approved. No visible
`chassis:` markers in frame titles or connector captions. Track
`render/miro/<board-id>.json` with IDs, fingerprints, format version, and operation
state only. Never store content, secrets, or full API payloads in the mapping.
Persist a pending entry before each create. Missing/mismatched mapped items stop
the run. Never adopt unmapped items. A create timeout without an item ID stays
unresolved; a fingerprint match cannot authorize adoption or a blind retry.

**C2, sensitivity and assignment:** Restricted records never enter the rendered
graph; exclude edges that reveal them. `assigned_agent` is descriptive metadata.
Resolve previously visible records becoming restricted and hidden-parent behavior
before renderer acceptance. Filtering future output alone leaves old content visible.

**C3, permissions:** Reload/check `agents.yaml` on every write. Grants are scoped
by agent ID, venture, and record type. Unknown agents are read-only. Missing or
invalid policy denies writes. Use configured caller identity, not `assigned_agent`.
Record tools cannot edit permissions. Do not claim data-access isolation before tested.

**C4, neutral graph:** The planner emits renderer-neutral JSON. No Miro runtime
types above `src/chassis/render/miro/`. A future portal consumes the same graph.

**C5, transport:** Tool handlers are independent of MCP transport. Stdio only now.

**C6, human edits and concurrency:** Refuse dirty target writes, naming the file
and saying exactly `uncommitted human edit`. Add `chassis commit-human <path>`
using `CHASSIS_HUMAN_NAME` / `CHASSIS_HUMAN_EMAIL` in Step 3. Reread and compare
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

One Acme task is restricted; all Ridgeview records are normal. A Ridgeview render
should contain one venture frame, seven cards, and two dependency connectors.

| AC | Required evidence | Current status |
| :--- | :--- | :--- |
| 1 | Obsidian opens cleanly; every record validates | Schema/relationships pass; actual Obsidian UI check pending after a desktop launch problem |
| 2 | Real MCP client lists, reads, creates, updates | Pending Step 5 |
| 3 | Stale rejection; good version bump and attributed Git commit | Pending Step 3; development commits do not prove this |
| 4 | Initiative created from template with filled go-to-market sections | Pending Step 4 |
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
| 3 | Create/update, policy enforcement, concurrency, Git, commit-human | Next, only after Joe's go |
| 4 | Initiative and agent templates | Pending |
| 5 | MCP tools and real stdio client integration | Pending |
| 6 | Scratch Miro contract probe and frame-deletion experiment | Pending |
| 7 | Neutral JSON graph, layout, per-item change planner | Pending |
| 8 | Miro adapter, mapping persistence, rate limits, rendering | Pending |
| 9 | Live read/write/render proof and final handoff | Pending |

Step 2 indexes authoritative working-tree Markdown, including uncommitted edits.
`RecordIndex(root)` exposes `list_records(filters)`, `get_record(id)`, `search(query)`,
and `rebuild()`. CLI commands are `chassis index rebuild`, `chassis list`,
`chassis get`, and `chassis search`; each accepts `--vault`. `validate [vault]`
retains its original positional path. Reads/rebuilds never mutate source records.

Filters combine exact matches on type, venture, status, parent, assigned_agent,
and sensitivity. Null is supported for parent/assignment. Results are ordered by
ID and include all fields plus body, including sensitivity for restricted records.
Search is a literal, Unicode-case-insensitive substring within title, next_step,
or body; blank and unmatched searches return `[]`. See the architecture for details.

Every read scans current source bytes, compares nanosecond mtime and SHA-256,
and validates the graph and policy before answering. Additions, edits, removals,
preserved-mtime edits, and invalid sources are covered. Missing/corrupt caches
rebuild; schema version 2, SQLite structure, and row-content digests are checked.
`.chassis/index.sqlite` stays ignored. A lock/storage error is reported rather
than treated as corruption. No large-vault benchmark or atomic snapshot across
concurrent multi-file edits has been established. Restricted read results are
intentional; renderer exclusion and write-time access enforcement remain pending.

Use [project instructions and the next-step prompt](docs/PROJECT_CHAT_SETUP.md).
At each step's end, update this checkpoint, acceptance evidence, and findings with
the implementation commit, executed checks, open gaps, and next chat's prompt.
An uploaded copy is a snapshot; the next chat must read current repo guidance.
Do not assume a prior scratch filesystem, installed app, or credential persists.

## Next chat starting prompt

Use only after Joe authorizes Step 3:

```text
Start Step 3 only. Pull current main and read AGENTS.md, CHASSIS_PROJECT_HANDOFF.md,
docs/ARCHITECTURE.md, evidence/acceptance.md, and FINDINGS.md. Step 2 code is at
39b5b2ee2efbdc272fdd33b479a4884c6b65cfc7; later documentation must be preserved.
Retain all 151 tests and the working-tree/disposable-index read contract.

Implement create_record, update_record, and chassis commit-human under C3/C6.
Use configured caller identity, never assigned_agent. Reload/validate agents.yaml
on every write and check venture/type grants, including old/new scope as relevant.
Unknown callers and missing/invalid policy cannot write. Record tools cannot edit
the policy. Templates remain Step 4.

Under an interprocess lock, reread the record and compare expected_version.
Reject dirty targets with the filename and exact phrase uncommitted human edit.
Stale/refused updates change no files and create no commits. Successful updates
bump version and commit only their record with agent attribution. Implement the
explicit human-commit path using CHASSIS_HUMAN_NAME and CHASSIS_HUMAN_EMAIL.

Use fictional records and local execution only. No MCP, Miro, custom UI, agent
spawning, or deployment. Tests first, roughly 150-line increments, push each
completed increment without force. Update evidence/findings/handoff, report
DELIVERED / VERIFIED / RISKS-OPEN / NEXT, then stop for the next go.
```
