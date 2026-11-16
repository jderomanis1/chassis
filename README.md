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

**This checkout delivers Steps 1 and 2 of Increment 0: validated records and local reads.**
All venture data is fictional. SQLite is a disposable index of working-tree files.
Record mutations, MCP, templates, and Miro remain in their approved later steps.

**Continuing in a new chat?** Read the [project handoff](CHASSIS_PROJECT_HANDOFF.md)
and [project chat setup](docs/PROJECT_CHAT_SETUP.md). Engineering agents should
start with [AGENTS.md](AGENTS.md).

## Start here

Prerequisites: **Python 3.12+, Git, and uv**. No runtime API key is needed for Steps 1–2.

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

Read commands return stable JSON with every record field plus `body`. Results
are ordered by ID and always include `sensitivity`, including restricted records.
The index is not an access-control layer. Use `--vault /path/to/chassis` on any
new read/index command to select a vault; `validate` retains its positional path.

List filters are exact matches combined with AND: `--type`, `--venture`,
`--status`, `--parent`, `--assigned-agent`, and `--sensitivity`. Use `null` for
no parent or an unassigned agent. Search matches a literal, case-insensitive
substring in title, next step, or body; an empty query returns an empty list.
A missing ID returns exit code 1; a list/search with no matches returns `[]`.

Reads detect changed, added, and removed working-tree records automatically.
Deleting `.chassis/index.sqlite` is safe: the next read rebuilds it. Damaged
caches also rebuild. Invalid source records fail with a filename and reason.
See the [read contract](docs/ARCHITECTURE.md#disposable-index-and-read-contract).

**For a visual browse:** open the repository folder as an Obsidian vault and open
[HOME.md](HOME.md). Obsidian is optional; the records are ordinary Markdown.
The actual Obsidian UI check is tracked in the acceptance evidence.

## What works today

| Capability | Current status |
| :--- | :--- |
| One Markdown file per venture, initiative, or task | Implemented |
| Strict frontmatter schema, including sensitivity and assigned agent | Implemented |
| Relationship and dependency validation | Implemented |
| Local validation command and automated tests | Implemented |
| Fictional sample vault | 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| Agent policy validation | Strict grants and known assignment IDs; write enforcement is Step 3 |
| Disposable SQLite and list/get/search | Implemented, including automatic refresh and recovery |
| MCP, Git-backed record mutations, templates, and Miro | Planned in the approved build order |

## Explore the sample

| Venture | Focus | Initiatives | Tasks |
| :--- | :--- | ---: | ---: |
| Ridgeview HOA | Maintenance planning and resident communication | 2 | 5 |
| Acme D2C | Preparing a first product launch | 1 | 3 |

Both sample dependencies belong to Ridgeview HOA, ready for the later Miro proof.
Names, owners, plans, and records are demonstration data.

## Design commitments

- **Files carry the truth.** YAML frontmatter and Markdown stay readable without a service.
- **History stays explicit.** Record writes will use version checks and attributed Git commits.
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
| `records/` | Authoritative ventures, initiatives, and tasks |
| `agents.yaml` | Agent access policy |
| `src/chassis/` | Schema, parsing, policy validation, index, and local commands |
| `tests/` | Tests of the implemented behavior |
| `docs/` | Architecture and project presentation |
| `evidence/` | Acceptance status and recorded checks |
| `render/miro/` | Tracked board mappings for the later renderer |
| `.chassis/` | Ignored, disposable `index.sqlite` and rebuild temporary files |

## Next in the build

Step 3 starts only after Joe's go: safe record mutations, permissions, version
checks, attributed Git commits, and `commit-human`. Templates and MCP follow.
A scratch-board contract probe precedes layout,
Miro rendering, and the complete read → write → render acceptance demo.

Keep secrets in environment variables. `.env` is ignored; `.env.example`
documents the configuration contract for later steps.

---

**Project owner: Andy Patterson.** See [OWNERSHIP.md](OWNERSHIP.md).
