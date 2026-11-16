# Chassis architecture

## Current boundary

Step 1 implements the source-record schema, safe parsing, relationship validation,
fictional records, and `chassis validate`. Everything described as a later contract
below is planned, not implemented. All Chassis execution stays local; the later
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
Record tools cannot edit the policy file. Step 1 commits the policy scaffold only.

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
in Step 1. Ordinary editors do not honor Chassis locks; concurrent manual editing
requires coordination. The disposable SQLite index reads working-tree files,
including uncommitted edits. Rebuilds must reproduce identical query results.

## C7: review and delivery

Use tests first and approximately 150-line increments. Commit and push each
completed increment to the private repository, preserving existing repository
instructions and work. Never force-push. Secrets come from the environment;
`.env` stays ignored. Report delivery, verification, open risks, and the next step.
