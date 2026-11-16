# Chassis project handoff

**Checkpoint date: 2026-11-16. Step 5 complete. Next: portal design prototype, awaiting Joe's go.**
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
The access layer is the primary value. On 2026-11-16 Joe moved the read-only
command-center portal into scope after MCP. It reuses the same library/index and
neutral graph; Miro follows the layout planner as an optional export.

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
- The prototype-gated portal, health calculations, layout, optional Miro export,
  and chat import remain pending. Step 5 does not authorize beginning them.

Read [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md),
[acceptance evidence](evidence/acceptance.md), and [findings](FINDINGS.md).

## Approved architecture and record model

| Layer | Decision |
| :--- | :--- |
| Store | One Markdown file per record, YAML frontmatter, Git history; repository opens as an Obsidian vault, with no runtime dependency on Obsidian |
| Index | Disposable SQLite rebuilt from working-tree files, including uncommitted edits |
| Connector | Python 3.12, official MCP SDK, stdio initially; transport-agnostic handlers and no model-specific SDK dependency |
| MCP tools | `list_records(filters)`, `read_record(id)`, `search(query)`, `create_record(type, fields)`, `create_from_template(template, venture, fields)`, `update_record(id, changes, expected_version)` |
| Templates | `templates/initiative.md` and `templates/agent.md`; implemented in Step 4, AC4 passed |
| Graph/layout | Renderer-neutral JSON; coordinates and layout logic owned by Chassis |
| Canvas | Read-only portal after MCP, with prototype approval before code; Miro REST API v2 becomes an optional later export |

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

One Acme task is restricted; all Ridgeview records are normal. A Ridgeview render
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
| 6 | Read-only command-center portal over the library/index | Next, only after Joe's go; Joe must approve the design prototype before any portal code |
| 7 | Neutral graph layout and per-item change planner | After the portal |
| 8 | Optional Miro export, including scratch contract/deletion probe before adapter and live proofs | Optional; existing C1–C7 still apply |
| 9 | Chat import as its own separately scoped step | Later |

The portal home must show venture health, allow venture → initiative → task
drilldown, provide a dependency map from neutral JSON, and include an ask-anything
bar wired to the agent. The portal and ask flow are read-only. The prototype gate
also needs to settle the agent connection/identity and health semantics. Step 5
adds only the approved data fields and MCP; the prototype and all portal code remain future work.

A minimal neutral nodes/edges read projection is needed during the portal step,
before Step 7 adds layout and change planning. `graph.py` currently validates
relationships only. Apply C2 filtering before graph emission and retain the Miro
ownership/reconciliation contracts if the optional export is selected.

Joe approved and Step 5 implemented `next_milestone`, `milestone_due_at`, task
`due_at`/`blocker_reason`, and derived `last_activity_at`. Existing `status`, `owner`,
`next_step`, `parent`, and `depends_on` support basic summaries and drilldown.
Health rules, explanations, freshness thresholds, unknown states, and colors
remain portal decisions. Human commits preserve `updated_at`; the derived Git
timestamp includes them. Uncommitted edits remain readable but do not advance
committed activity. Do not add health heuristics without resolving the prototype's semantics.

Step 2 indexes authoritative working-tree Markdown, including uncommitted edits.
`RecordIndex(root)` exposes `list_records(filters)`, `get_record(id)`, `search(query)`,
and `rebuild()`. CLI commands are `chassis index rebuild`, `chassis list`,
`chassis get`, and `chassis search`; each accepts `--vault`. `validate [vault]`
retains its original positional path. Reads/rebuilds never mutate source records.

Filters combine exact matches on type, venture, status, parent, assigned_agent,
sensitivity, next_milestone, milestone_due_at, due_at, blocker_reason, and
last_activity_at. Null is supported for nullable fields. Results are ordered by
ID and include all fields plus body/activity, including sensitivity for restricted records.
Search is a literal, Unicode-case-insensitive substring within title, next_step,
or body; blank and unmatched searches return `[]`. See the architecture for details.

Every read scans current source bytes, compares nanosecond mtime and SHA-256,
and validates the graph and policy before answering. Additions, edits, removals,
preserved-mtime edits, and invalid sources are covered. Missing/corrupt caches
rebuild; schema version 3, SQLite structure, and row-content digests are checked.
Git history is consulted at index time even when source bytes and mtime are unchanged.
`.chassis/index.sqlite` stays ignored. A lock/storage error is reported rather
than treated as corruption. No large-vault benchmark or atomic snapshot across
concurrent multi-file edits has been established. Restricted read results are
intentional; renderer exclusion remains pending. Step 3 write authorization is enforced.

## Current write contract and limits

`RecordStore(root)` exposes `update_record(id, changes, expected_version, agent)`,
`create_record(type, fields, agent)`, and `commit_human(path)`. CLI commands are
`chassis update ID --expected-version N --changes '<JSON>'`, `chassis create TYPE
--fields '<JSON>'`, and `chassis commit-human <path>`, each with optional `--vault`.
CLI caller ID is `CHASSIS_AGENT_ID`; authors come from `CHASSIS_AGENT_NAME` and
`CHASSIS_AGENT_EMAIL`. The library's explicit agent argument is trusted caller
configuration, not `assigned_agent` metadata or an authentication service.

Unknown/read-only agents are denied after policy-only reads. Scoped updates check
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

`commit-human` preserves manual file bytes and their version, commits as the human,
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
The new document ID remains read-only unless a human separately grants access
in `agents.yaml`; assignment still requires a known policy ID. Sample policy is unchanged.

The lock is POSIX and was verified on Linux. Ordinary editors/external Git do not
honor it. A hard exit after replace but before commit can leave a complete dirty
record needing explicit recovery; a pre-replace crash can leave an unused temp.
Do not unlink a live lock. No unrestricted concurrent manual-editing or filesystem
isolation claim is made. Template validation checks structure and explicit markers,
not business quality. Obsidian UI, desktop MCP-client UI, portal, and live Miro remain unverified.

## Current MCP contract

`chassis-mcp --vault PATH` (or `python -m chassis.mcp_server`) uses official SDK
stdio. `CHASSIS_VAULT` is the fallback root; otherwise the working directory is
used. Configure `CHASSIS_AGENT_ID`, `CHASSIS_AGENT_NAME`, and `CHASSIS_AGENT_EMAIL`
on the server. Tool schemas accept no caller identity arguments. `read_record`
wraps the library's existing `get_record`; the tool is `update_record`, never upsert.

`ToolHandlers` is independent of the MCP transport and delegates to the CLI's
existing library methods. A future HTTP adapter must reuse it. Errors are
structured (`conflict` with current_version, unauthorized, dirty_record,
validation with field/reason, not_found). Git/index/internal failures remain
distinct, and committed/unknown outcomes keep recovery metadata. Raw hook and
exception diagnostics go only to stderr. Stdout contains protocol traffic only.
The stable lock inode remains after clean process exit, but the kernel lock is
released; never unlink it to clear contention. Restricted records remain readable
under the existing library contract, so portal/renderer filtering is still required.

See README for a placeholder-only client configuration and the exact tool/result
shapes. Raw JSON-RPC and official SDK subprocess clients were verified; no Claude
Desktop UI or HTTP transport pass is claimed.

Use [project instructions and the next-step prompt](docs/PROJECT_CHAT_SETUP.md).
At each step's end, update this checkpoint, acceptance evidence, and findings with
the implementation commit, executed checks, open gaps, and next chat's prompt.
An uploaded copy is a snapshot; the next chat must read current repo guidance.
Do not assume a prior scratch filesystem, installed app, or credential persists.

## Next chat starting prompt

Use only after Joe authorizes the portal step:

```text
Start the portal step with the design prototype only. Pull current main and
read AGENTS.md, CHASSIS_PROJECT_HANDOFF.md, docs/ARCHITECTURE.md,
evidence/acceptance.md, and FINDINGS.md. Step 5 runtime/test checkpoint is
6ab3b14a759e1e3d5f8e9beae08bf8943b7c8d5d, with 431 tests passing from a clean
checkout and real stdio AC2 evidence. Preserve every later documentation commit.

Use only fictional records and local execution. The portal is read-only, reuses
the existing library/index and a minimal renderer-neutral read projection, and
must respect C1-C7. Show venture health, venture-to-initiative-to-task drilldown,
a dependency map, and an ask-anything bar with a read-only agent flow.

The approved milestone/date/blocker fields and derived last_activity_at exist.
Settle health rules, explanations, unknown states, freshness, hidden-record
handling, and the ask flow's connection/identity in the prototype. Do not treat
status alone as health. Apply C2 before any rendered graph or portal exposure.

Present a concrete design prototype for Joe's review. No portal implementation
code before Joe approves that prototype. Do not begin layout/change planning,
optional Miro export, chat import, agent spawning, real-data work, or deployment.
Update the handoff and report DELIVERED / VERIFIED (table) / RISKS-OPEN / NEXT,
then stop at the prototype approval gate.
```
