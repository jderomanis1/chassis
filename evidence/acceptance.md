# Acceptance evidence

**Snapshot:** Increment 0, Step 2 complete. **Date:** 2026-11-16.
All source records and people are fictional. AC9 passes; later gates remain pending.

## Step 2 executed checks

Implementation commit: **`39b5b2ee2efbdc272fdd33b479a4884c6b65cfc7`**.
Verification used a fresh detached Git worktree at that commit, initially without
an environment or index. Python was 3.12.14. Subsequent commits update documentation.

| Check | Observed result |
| :--- | :--- |
| `uv sync --locked` | Passed in the clean checkout; committed lock unchanged |
| `uv run pytest -q` | **151 passed** in the clean checkout; all prior tests retained |
| `uv run chassis validate` | 13 records, 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| `uv run chassis index rebuild` | Indexed all 13 working-tree records |
| S1 policy and assignment validation | Invalid grants, unknown assignments, invalid/missing policy, duplicate keys, and unsafe tags rejected with file/reason |
| N1/N2 rejection assertions | Unsafe tag checks the constructor error; field rejection tests match the field; existing parser failures match their cause |
| AC9 library proof | 15 fixed queries serialize to identical UTF-8 bytes after database deletion and rebuild |
| AC9 CLI proof | Six command outputs are byte-identical after deletion/rebuild, both in subprocess tests and an installed-entry-point check |
| Filters | All six fields, combined AND filters, no-match scopes, null parents, and null assignments pass |
| Search | Title-only, next-step, body, Unicode case folding, blank, literal wildcard characters, and non-match cases pass |
| Working-tree refresh | Every read detects edits, including same-size edits with restored mtime; additions, removals, and mtime-only changes pass |
| Source failures | Invalid files and broken relationships block reads with filenames; no silent skip or stale answer |
| Cache recovery | Missing, non-SQLite, truncated, wrong schema/version, invalid JSON, and damaged valid values recover from source |
| Restricted records | Returned by list/get/search with sensitivity; no filtering or caller authorization implemented here |
| Storage boundary | An actual exclusive SQLite lock is reported; cache symlinks are rejected |
| Source preservation | Record and policy bytes unchanged by CLI/rebuild proof; clean checkout remained clean after execution |
| Ignore rule | `git check-ignore .chassis/index.sqlite` passed; `git ls-files .chassis` was empty |

The fixed library proof is
`tests/test_index.py::test_delete_rebuild_produces_byte_identical_results`.
It covers all records, a restricted get, a missing get, matching/non-matching
searches, and the nine individual/combined/null filter cases. The CLI proof is
`tests/test_index_cli.py::test_cli_queries_are_byte_identical_after_delete_and_rebuild`.
It covers list, a combined six-field filter, null parent, restricted get,
next-step search, and no-match search.

The installed CLI check used the same six commands and compared actual stdout
bytes. SHA-256 of the six outputs joined by NUL bytes was:
`1f9bc7a4022f80f7cb630cb4d304bdb8d0f67969067d5204baf901ef95134911`.

Tests for the review fixes failed before policy implementation. The initial index
tests failed on the absent module. Filters/search, refresh, recovery, and CLI
tests failed before their corresponding implementations. Final review added four
regressions for altered cached values that still passed SQLite quick_check; all
four failed before row-content digests were added and now pass.

No record mutation, MCP-client, UI, Miro, or deployment check was run in Step 2.

## Step 1 baseline checks (historical)

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
| 9 | SQLite deletion/rebuild preserves query results | **Passed Step 2**, library and installed CLI byte-equivalence proofs at `39b5b2e` |

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

## Published Step 2 increments

Start-of-chat `main` was `f6b7ee6`, two documentation-only commits ahead of the
reviewed Step 1 baseline `7274934`. The uploaded handoff matched the repository.
Both migration commits were preserved. Direct Git authentication was unavailable;
the connected GitHub API retrieved the checkout and published each increment.
Downloaded blobs, source tree, and local commit objects were checked against
their GitHub SHAs. Ref updates used the expected parent and no force push.

| Increment | Commit | Scope | Tests after increment |
| :--- | :--- | :--- | ---: |
| Review fixes | `9f2dc28` | S1 policy validation, N1/N2 assertions | 81 |
| 2.1 | `e70f62d` | Atomic rebuild, list/get, initial AC9 proof | 83 |
| 2.2 | `a62c6b5` | Filters, search, expanded AC9 queries | 107 |
| 2.3 | `3255544` | mtime/hash refresh, additions/removals, source failures | 119 |
| 2.4 | `ff56a70` | Missing/corrupt cache recovery and storage errors | 141 |
| 2.5 | `8360446` | CLI commands and byte-output proof | 146 |
| 2.6 | `39b5b2e` | Row-content integrity and timestamp-only proof | 151 |
| Documentation | `28c0a57` | Read contract, usage, and observed findings | No runtime changes |

Each implementation increment was pushed after its tests passed. Hand-authored
diffs ranged from 64 to 128 lines. The final evidence/handoff documentation follows.
Next: Step 3 only after Joe's go; see `CHASSIS_PROJECT_HANDOFF.md` for its prompt.
