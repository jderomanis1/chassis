# Chassis architecture

## Current boundary

Steps 1–6 implement the source-record schema, safe parsing, relationship and policy
validation, fictional records, a disposable SQLite index, and versioned local
record writes, constrained templates, approved portal data fields, and stdio MCP. Commands include `validate`, `index
rebuild`, `list`, `get`, `search`, `update`, `create`, `new`, and `commit-human`.
`chassis-mcp` exposes six tools using the optional official MCP SDK, locked at 2.3.0.
Step 6 adds authenticated, scoped library reads, clearance, audit, token provisioning,
and the optional Starlette/uvicorn P1–P4 portal backend with pure health calculations.
Step 7 C-1/C0/C3 add review fixes, session/version contracts, and a demo vault.
The authorized React Flow canvas and gated write/layout endpoints remain open.
Execution and data remain local and fictional; any Miro proof uses designated scratch space.

## Source records

One UTF-8 Markdown file lives at `records/<type>s/<id>.md`. Required frontmatter:
`id`, `type`, `title`, `status`, `owner`, `venture`, `parent`, `next_step`,
`updated_at`, `version`. IDs are lowercase hyphen-separated identifiers.
Statuses are `planned`, `in_progress`, `blocked`, and `done`.

| Type | Venture reference | Parent |
| :--- | :--- | :--- |
| venture | Its own ID | `null` |
| initiative | Existing venture ID | That venture |
| task | Existing venture ID | An initiative in that venture |
| agent | Existing venture ID | That venture; descriptive document only |

Optional fields: `depends_on: []`, `sensitivity: normal | restricted` (default
normal), and `assigned_agent` (default null). Assignment is descriptive metadata.
Ventures and initiatives additionally accept optional `next_milestone` and
`milestone_due_at`; tasks accept optional `due_at` and `blocker_reason`. Dates are
strict `YYYY-MM-DD` strings or YAML date values, never datetimes or numeric epochs.
A task with status `blocked` requires a nonempty reason. Every other status
requires an empty/null reason. Optional fields default to null, so older records
continue to validate except that legacy blocked tasks must supply a reason.
The sample blocked Ridgeview task has been migrated. Fields cannot be populated
on the wrong record type. `last_activity_at` is a read projection, not frontmatter.
Dependencies may cross ventures; self-dependencies, missing targets, and cycles
are invalid. Versions are positive integers. Timestamps carry an explicit zone.
Unknown fields, duplicate YAML keys, unsafe tags, and merge keys are rejected.
Only files under `records/` are records. Body text and line endings are preserved.

## C1: board ownership and tracked mapping

Cards receive a native tag. Frame titles and connector captions have no visible
ownership markers. Mapping files live at `render/miro/<board-id>.json` in Git.
They contain IDs, fingerprints, format version, and operation state only. They
never contain record text, request bodies, credentials, or full API responses.

Persist a pending entry before each create. After a confirmed response, save its
item ID and fingerprint. Verify every mapped remote item before changing it.
A missing or mismatched item stops rendering. Never adopt an unmapped item.

An ambiguous timeout without an item ID stays unresolved and stops the run.
A matching fingerprint cannot prove ownership, so it never authorizes adoption
or an automatic retry. Resolution needs independent confirmation of the original
create outcome. Group deletion is absent from the renderer. A frame-deletion
probe uses separate disposable scratch items and records the observed result.

## C2 and C4: sensitivity and a neutral graph

The future planner emits renderer-neutral JSON: nodes, edges, dimensions,
positions, and semantic presentation fields. No Miro item types or remote IDs
belong in that graph. Layout and generic planning remain outside the adapter.
Miro-specific runtime code lives only below `src/chassis/render/miro/`.

`RecordIndex.graph()` and `read_model.neutral_graph()` supply the current neutral
nodes/edges projection without layout. Library filtering removes unauthorized
restricted records, their edges, hidden-parent descendants, and hidden dependency
IDs from visible records. An update that omits `depends_on` leaves stored
dependency ids unchanged. An update that sends `depends_on` keeps ids the caller
cannot see and checks only ids that are not already stored. A new missing id and
a new hidden id share one `invalid dependency` error and do not write.
A restricted-clearance agent still needs an exact grant.
Counts and health use only that filtered view. Joe's Step 6 decision supersedes
the masked-placeholder design in the supplied ADR and checkpoint.
Previously rendered content becoming restricted still needs explicit removal in
future clients/exporters. The future Miro single-card update contract must not
move neighbors; the portal's computed parent health does roll up visible status.

## C3 and C5: agent identity and tool boundaries

`agents.yaml` defines grants by agent ID, venture ID, and record type. A write
grant permits reads too. Unknown/empty agents and invalid credentials have no access.
Missing or invalid policy denies all reads and writes. Reload policy and token
hashes before and under the vault lock. A record's `assigned_agent` never supplies identity.
Record tools cannot edit the policy file. Policy validation rejects grants other
than read/write, unknown venture references, and unknown assignment IDs. Step 3
enforces exact venture/type write grants, including old and new scope on a move.
Each agent has `clearance: normal` by default or explicit `restricted`. Reading or
writing a restricted record requires restricted clearance and a venture/type grant.
Updates check both current and proposed sensitivity, preventing declassification by
a normal-clearance writer. Reads outside the caller's scope are indistinguishable
from missing records; unauthorized updates use a generic refusal without type/venture.

CLI/MCP caller identity is `CHASSIS_AGENT_ID`, proven with `CHASSIS_AGENT_TOKEN`.
The library accepts explicit agent/token arguments or those environment values.
Token comparison uses SHA-256 and constant-time digest comparison against ignored
`.chassis/agent-tokens.yaml`. The local operator command `chassis agent-token create
<agent-id>` prints a fresh token once, stores only its hash with mode 0600, and
rotates any previous token. The example file contains placeholders only.
Author name/email come from `CHASSIS_AGENT_NAME` / `CHASSIS_AGENT_EMAIL`.
Unknown or nonwriting callers are refused after policy/credential reads, before record,
lock, index, template, or Git access. Scoped updates read only target frontmatter
and check current/destination grants before reading a record body. Template creates
check the supplied venture/type grant before any template or record I/O.
Denied scopes never open the lock/index or invoke Git. Under the lock,
policy, credentials, and the target are reread and grants are checked again.
These are local bearer-token controls; direct filesystem and Git access bypass them.

Each public library read/write appends one UTC JSON line to ignored
`.chassis/audit.jsonl`: agent ID, tool, outcome, and returned IDs or list/search count.
Denied reads record no IDs. Bodies, search text, and tokens are never logged.
An append failure withholds a read result; a post-commit failure reports recovery
metadata rather than falsely saying the write did not commit. The log is local,
append-locked, and body-free; it is not a remote tamper-proof ledger.

`chassis.tool_handlers.ToolHandlers` contains transport-independent argument
models, error mapping, and thin calls into the same `RecordIndex`/`RecordStore`
methods used by the CLI. `chassis.mcp_server` lazily loads `mcp_transport` and gives
an install message when the `mcp` extra is absent. The official SDK adapter runs
blocking library calls in worker threads and logs to stderr.
There are exactly six tools: `list_records`, `read_record`, `search`,
`create_record`, `create_from_template`, and `update_record`. The library's
`get_record` method is exposed as `read_record`; no `upsert_record` tool exists.
Arguments forbid extra fields and accept no caller ID/token/name/email. `--vault` or
`CHASSIS_VAULT` sets the vault; the default is the process's working directory.
No model SDK, model credential, or agent spawning is required. Agent templates
remain descriptive files and grant no access. MCP has no HTTP listener.
Stdio refuses invalid identity before handshake, caps each request at 1 MiB
(environment/CLI configurable), returns `-32700` for malformed JSON, and drains
oversized requests before continuing. SIGTERM waits for an active transaction,
ends child processes, and frees the kernel lock while retaining its stable inode.

MCP success results are objects: `records` for list/search, `record` for read,
and `record` plus `commit` for writes. Identical JSON is returned in text content
and `structuredContent`. Failures set `isError: true`: `conflict` includes the
expected/current versions, `unauthorized` is generic, `dirty_record` retains actionable
details, `validation` includes a field and reason (plus issues for schema errors),
and record `not_found` never echoes the requested ID. Whole-record/relationship errors
use `record` as the field when no narrower field is available. Git/post-commit failures retain their recovery codes; index-path failures map
to generic internal_error without exposing the absolute path. Raw hook/exception diagnostics go only
to stderr. Post-commit and uncertain-commit metadata is preserved for recovery.

## C6: writes, human edits, and the index

`RecordStore(root)` in `chassis.store` exposes `update_record(id, changes,
expected_version, agent)`, `create_record(type, fields, agent)`, and
`create_from_template(template, venture, fields, agent)`, plus `commit_human(path)`.
The root must be an initialized Git repository with a HEAD.
The shared exclusive POSIX lock is `.chassis/write.lock`. Cache reads/rebuilds
also use it. The kernel releases it on process exit; never unlink a live lock file.

After authorization preflight, an update locks, rereads the source, rechecks grants
and `expected_version`, rejects a dirty target, and validates the proposed schema,
references, assignments, and graph. It bumps version by exactly one and advances
`updated_at`, writes atomically, commits only that record, refreshes the index,
and releases the lock. Body bytes are preserved unless explicitly changed.
Create uses the same transaction, starts at version 1 with a generated timestamp,
and rejects duplicate IDs, missing references, and cycles before writing.

`id`, `version`, and `updated_at` cannot be supplied in update changes. Create
requires an ID but generates version/time. Type changes are refused because they
would move the stable record path. Supplied new venture scopes cannot bootstrap
their own grants: A2 requires policy venture references to already exist. Human
provisioning of a venture and its policy remains separate from record tools.

Success returns `{"record": <full record plus body and derived activity>, "commit": <SHA>}`. A stale
write raises `ConflictError` with `as_dict()` containing `error: conflict`, `id`,
`expected_version`, and `current_version`. No record/cache write or commit occurs.
Other write refusals also expose `as_dict()`. The CLI prints success JSON to
stdout, refusal JSON to stderr, and uses exit 3 for conflicts, 1 for other errors,
and argparse's exit 2 for usage errors. Schema/parser errors retain their reasons.

All replacements go through `atomic.write_atomic`: sibling temp file, flush,
file fsync, `os.replace`, then directory fsync. A failed Git commit restores the
original bytes (or removes a new file) when HEAD and the file have not changed
externally. Unrelated staging is preserved. A cache failure after a successful
commit raises `CommittedIndexError` with `committed: true`, the commit SHA, and
current version. Rebuild the disposable index; do not blindly repeat that write.

A dirty target is refused with its filename and the exact phrase
`uncommitted human edit`. The shared guard runs `git ls-files -v -- <path>` and
refuses `S` or any lowercase tag even on an unchanged file. Normal uppercase `H`
is accepted. It then checks status and compares content with HEAD if status is clean.
`chassis commit-human <path>` validates and commits only the selected record as
`CHASSIS_HUMAN_NAME` / `CHASSIS_HUMAN_EMAIL`, then refreshes the index. It preserves
the manual file bytes, including its version, and cannot commit policy/nonrecord
paths. It reuses that same flag/hash check. Clear assume-unchanged/skip-worktree
flags first if the guard names them; Chassis never clears flags implicitly.
It also requires a valid configured agent token, write grant, and clearance;
the human name/email are Git attribution, not a permission bypass.

Ordinary editors and external Git commands do not honor Chassis locks. Coordinate
manual editing and reread after the human handoff. File replacement and Git are
not one crash-atomic transaction: a hard exit after replace can leave a complete,
uncommitted record for explicit recovery. A hard exit before replace leaves the
original intact and can leave an unused temp file, which record parsing ignores.
Only Linux/POSIX execution has been verified; native Windows locking is not provided.
The index remains disposable and reads working-tree edits, including uncommitted ones.

## Templates (AC4)

`GTM_SECTIONS` in `chassis.templates` fixes the exact ordered names: `Positioning`,
`Audience`, `Channels`, `Offer`, `Launch checklist`, `Success metrics`.
`templates/initiative.md` contains those headings and one named placeholder per
section. `fields.sections` maps those exact names to nonempty strings. Expansion
rejects missing/unknown keys, empty or markup-only content, recognized placeholder
markers, damaged headings/order, and tokens assigned to the wrong sections.
This validates structure and explicit markers, not the business quality of prose.
Markers include FIXME and XXX. Matching normalizes to Unicode NFKC so compatibility
forms cannot conceal known markers; it does not claim to detect all Unicode
homoglyphs. Accepted content is not normalized/replaced. Caller owner, sensitivity,
and assignment use the same strict schema constraints before template expansion,
and a non-null assignment must be a known policy ID. The shared create path checks
the complete record and policy again.

`create_from_template` checks policy and the venture/type grant before opening
the template, then calls `create_record`. That path reloads authorization before
and inside the shared lock, validates the complete proposed record graph, writes
atomically, creates one attributed record-only commit, and refreshes the index.
No second persistence path or policy writer exists. Unknown template names never
become paths; template files/directories cannot be symlinks. No template code runs.

Required input fields are `id`, `title`, `owner`, `next_step`, and `sections`.
`status` defaults to `planned`. Other existing optional record fields are accepted.
The call controls type, venture, parent, and body; supplied overrides are refused.
The existing create path generates version/time and rejects supplied values.
Raw `create_record` and later updates retain the general Markdown-body contract;
AC4's section contract applies to creation from the initiative template.

`templates/agent.md` takes `Playbooks`, `Channels`, and `Data scope`; its fixed
`Permissions` text states the read-only default and human-managed policy authority.
It creates an `agent` record under `records/agents/`, parented to its venture.
The new kind uses existing validation, index, update, and human-commit behavior.
It grants no access, registers no caller, and starts no process. A human must
explicitly grant the author `agent: write` to create these documents. A separate
human policy edit is required to give the new ID any writes or make it assignable.
Step 6 changes the sample policy to deny unknown agents and gives the chief-of-staff
restricted clearance. The restricted sample's owner is unique for meaningful leak
scans; the fixture remains 13 fictional records.

## Disposable index and read contract

`RecordIndex(root, agent=None, token=None)` is the transport-independent read API.
It uses the Python standard-library SQLite driver. `.chassis/index.sqlite` is
ignored by Git and can always be deleted. Sources, policy, and Git history are
never changed by reads or rebuilds.

```python
from pathlib import Path
from chassis.index import RecordIndex

index = RecordIndex(Path("."))  # Uses CHASSIS_AGENT_ID and CHASSIS_AGENT_TOKEN.
index.list_records({"type": "task", "sensitivity": "restricted"})
index.get_record("task-launch-budget")
index.search("three most repeated")
```

All results contain the full normalized record plus unchanged Markdown `body`
and derived `last_activity_at`.
Lists and searches use ascending ID order. `sensitivity` is always present on
returned records. All filtering, including hidden parents and dependencies, is
enforced here before CLI, MCP, graph, search, counts, or portal serialization.
`read_record` aliases `get_record`; `graph(venture=None)` uses the same visibility.

Filters are case-sensitive exact matches on type, venture, status, parent,
assigned_agent, sensitivity, next_milestone, milestone_due_at, due_at,
blocker_reason, and last_activity_at, combined with AND. Omission means no constraint.
`None` matches any nullable field; CLI `null` has the same meaning. Date filters
require `YYYY-MM-DD`. Activity filters match the returned UTC datetime exactly.
Unsupported filter fields or value types raise `ValueError`. No-match
list/search results are `[]`; a missing or unauthorized ID is `None` in Python and
exit code 1 with generic JSON `not_found` on CLI stderr. Unauthorized list/search
and rebuild return `[]` and zero respectively. JSON has no cache metadata.

Search trims outer query whitespace, then matches a literal Unicode-casefolded
substring within title, next_step, or body. There is no query language, wildcard,
regular expression, relevance ranking, or cross-field phrase match. Blank search
returns `[]`; valid callers' working-tree reads still validate authoritative sources.

Every read scans record paths and hashes their current bytes with SHA-256, even
when mtime is unchanged. Nanosecond mtime and content hash select cached versus
newly parsed records. The exact bytes hashed are parsed; metadata changes during
that individual read fail safely. Public validation errors omit source names and
contents so a malformed hidden row cannot expose them. Additions, edits, and removals are
validated as a complete graph before the cache transaction updates changed rows.
Policy validation and known-assignment checks also run on every read.
The generic error has no private parser cause for a transport formatter to expose.
Whole-vault validation during writes also hides diagnostics when the caller lacks
read access to any involved source. Unreadable target metadata cannot prove a grant
and returns the same generic write denial. Caller-supplied proposal validation
retains field-level diagnostics when they do not expose another source.

Rebuild validates all sources before replacing the database atomically. Missing
indexes rebuild automatically. Schema version 3, column order, SQLite quick_check,
record JSON, and row-content digests detect cache damage; a read rebuilds and
retries once. Locked databases and other storage errors are reported, not treated
as corruption. Cache symlinks are rejected. Invalid sources never yield old data.

At index time, `git log` over current HEAD history supplies the newest touching
commit for each record path. Its committer timestamp is normalized to UTC. Agent
and human commits count; an unrelated commit or an uncommitted edit does not advance
the record's activity. No history means null, including non-Git read-only folders,
unborn repositories, and new uncommitted records. The value is stored only in the
disposable projection and included in row integrity checks, never in record JSON
or source Markdown. History is refreshed on every read, independently of source
mtime/hash; an edit followed by a byte-identical restore still advances activity.
Schema-2 caches rebuild automatically. Health is a pure portal projection over
the authorized read view, never stored in source Markdown or SQLite.

Each read costs a full source-byte scan, Git history scan, and graph validation. Rebuilds serialize
an in-memory SQLite database through the same atomic writer. This is an explicit
local-increment tradeoff, not a large-vault performance claim. The shared lock
coordinates Chassis operations but cannot provide an atomic snapshot across
multiple files edited concurrently by ordinary editors.

## C7: review and delivery

Use tests first and approximately 150-line increments. Commit and push each
completed increment to the private repository, preserving existing repository
instructions and work. Never force-push. Secrets come from the environment;
`.env` stays ignored. Report delivery, verification, open risks, and the next step.

## Approved canvas pivot, 2026-11-17

Joe's [Step 7 authorization](STEP7-CANVAS-SCOPE.md) records the client's November
16 decision: one zoomable card canvas over the live store. It supersedes the
five-screen P5–P8 port and stub ask flow. The approved prototype is the visual
source for React 18, React Flow v12, and Vite. Built assets will be committed;
Node is not a Python runtime requirement. The review branch now has a partial F1
scaffold and committed assets; browser execution is blocked before page navigation.

| Order | Scope and gate |
| :--- | :--- |
| Step 5 | Complete: real stdio MCP proof |
| Step 6 | Complete: authenticated read security and portal backend P1–P4 |
| Step 7 | C1/C2 on review branch; partial F1 browser-blocked; F2-F6 open; source pack supplied |
| Optional Miro | Later export; designated scratch probe before any adapter proof |
| Chat import | Separately scoped later work |

### Current portal backend

`chassis portal` runs one Starlette/uvicorn process with the optional `portal`
extra. It binds only `127.0.0.1`; `localhost` is normalized and the remote override
is removed. The configured viewer defaults to `reviewer` and is proven with
`CHASSIS_AGENT_TOKEN`. Requests cannot choose another identity or clearance.
Exact Host and optional matching Origin checks remain on the original seven GET
routes, with private, no-store responses and generic JSON errors. A layout GET is
added. The package mount serves the built F1 shell and never serves the vault.

`/api/session` returns a fresh per-launch CSRF token, the actual writes_enabled flag, and
the viewer ID. The token stays in memory. Cards, task projections, and portal
graph nodes expose source versions; task projections include next_step so an
editor can preserve it. Full venture and initiative objects already include it.

`version_etag` hashes the viewer's authorized records, including derived activity.
It excludes global Git HEAD, hidden rows, and unrelated repository files, so
hidden edits/commits do not signal activity. Snapshot/drilldown/graph reads retain
concurrent-change retry behavior. Counts and health use only visible children;
health retains the pure Phoenix-calendar 3/7/14-day rules.

C1/C2 are implemented on `step7-c1-write` using the supplied SecOps section 4.
The shared guard requires explicit write enablement, a separate proven normal
editor, exact Host/Origin, same-origin fetch metadata, JSON, CSRF, bounded input,
audit, and rate limiting. PATCH delegates to `RecordStore.update_record` with an
explicit server-bound Git identity and normal-clearance recheck under the lock.
C2 shares the lock/atomic writer and library visibility for ignored per-viewer
layout. No second record-persistence path exists. Independent SecOps review must
precede merge. The F1 shell uses the approved tokens and local font files, but
its browser checks are blocked. F2-F6 and the live MCP/canvas loop remain pending.
No ask endpoint or model call is part of this step.

### Fictional demo generator

`chassis demo-init <new-directory>` creates an independent Git vault with seven
fictional ventures, two initiatives per venture, three tasks per initiative,
29 dependencies including one cross-venture edge, and one restricted task.
It uses the existing schema, validation, atomic writer, and credential provisioner.
It refuses any existing destination and leaves source fixtures unchanged.

The reviewer has normal clearance/read grants, canvas-editor has normal clearance
and write grants on the seven sample ventures, and chief-of-staff has restricted
clearance/write grants. Fresh tokens are returned once; only hashes persist in
ignored `.chassis/agent-tokens.yaml` with mode 0600. One fictional baseline commit
contains records, policy, and the ignore file, with no credentials in Git.
