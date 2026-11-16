# Chassis architecture

## Current boundary

Steps 1–3 implement the source-record schema, safe parsing, relationship and policy
validation, fictional records, a disposable SQLite index, and versioned local
record writes. Commands include `validate`, `index rebuild`, `list`, `get`,
`search`, `update`, `create`, and `commit-human`. Templates, MCP, and rendering
remain planned. All Chassis execution stays local; the later
scratch Miro connection is the only external runtime integration in Increment 0.

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

Optional fields: `depends_on: []`, `sensitivity: normal | restricted` (default
normal), and `assigned_agent` (default null). Assignment is descriptive metadata.
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

CLI identity comes from `CHASSIS_AGENT_ID`; the library accepts an explicit trusted
caller ID. Author name/email come from `CHASSIS_AGENT_NAME` / `CHASSIS_AGENT_EMAIL`.
Unknown/read-only callers are refused after reading only policy, before record,
lock, index, or Git access. Scoped writers additionally read the target for scope
preflight. Denied scopes never open the lock/index or invoke Git. Under the lock,
policy and the target are reread and grants are checked again. These are local
authorization checks, not an authentication service or a filesystem sandbox.

Tool handlers are transport-agnostic functions. A thin MCP adapter will expose
them through stdio. No model SDK, model credential, HTTP server, or agent spawning
is required. Agent templates remain files; their default permission is read-only.

## C6: writes, human edits, and the index

`RecordStore(root)` in `chassis.store` exposes `update_record(id, changes,
expected_version, agent)`, `create_record(type, fields, agent)`, and
`commit_human(path)`. The root must be an initialized Git repository with a HEAD.
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

Success returns `{"record": <full record plus body>, "commit": <SHA>}`. A stale
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
`uncommitted human edit`. The guard checks staged/unstaged changes and compares
content with HEAD even when Git index flags hide changes from status.
`chassis commit-human <path>` validates and commits only the selected record as
`CHASSIS_HUMAN_NAME` / `CHASSIS_HUMAN_EMAIL`, then refreshes the index. It preserves
the manual file bytes, including its version, and cannot commit policy/nonrecord
paths. Clear assume-unchanged/skip-worktree flags first if the guard names them.

Ordinary editors and external Git commands do not honor Chassis locks. Coordinate
manual editing and reread after the human handoff. File replacement and Git are
not one crash-atomic transaction: a hard exit after replace can leave a complete,
uncommitted record for explicit recovery. A hard exit before replace leaves the
original intact and can leave an unused temp file, which record parsing ignores.
Only Linux/POSIX execution has been verified; native Windows locking is not provided.
The index remains disposable and reads working-tree edits, including uncommitted ones.

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

All results contain the full normalized record plus unchanged Markdown `body`.
Lists and searches use ascending ID order. `sensitivity` is always present;
restricted records remain readable here. Renderer filtering belongs to C2.

Filters are case-sensitive exact matches on type, venture, status, parent,
assigned_agent, and sensitivity, combined with AND. Omission means no constraint.
`None` matches null parent/assignment; CLI `null` has that meaning for those two
options. Unsupported filter fields or value types raise `ValueError`. No-match
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
indexes rebuild automatically. Schema version 2, column order, SQLite quick_check,
record JSON, and row-content digests detect cache damage; a read rebuilds and
retries once. Locked databases and other storage errors are reported, not treated
as corruption. Cache symlinks are rejected. Invalid sources never yield old data.

Each read costs a full source-byte scan plus graph validation. Rebuilds serialize
an in-memory SQLite database through the same atomic writer. This is an explicit
local-increment tradeoff, not a large-vault performance claim. The shared lock
coordinates Chassis operations but cannot provide an atomic snapshot across
multiple files edited concurrently by ordinary editors.

## C7: review and delivery

Use tests first and approximately 150-line increments. Commit and push each
completed increment to the private repository, preserving existing repository
instructions and work. Never force-push. Secrets come from the environment;
`.env` stays ignored. Report delivery, verification, open risks, and the next step.
