# Acceptance evidence

**Snapshot:** Increment 0, Step 1. **Date:** 2026-11-16.
All source records and people are fictional. Later acceptance criteria are pending.

## Executed checks

| Check | Result |
| :--- | :--- |
| `uv sync --locked` | Passed with the committed dependency lock |
| `uv run pytest -q` | 72 passed |
| `uv run chassis validate` | 13 records, 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| Malformed records | Required fields, unsafe IDs, strict versions, timestamps, optional fields checked |
| YAML and Markdown | Duplicate keys and unsafe tags rejected; body text and Windows line endings preserved |
| Relationships | Invalid parents, venture mismatch, missing dependencies, duplicate IDs, self-dependencies, cycles rejected |
| CLI | Working-tree edits read; failures have filenames and no traceback for covered cases |
| Sample allocation | Ridgeview: 2 initiatives, 5 tasks, 2 dependencies; Acme: 1 initiative, 3 tasks |
| Restricted sample | One explicitly fictional Acme record; renderer exclusion is not implemented yet |
| Repository presentation | SVG parsed, rendered, and visually inspected at 1280 × 360 |
| Configuration | Obsidian app configuration parses; `.env` ignored; mapping path is not ignored |
| Credential scan | No environment secrets, private-key headers, or common GitHub token patterns in tracked files |

Tests were written and run before their corresponding implementation. The record,
parser, graph, and CLI tests first failed on the absent implementation. Sample-data
assertions failed before adding the records. Independent review found numeric
timestamp strings being coerced to Unix time; four regression cases failed before
the fix and now pass.

## Acceptance matrix

| AC | Requirement | Status and evidence |
| :--- | :--- | :--- |
| 1 | Obsidian vault and valid records | All records validate. Actual Obsidian open-and-browse check pending; see below. |
| 2 | MCP client list/read/create/update | Pending Step 5 |
| 3 | Stale write rejection, version bump, Git commit | Pending Step 3 |
| 4 | Filled initiative template | Pending Step 4; the sample initiative is not template-engine evidence |
| 5 | Ridgeview rendered on Miro | Pending Steps 6–9 |
| 6 | MCP status update changes one card | Pending Steps 5–9 |
| 7 | Unchanged render has zero writes | Pending Steps 7–9 |
| 8 | Delete-frame behavior observed | Pending Step 6; no result has been inferred |
| 9 | SQLite deletion/rebuild preserves query results | Pending Step 2 |

## Obsidian demo status

The application was initially absent. An official local copy was downloaded for
verification outside the repository, without disabling its sandbox. The desktop
launch did not produce an observable Obsidian window, so this is **not a UI pass**.
No account, plugin, subscription, or proprietary extension is required by the vault.

Remaining demo: open this repository as a folder vault, open `HOME.md`, follow a
venture and task link, and inspect YAML properties and a dependency. Record the
app version and screenshot. No error dialog should appear.

## Published increments

GitHub access was initially unavailable. Once access was restored, the initial
README commit was preserved and prepared increments were published in order to
the private repository's `main` branch. No force push or repository visibility
change was used. Development commits identify Codex and include agent co-authorship.

| Increment | Remote commit | Scope |
| :--- | :--- | :--- |
| 1.1 | `8cf3af1` | Required fields and optional sensitivity/assignment |
| 1.2 | `7806346` | Safe Markdown frontmatter parsing |
| 1.3 | `951028c` | Relationship and dependency validation |
| 1.4 | `f8f2200` | Working-tree validation command |
| 1.5 | `b402e5b` | Venture fixtures and policy scaffold |
| 1.6 | `bc88553` | Ridgeview tasks and dependencies |
| 1.7 | `9db3e34` | Complete Acme sample and restricted fixture |
| 1.8 | `4d059f0` | Numeric timestamp regression fix |
| 1.9 | `91e0747` | Vault navigation and approved contracts |
| 1.10 | `f5574b6` | README and visual identity |

Ordinary increments contain 116–157 hand-authored lines; the focused timestamp
fix is seven lines. The generated dependency lock is additional to those counts.
The commit containing this evidence is the following documentation increment.
