# Chassis architecture

## Current boundary

Steps 1–5 implement the source-record schema, safe parsing, relationship and policy
validation, fictional records, a disposable SQLite index, and versioned local
record writes, constrained templates, approved portal data fields, and stdio MCP. Commands include `validate`, `index
rebuild`, `list`, `get`, `search`, `update`, `create`, `new`, and `commit-human`.
`chassis-mcp` exposes six tools using the official MCP Python SDK, locked at 2.3.0.
Portal UI, health calculations, layout, and rendering remain later work.
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

Restricted records and edges exposing them are excluded before graph emission.
Later tests must cover hidden parents and descendants, and a previously rendered
record changing from normal to restricted. Exclusion alone does not remove old
board content; that transition needs an explicit, tested policy before release.
Status changes must not move neighboring cards or alter parent summaries.

## C3 and C5: agent identity and tool boundaries

`agents.yaml` defines grants by agent ID, venture ID, and record type. A write
grant permits reads too. Unknown agents are read-only. Missing or invalid policy
must deny writes. Reload and check the policy on every write, including old and
new scope when relevant. A record's `assigned_agent` never supplies caller identity.
Record tools cannot edit the policy file. Policy validation rejects grants other
than read/write, unknown venture references, and unknown assignment IDs. Step 3
enforces exact venture/type write grants, including old and new scope on a move.
Restricted records use the same write-grant rule; sensitivity is not an identity.

CLI and MCP caller identity come from `CHASSIS_AGENT_ID`; the library accepts an explicit trusted
caller ID. Author name/email come from `CHASSIS_AGENT_NAME` / `CHASSIS_AGENT_EMAIL`.
Unknown/read-only callers are refused after reading only policy, before record,
lock, index, template, or Git access. Scoped updates read only target frontmatter
and check current/destination grants before reading a record body. Template creates
check the supplied venture/type grant before any template or record I/O.
Denied scopes never open the lock/index or invoke Git. Under the lock,
policy and the target are reread and grants are checked again. These are local
authorization checks, not an authentication service or a filesystem sandbox.

`chassis.tool_handlers.ToolHandlers` contains transport-independent argument
models, error mapping, and thin calls into the same `RecordIndex`/`RecordStore`
methods used by the CLI. `chassis.mcp_server` supplies the official SDK stdio
adapter, runs blocking library calls in worker threads, and logs to stderr.
There are exactly six tools: `list_records`, `read_record`, `search`,
`create_record`, `create_from_template`, and `update_record`. The library's
`get_record` method is exposed as `read_record`; no `upsert_record` tool exists.
Arguments forbid extra fields and accept no caller ID/name/email. `--vault` or
`CHASSIS_VAULT` sets the vault; the default is the process's working directory.
No model SDK, model credential, HTTP server, or agent spawning
is required. Agent templates remain files; their default permission is read-only.

MCP success results are objects: `records` for list/search, `record` for read,
and `record` plus `commit` for writes. Identical JSON is returned in text content
and `structuredContent`. Failures set `isError: true`: `conflict` includes the
expected/current versions, `unauthorized` and `dirty_record` retain actionable
details, `validation` includes a field and reason (plus issues for schema errors),
and `not_found` identifies missing records/tools. Whole-record/relationship errors
use `record` as the field when no narrower field is available. Git/index/internal
failures keep separate structured codes. Raw hook/exception diagnostics go only
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
The checked-in sample policy and original 13 records remain unchanged.

## Disposable index and read contract

`RecordIndex(root)` in `chassis.index` is the transport-independent library API.
It uses the Python standard-library SQLite driver. `.chassis/index.sqlite` is
ignored by Git and can always be deleted. Sources, policy, and Git history are
never changed by reads or rebuilds.

```python
from pathlib import Path
from chassis.index import RecordIndex

index = RecordIndex(Path("."))
index.list_records({"type": "task", "sensitivity": "restricted"})
index.get_record("task-launch-budget")
index.search("three most repeated")
```

All results contain the full normalized record plus unchanged Markdown `body`
and derived `last_activity_at`.
Lists and searches use ascending ID order. `sensitivity` is always present;
restricted records remain readable here. Renderer filtering belongs to C2.

Filters are case-sensitive exact matches on type, venture, status, parent,
assigned_agent, sensitivity, next_milestone, milestone_due_at, due_at,
blocker_reason, and last_activity_at, combined with AND. Omission means no constraint.
`None` matches any nullable field; CLI `null` has the same meaning. Date filters
require `YYYY-MM-DD`. Activity filters match the returned UTC datetime exactly.
Unsupported filter fields or value types raise `ValueError`. No-match
list/search results are `[]`; a missing ID is `None` in Python and exit code 1
with `NOT FOUND` on CLI stderr. JSON output has sorted keys and no cache metadata.

Search trims outer query whitespace, then matches a literal Unicode-casefolded
substring within title, next_step, or body. There is no query language, wildcard,
regular expression, relevance ranking, or cross-field phrase match. Blank search
returns `[]` after validating the working tree.

Every read scans record paths and hashes their current bytes with SHA-256, even
when mtime is unchanged. Nanosecond mtime and content hash select cached versus
newly parsed records. The exact bytes hashed are parsed; metadata changes during
that individual read fail with the filename. Additions, edits, and removals are
validated as a complete graph before the cache transaction updates changed rows.
Policy validation and known-assignment checks also run on every read.

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
Schema-2 caches rebuild automatically. No health, age threshold, or colors are derived.

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

## Approved roadmap change, 2026-11-16

Joe moved the portal into scope after MCP. This supersedes the earlier Miro-first
sequence. Step 5 adds the explicitly approved data fields and MCP only; no portal,
graph-export, layout, Miro, agent integration, or chat-import implementation is included.

| Order | Scope and gate |
| :--- | :--- |
| Step 5 | Complete: transport-independent MCP tools, proved through real stdio clients |
| Step 6 | Read-only command-center web portal over the Chassis library and index; Joe must approve its design prototype before any portal code |
| Step 7 | Renderer-neutral layout and change planner |
| Step 8, optional | Miro export: designated scratch API contract/deletion probe first, then adapter and live export proofs |
| Step 9, separately scoped later | Chat import |

Portal requirements: home shows every venture's health; navigation drills from
venture to initiative to tasks; a dependency map consumes the neutral JSON graph;
an ask-anything bar is wired to the agent. The portal and its ask flow are read-only.
The prototype review must settle information hierarchy, health definitions, and
the agent connection/identity before implementation. It does not authorize deployment.

The portal needs a minimal renderer-neutral nodes/edges projection before the
later layout planner exists. Define that read contract during the portal step;
leave position planning and per-item change planning for Step 7. The present
`graph.py` validates relationships and is not that JSON export. C2 filtering of
restricted nodes and revealing edges still applies. The index alone does not
provide read isolation. C1 and the other Miro contracts still govern an optional export.

### Portal fields approved; health decisions remain

Joe approved the milestone, due-date, blocker, and derived activity fields in Step 5.
The remaining decisions concern how the future portal interprets and presents them.

| Information | Current support | Decision needed before the health view |
| :--- | :--- | :--- |
| Lifecycle, responsibility, next action | `status`, `owner`, `assigned_agent`, `next_step` | Define health separately from lifecycle status |
| Drilldown and dependencies | `venture`, `parent`, `depends_on` | Define rollups and hidden-record handling in the neutral read projection |
| Next milestone | Optional `next_milestone` and `milestone_due_at` on ventures/initiatives | Define how missing milestones/dates affect the display |
| Overdue tasks | Optional task `due_at` | Define whether/how lateness affects health |
| Reason for a blocker | Task `blocker_reason`, required only when blocked | Define summaries and dependency effects |
| Last committed activity | Derived `last_activity_at`, including agent/human commits | Define freshness thresholds and how to present uncommitted changes separately |
| Overall health and explanation | No health model | Define computed health, reason, freshness, and an unknown state before assigning colors |

The portal step must settle health rules, reasons, freshness, and unknown states
before assigning colors. Step 5 does not implement health calculations or UI.
