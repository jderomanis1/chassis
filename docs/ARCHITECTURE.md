# Chassis architecture

## Current boundary

Steps 1–2 implement the source-record schema, safe parsing, relationship and policy
validation, fictional records, and a disposable SQLite read index. Commands are
`validate`, `index rebuild`, `list`, `get`, and `search`. Later contracts below
remain planned, not implemented. All Chassis execution stays local; the later
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
Record tools cannot edit the policy file. Step 2 validates policy shape with
Pydantic and rejects unknown assignment IDs. Caller authentication and write-time
authorization remain in Step 3; valid assignment metadata never authorizes a write.

Tool handlers are transport-agnostic functions. A thin MCP adapter will expose
them through stdio. No model SDK, model credential, HTTP server, or agent spawning
is required. Agent templates remain files; their default permission is read-only.

## C6: writes, human edits, and the index

The later write path locks, rereads the file, checks permissions and version,
validates changes, atomically replaces, and commits only the target record.
Failed commits must not produce false success. The agent identity comes from
process configuration. Unrelated changes must never enter a record commit.

A dirty target is refused with its filename and the exact phrase
`uncommitted human edit`. `chassis commit-human <path>` will commit an explicitly
selected path as `CHASSIS_HUMAN_NAME` / `CHASSIS_HUMAN_EMAIL`. It is not available
in Steps 1–2. Ordinary editors do not honor Chassis locks; concurrent manual editing
requires coordination. The disposable SQLite index reads working-tree files,
including uncommitted edits. Rebuilds must reproduce identical query results.

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

Each read costs a full source-byte scan plus graph validation. This is an explicit
local-increment tradeoff, not a large-vault performance claim. Reads do not provide
an atomic snapshot across concurrent edits to multiple files. Write locking and
version control remain Step 3 work.

## C7: review and delivery

Use tests first and approximately 150-line increments. Commit and push each
completed increment to the private repository, preserving existing repository
instructions and work. Never force-push. Secrets come from the environment;
`.env` stays ignored. Report delivery, verification, open risks, and the next step.
