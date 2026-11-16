<p align="center">
  <img src="docs/assets/chassis-banner.svg" alt="Chassis: keep the work connected. Venture, initiative, and task records form the foundation." width="100%">
</p>

<p align="center">
  <strong>One place to understand the work. One foundation for moving it forward.</strong>
</p>

<p align="center">
  <a href="#start-here">Start here</a> ·
  <a href="#what-works-today">Current build</a> ·
  <a href="docs/ARCHITECTURE.md">Architecture</a> ·
  <a href="evidence/acceptance.md">Acceptance evidence</a>
</p>

Chassis is Andy Patterson’s command foundation for running parallel ventures.
Its goal is a shared project state that a chief-of-staff agent can read and update,
with a spatial view that makes the next action easy to see.

**This checkout delivers Steps 1–5 of Increment 0: validated records, reads, local writes, templates, and MCP.**
All venture data is fictional. SQLite is a disposable index of working-tree files.
Six MCP tools run over stdio. The portal, layout planner, optional Miro export, and chat import follow.

**Continuing in a new chat?** Read the [project handoff](CHASSIS_PROJECT_HANDOFF.md)
and [project chat setup](docs/PROJECT_CHAT_SETUP.md). Engineering agents should
start with [AGENTS.md](AGENTS.md).

## Start here

Prerequisites: **Python 3.12+, Git, uv, and a POSIX environment**. Step 5 was verified
on Linux; native Windows locking is not implemented. No runtime API key is needed.

```bash
git clone https://github.com/jderomanis1/chassis.git
cd chassis
uv sync --locked
uv run pytest -q
uv run chassis validate
uv run chassis index rebuild
uv run chassis list --venture venture-ridgeview --status blocked
uv run chassis get task-launch-budget
uv run chassis search "three most repeated"
```

Already have a checkout? Start with `uv sync --locked` from its root.
Validation reads the Markdown files in the working tree.

Read commands return stable JSON with every record field plus `body` and derived `last_activity_at`. Results
are ordered by ID and always include `sensitivity`, including restricted records.
The index is not an access-control layer. Use `--vault /path/to/chassis` on any
new read/index command to select a vault; `validate` retains its positional path.

List filters are exact matches combined with AND: `--type`, `--venture`,
`--status`, `--parent`, `--assigned-agent`, `--sensitivity`, `--next-milestone`,
`--milestone-due-at`, `--due-at`, `--blocker-reason`, and `--last-activity-at`.
Use `null` for any optional filter, including no parent or an unassigned agent.
Date filters take `YYYY-MM-DD`; activity filters match the returned UTC timestamp exactly.
Search matches a literal, case-insensitive
substring in title, next step, or body; an empty query returns an empty list.
A missing ID returns exit code 1; a list/search with no matches returns `[]`.

Reads detect changed, added, and removed working-tree records automatically.
Deleting `.chassis/index.sqlite` is safe: the next read rebuilds it. Damaged
caches also rebuild. Invalid source records fail with a filename and reason.
See the [read contract](docs/ARCHITECTURE.md#disposable-index-and-read-contract).

### Write a fictional record

Writes require a configured caller with an exact venture/type grant in `agents.yaml`.
Use a local checkout of the sample vault and set the author identity explicitly:

```bash
export CHASSIS_AGENT_ID=chief-of-staff
export CHASSIS_AGENT_NAME="Fictional Homer"
export CHASSIS_AGENT_EMAIL=homer@chassis.local
uv run chassis get task-launch-budget
uv run chassis update task-launch-budget --expected-version 1 --changes '{"status":"blocked","blocker_reason":"Waiting for fictional review"}'
uv run chassis create task --fields '{"id":"task-fictional-review","title":"Review the fictional launch","status":"planned","owner":"Example Owner","venture":"venture-acme","parent":"initiative-d2c-launch","next_step":"Review the sample plan","body":"Fictional sample only.\n"}'
```

Use the version returned by `get`. Successful writes return the complete record
and commit SHA, commit only that file as the agent, and refresh the index. A stale
write returns exit 3 and a JSON conflict with `current_version`, without changing
the record or history. Version and timestamp are generated; callers cannot change
ID, version, or timestamp on updates. New venture scopes require human provisioning.

Manual edits block agent writes with the filename and `uncommitted human edit`.
Commit an explicitly selected manual edit with the human identity, then reread it:

```bash
export CHASSIS_HUMAN_NAME="Fictional Human"
export CHASSIS_HUMAN_EMAIL=human@chassis.local
uv run chassis commit-human records/tasks/task-launch-budget.md
uv run chassis get task-launch-budget
```

`commit-human` validates and commits the manual bytes, including their version,
without rewriting them. It cannot commit `agents.yaml` or other nonrecord files.
All three commands accept `--vault`. Library callers use the same methods on
`chassis.store.RecordStore(Path(...))`; MCP uses these same methods.
See [write behavior and recovery limits](docs/ARCHITECTURE.md#c6-writes-human-edits-and-the-index).

### Create from a template

With the fictional caller identity above, run:

```bash
uv run chassis new initiative --venture venture-acme --fields '{
  "id": "initiative-sample-launch",
  "title": "Fictional desk-kit pilot",
  "owner": "Avery Quinn",
  "next_step": "Review the fictional launch plan.",
  "sections": {
    "Positioning": "A compact kit for a small desk.",
    "Audience": "Fictional remote workers with small desks.",
    "Channels": "A draft product page and an opt-in sample email.",
    "Offer": "One illustrative starter kit.",
    "Launch checklist": "- [ ] Review ten fictional interviews.",
    "Success metrics": "Sample target: three expressions of interest."
  }
}'
```

The six case-sensitive section names and their order are fixed in `GTM_SECTIONS`.
Every section needs content. Missing values, blanks, markup-only lists, unresolved
`{{...}}`/`${...}` tokens, TODO/TBD/TBC/FIXME/XXX/PLACEHOLDER markers, and insert/replace/fill
markers in brackets are refused. An edited template must retain its headings,
order, and each section's own placeholder. Matching uses Unicode NFKC normalization
to detect compatibility forms such as fullwidth letters. Accepted prose is preserved.
Caller owner, sensitivity, and assignment are checked against the record constraints
before expansion, then revalidated through the shared create transaction.
Expansion does not evaluate code.

`RecordStore(root).create_from_template(template, venture, fields, agent)` is the
same library entry point used by `chassis new`. Both delegate to `create_record`:
exact grant check, lock, validation, generated version/time, one record-only Git
commit, and index refresh. `status` defaults to `planned`; type, venture, parent,
and body are controlled by the template call. `--vault` selects another vault,
which must also contain the two files in `templates/`.

`chassis new agent` takes the same record fields with `sections` named `Playbooks`,
`Channels`, and `Data scope`. It adds the fixed read-only `Permissions` section.
The result is a descriptive file at `records/agents/<id>.md`, parented to its
venture. It neither spawns nor registers an agent and never changes `agents.yaml`.
Its ID remains read-only unless a human explicitly configures grants there.

Authoring an agent document is itself scoped: a human must add `agent: write`
under the existing author's venture policy. The sample policy is unchanged and
contains no such grant. This permits document creation, not writes by the new
document's ID. `assigned_agent` continues to require a known policy agent ID.

### Approved portal data fields

| Records | Optional fields | Rule |
| :--- | :--- | :--- |
| Ventures and initiatives | `next_milestone`, `milestone_due_at` | Milestone text and an ISO date, `YYYY-MM-DD` |
| Tasks | `due_at`, `blocker_reason` | ISO due date; a blocked task requires a nonempty reason; other statuses require an empty/null reason |
| All read results | `last_activity_at` | Derived from the latest commit touching the record on the current HEAD's history, using UTC committer time |

Omitted optional fields remain valid on older records. A legacy blocked task needs
a reason under the new invariant; the fictional Ridgeview task has been migrated.
To unblock a task, clear `blocker_reason` in the same update. Dates reject timestamps
and numeric coercion. `last_activity_at` is never written into frontmatter. It is
null for records with no commit history, and uncommitted edits do not advance it.
The index recomputes activity even when source bytes and mtime have not changed.
No health calculation or colors are implemented.

### Connect an MCP client

Run `uv sync --locked` in the checkout first. The installed entry point is
`.venv/bin/chassis-mcp`; `uv run chassis-mcp --vault /path/to/sample-vault` and
`uv run python -m chassis.mcp_server --vault /path/to/sample-vault` also start it.
The process waits for JSON-RPC on stdin. Only protocol messages go to stdout;
logs go to stderr. There is no listening HTTP endpoint.

For Claude Desktop, merge an entry like this into `claude_desktop_config.json`.
Replace every placeholder with local sample-vault configuration. The format follows
the [official MCP client guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

```json
{
  "mcpServers": {
    "chassis": {
      "command": "/ABSOLUTE/PATH/TO/chassis/.venv/bin/chassis-mcp",
      "args": ["--vault", "/ABSOLUTE/PATH/TO/FICTIONAL-VAULT"],
      "env": {
        "CHASSIS_AGENT_ID": "CONFIGURED_POLICY_AGENT_ID",
        "CHASSIS_AGENT_NAME": "CONFIGURED_AGENT_NAME",
        "CHASSIS_AGENT_EMAIL": "agent@example.invalid"
      }
    }
  }
}
```

Restart the client after editing its configuration. `--vault` can instead be set
through `CHASSIS_VAULT`; it defaults to the server's working directory. Caller ID
comes from `CHASSIS_AGENT_ID`, and Git attribution comes from `CHASSIS_AGENT_NAME`
and `CHASSIS_AGENT_EMAIL`. These are server configuration, never tool arguments.
Missing/unknown/read-only callers cannot write. Name/email must be valid before
a permitted write. Record owner and `assigned_agent` are descriptive metadata.

| Tool | Arguments | Successful structured content |
| :--- | :--- | :--- |
| `list_records` | Optional `filters` object using the fields above | `{"records": [...]}` |
| `read_record` | `id` | `{"record": {...}}` |
| `search` | `query` | `{"records": [...]}` |
| `create_record` | `type`, `fields` | `{"record": {...}, "commit": "..."}` |
| `create_from_template` | `template`, `venture`, `fields` | `{"record": {...}, "commit": "..."}` |
| `update_record` | `id`, `changes`, `expected_version` | `{"record": {...}, "commit": "..."}` |

Responses include matching JSON text and MCP `structuredContent`. Tool failures
set `isError: true` and an `error` code: `conflict` includes `current_version`,
`unauthorized` and `dirty_record` retain refusal details, `validation` has `field`
and `reason`, and `not_found` identifies a missing record/tool. Storage/Git failures
retain their separate recovery codes. If `committed` is true or unknown, inspect
the result and history before retrying. Raw exception/hook diagnostics stay on stderr.

The stable `.chassis/write.lock` inode remains after shutdown so concurrent
waiters share one lock. Successful shutdown releases the kernel lock, leaves no
Git index lock, and ends the server process. Never delete a lock file to unblock it.
The configuration example has not been exercised in the Claude Desktop UI.
Real raw JSON-RPC and official SDK subprocess clients are verified in
[AC2 evidence](evidence/acceptance.md); the recorded wire session is
[mcp-session.jsonl](evidence/mcp-session.jsonl).

**For a visual browse:** open the repository folder as an Obsidian vault and open
[HOME.md](HOME.md). Obsidian is optional; the records are ordinary Markdown.
The actual Obsidian UI check is tracked in the acceptance evidence.

## What works today

| Capability | Current status |
| :--- | :--- |
| One Markdown file per venture, initiative, task, or agent document | Implemented |
| Strict frontmatter schema, including sensitivity and assigned agent | Implemented |
| Relationship and dependency validation | Implemented |
| Local validation command and automated tests | Implemented |
| Fictional sample vault | 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| Agent policy and write authorization | Strict known venture/type grants; unknown/read-only agents cannot write |
| Disposable SQLite and list/get/search | Implemented, including automatic refresh and recovery |
| Versioned create/update and human commits | Implemented; process lock, atomic files, record-only Git commits |
| Initiative and read-only agent templates | Implemented; AC4 passes through the library and CLI |
| Milestones, task due dates/blockers, and derived Git activity | Implemented; no health calculation |
| Six official SDK MCP tools over stdio | Implemented; AC2 real-client and concurrent-writer proof |
| Portal, layout, optional Miro, chat import | Later steps; portal code requires prototype approval |

## Explore the sample

| Venture | Focus | Initiatives | Tasks |
| :--- | :--- | ---: | ---: |
| Ridgeview HOA | Maintenance planning and resident communication | 2 | 5 |
| Acme D2C | Preparing a first product launch | 1 | 3 |

Both sample dependencies belong to Ridgeview HOA, ready for the later Miro proof.
Names, owners, plans, and records are demonstration data.

## Design commitments

- **Files carry the truth.** YAML frontmatter and Markdown stay readable without a service.
- **History stays explicit.** Record writes use version checks and attributed Git commits.
- **Permissions have a home.** `agents.yaml` defines scoped grants; unknown agents are read-only.
- **Private work stays private.** Restricted records will be excluded from rendered graphs.
- **The canvas can change.** A renderer-neutral graph will keep layout independent of Miro.
- **Board changes stay precise.** Tracked mappings, fingerprints, and pending creates will protect item identity.

These are the build contracts. See [architecture](docs/ARCHITECTURE.md) for the
implementation boundaries and [acceptance evidence](evidence/acceptance.md) for
what has actually been verified.

## Find your way around

| Path | Purpose |
| :--- | :--- |
| `records/` | Authoritative ventures, initiatives, tasks, and agent documents |
| `agents.yaml` | Agent access policy |
| `templates/` | Constrained initiative and agent Markdown templates |
| `src/chassis/` | Schema, parsing, policy, index, write transactions, and local commands |
| `tests/` | Tests of the implemented behavior |
| `docs/` | Architecture and project presentation |
| `evidence/` | Acceptance status and recorded checks |
| `render/miro/` | Tracked board mappings for the later renderer |
| `.chassis/` | Ignored, disposable `index.sqlite` and shared `write.lock`; do not unlink a live lock |

## Next in the build

Step 5 is complete. Next, only after Joe's go, is a read-only command-center portal over the
library and index, with design prototype approval before any portal code.
Layout and change planning follow; Miro becomes an optional export. Chat import
has a separate later step. See the handoff for the sequence and open health/design decisions.

Keep secrets in environment variables. `.env` is ignored; `.env.example`
documents the author identity and later Miro configuration.

---

**Project owner: Andy Patterson.** See [OWNERSHIP.md](OWNERSHIP.md).
