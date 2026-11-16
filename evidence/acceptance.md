# Acceptance evidence

**Snapshot:** Increment 0, Step 4 complete. **Date:** 2026-11-16.
All source records and people are fictional. AC3, AC4, and AC9 pass; later gates remain pending.

## Step 4 executed checks

Start: accepted `main` at **`9774ed4cbdca94f6a9724318b733a08cd9ff88f0`**.
Part A was published separately as **`9f0259917fedb3ed503e549e6da6975997497577`**.
Implementation checkpoint: **`176478a0ae56c718c2683fd5fb5f885a15554508`**.
The uploaded handoff was the older Step 1 snapshot; current repository instructions
and Joe's accepted Step 3 checkpoint governed. The 236-test baseline was rerun and passed.

Final verification used a fresh detached Git worktree at the implementation SHA,
with neither `.venv` nor `.chassis` present initially. Python was 3.12.14 on Linux.
Subsequent commits update documentation only and retain the tested runtime tree.

| Check | Observed result |
| :--- | :--- |
| `uv sync --locked` | Passed from the clean checkout; no dependency or lock changes |
| `uv run pytest -q` | **343 passed in 13.83s**, including the real-process race and crash regressions |
| `uv run chassis validate` | 13 records, 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| `uv run chassis index rebuild` | Indexed all 13 original working-tree records |
| Source/history boundary | Clean checkout status empty; original records, `agents.yaml`, `pyproject.toml`, and `uv.lock` unchanged from `9774ed4` |
| A1 flag-aware refusal | Real `git update-index` sets `S`/`h`; unchanged flagged targets raise `DirtyRecordError` with filename, exact phrase, and flag advice before write/commit; normal `H` passes |
| A2 human handoff | `commit-human` shares the flag/hash check; flagged clean and edited files are refused; a forced-clean status response still allows the real content hash to detect a human edit |
| A3 authorization ordering | Both current and proposed venture scopes are checked from frontmatter before body reads; denied callers/scopes retain the established I/O boundaries |
| A4 atomic event assertion | The test requires the exact `sync`, `replace`, `sync` sequence |
| AC4 initiative | All six exact GTM sections are populated in order, version is 1, parent/venture agree, and one attributed record-only commit matches the index |
| Invalid sections | Every GTM field is tested missing, empty, and unresolved; source/cache bytes and HEAD remain unchanged |
| Template integrity | Invalid names/order, wrong-section tokens, markup-only values, unresolved markers, and body/parent overrides are refused |
| Read-only agent document | Creation leaves policy byte-identical; the new ID cannot perform an actual record update; authoring needs an explicit existing `agent: write` grant |
| Unknown template/venture | Unknown/path-traversal template names and missing ventures are refused; even an invalid policy grant cannot manufacture a missing venture |
| Unauthorized template caller | Unknown, read-only, and wrong-scope callers read only `agents.yaml`; spies forbid template/record, lock, index, or Git I/O |
| Revoked grant | A grant revoked after expansion is rejected again by the shared create path before the lock |
| CLI | Both `chassis new initiative` and `chassis new agent` create one attributed record; explicit `--vault`, configured callers, usage errors, and content refusals pass |
| AC3 and AC9 retained | Existing concurrency/version/Git and delete/rebuild equivalence proofs remain green |

The 236 existing test cases remain represented. The malformed-type parameter
formerly using `agent` now uses `unknown`, because Step 4 introduces descriptive
agent records. Positive creation, parent validation through the shared graph,
read/query, update, human-commit, and no-grant behavior are exercised for that kind.
The original sample policy and record allocation were not expanded.

### AC4 proof locations

- `tests/test_template_creates.py::test_ac4_template_creation_populates_six_sections_and_commits_once`
  checks headings, every supplied value, parent, version, sole changed file, author,
  exactly one parent-to-child commit, and identical index payload.
- `tests/test_templates.py` fixes the golden names to `Positioning`, `Audience`,
  `Channels`, `Offer`, `Launch checklist`, and `Success metrics`, in that order.
- `tests/test_template_creates.py` verifies no-write refusals for every section,
  unknown template/venture, and policy-only I/O for denied callers.
- `tests/test_agent_templates.py::test_agent_document_created_from_template_grants_no_access`
  checks fixed read-only text, unchanged policy, and an actual refused write as the new ID.
- `tests/test_template_cli.py` and `tests/test_template_guards.py` cover CLI routing,
  structural integrity, grant injection, and authorization rechecks.
- `tests/test_review_fixes.py` contains the live Git flag and body-access regressions.

### Installed CLI proof

The clean checkout's installed `.venv/bin/chassis` ran from a different working
directory against a separate disposable fictional Git repository. The fixture
explicitly provisioned the author's agent-document grant to represent a separate
human policy edit; template creation itself made no policy changes.
Observed results:

- Created one initiative with all six populated sections in order and one agent
  document with the fixed read-only notice; each produced one record-only commit
  authored by `Fictional Homer <homer@chassis.local>`.
- Both returned records matched subsequent installed `get` output and version 1.
- An update attempted as the new agent ID returned `unauthorized` without a commit.
- Missing, empty, and unresolved `Offer` values were refused; cache bytes and HEAD
  remained unchanged. Policy bytes stayed unchanged throughout template creation.
- Exactly two successful runtime commits followed the fixture baseline. After
  deleting the cache, the installed CLI rebuilt 15 records and returned both new
  payloads unchanged. The temporary repository ended clean.
- The original clean checkout's records, policy, and dependency lock stayed identical.

### Test-first and publication record

Part A had nine failing regressions before the fix. Initiative tests failed on
the absent module; four agent-template checks and 29 create-entry-point checks
failed before their implementations. All nine CLI checks failed before `new`
existed. Final review reproduced two misplaced-token cases and an empty numbered
list being accepted; those three regressions failed before the integrity fix.

| Increment | Published commit | Tests after increment |
| :--- | :--- | ---: |
| Part A fixes, separately | `9f02599` | 246 |
| Initiative template expansion | `4cbda44` | 291 |
| Read-only agent documents | `b3fd630` | 295 |
| Shared template-create transaction | `18f96c7` | 323 |
| CLI `new` | `debed11` | 332 |
| Section-placement and empty-content fixes | `176478a` | 343 |

Direct shell Git authentication was unavailable. The connected GitHub API supplied
an exact SHA-verified shallow checkout and published each completed increment with
its expected parent and no force. Remote trees and commit objects matched local
Git objects; previous history was preserved. No runtime code was added for the
portal, MCP, layout, Miro, or chat import. No UI, real MCP-client, portal, or live
Miro check is claimed.

The portal roadmap and health-field decisions are in the architecture and handoff.
Step 5 starts only after Joe's go.

## Step 3 executed checks

Start: accepted `main` at **`f8856e757168cf55a1d522ada9077293b63d0be7`**.
Part A was published separately as **`cdc6532ebbeecb35a3872bdf9bf9c8a80204250a`**.
Implementation checkpoint: **`24ddcc790a228a822bb6b4b57829302116211811`**.
Verification used a fresh detached worktree at that commit, initially without an
environment or cache. Python was 3.12.14 on Linux. Later commits update documentation.

| Check | Observed result |
| :--- | :--- |
| `uv sync --locked` | Passed from the clean checkout; committed lock unchanged |
| `uv run pytest -q` | **236 passed in 9.12s**; all Step 2 tests retained |
| `uv run chassis validate` | 13 records, 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| `uv run chassis index rebuild` | All 13 authoritative working-tree records indexed |
| Clean tree and source preservation | `git diff --exit-code` passed; status empty; records, policy, and dependency lock unchanged from the accepted baseline |
| Ignore boundary | `.chassis/index.sqlite` ignored; `git ls-files .chassis` empty |
| A1 atomic primitive | Exclusive interprocess lock; sibling temp file fsynced before replacement; original survives an injected pre-replace crash; normal failures clean the temp |
| A2 policy references | Nonexistent venture IDs and task IDs used as ventures rejected with policy path/reason |
| A3 rename | New filename and ID replace the old source; old ID/path disappear from the cache; new row has the new path |
| A4 precise assertions | Golden ID lists replace count/order-only checks; invalid sources leave an existing cache byte-identical or an absent cache absent |
| AC9 retained | All prior library and CLI delete/rebuild equivalence tests remain green |

### AC3 and required mutation proofs

All Git mutation tests use temporary repositories populated only with fictional
records. Development commits in this repository are not the evidence for record
attribution; the tests inspect commits actually created by the runtime methods.

| Required test | Observed result and executable proof |
| :--- | :--- |
| T1: two real writers | `tests/test_concurrency.py::test_ac3_two_real_processes_same_version_have_one_winner_and_one_commit`: two OS processes race expected version 1; exactly one succeeds, one gets conflict/current version 2; exactly one new commit; file, index, commit contents, and author match the winner |
| T2: stale version | `tests/test_updates.py::test_stale_version_returns_current_version_without_file_cache_or_commit_change`: source and cache bytes plus HEAD unchanged; structured conflict includes current version 2 |
| T3: successful update | `tests/test_updates.py::test_good_update_bumps_once_commits_only_target_as_agent_and_refreshes_index`: version increments by exactly 1, timestamp advances, body preserved, one record-only commit uses configured agent author, unrelated staging unchanged |
| T4: immutable fields | `tests/test_updates.py::test_immutable_update_preserves_file_and_git_history`: id/version/updated_at attempts rejected; source and HEAD unchanged; no lock/cache directory created |
| T5: human edits | `tests/test_human_commits.py::test_dirty_refusal_then_human_commit_allows_agent_update`: staged and unstaged edits refused with filename and exact phrase; explicit human commit preserves manual bytes and uses human author; subsequent agent update succeeds |
| T6: authorization | `tests/test_write_permissions.py`: unknown/read-only callers read only policy, with record-open/Git/lock spies forbidding other I/O; denied current/destination scopes never open lock/index or Git; Acme normal and restricted records follow the same grant rule |
| T7: pre-replace crash | `tests/test_atomic.py::test_crash_before_replace_preserves_original` plus `tests/test_concurrency.py::test_process_crash_before_replace_preserves_source_head_cache_and_releases_lock`: forced OS-process exit leaves original source complete, cache/HEAD unchanged, and the lock available to a subsequent writer |
| T8: create rejection | `tests/test_creates.py`: duplicate IDs, missing parents/dependencies, self-dependencies, multi-record cycles, invalid schema/assignment, and supplied version/timestamp rejected without source/cache/HEAD changes |

Additional executed checks cover CLI JSON outputs and exit codes, explicit vault
selection, malformed manual edits, canonical record-only human paths, configured
identities, invalid updates, and policy revocation between preflight and lock entry.
Real failing pre-commit hooks prove rollback for both create and update. An injected
cache failure after a successful commit reports `committed: true` and the actual
SHA/version instead of claiming a rollback. A content check rejects human edits
hidden by Git's assume-unchanged/skip-worktree flags.

### Installed CLI proof

The clean checkout's installed `.venv/bin/chassis` was run against a separate,
temporary Git repository, with fictional agent/human identities. Observed:

- Agent update: version 1 to 2; one attributed record commit.
- Stale retry: exit 3, `error: conflict`, `current_version: 2`, unchanged HEAD.
- Create initiative: version 1; new record and cache entry match.
- Dirty update: exit 1 with `dirty_record`; unchanged HEAD and preserved manual edit.
- Human commit: author `Fictional Human <human@chassis.local>`; only the selected record.
- Agent update after human handoff: version 2 to 3; manual body note preserved.
- Exactly four successful runtime commits, each touching only its selected record;
  temporary repository clean afterward; index results match the sources.
- The clean checkout's original record and policy bytes remained identical.

### Test-first and publication record

New atomic/policy tests failed before implementation. Git, proposed-validation,
transaction, and store tests failed on the absent modules/functions. Create,
human-commit, and CLI tests failed before those entry points existed. Scoped-denial
tests exposed an early lock open; the preflight fix made them pass. Final review
regressions exposed hidden dirty edits before the content-hash guard was added.

The two-process and transaction-crash acceptance tests passed against the real
lock and write implementation. No MCP client, UI, Miro API, live venture, or
deployment check was run or claimed in Step 3.

| Increment | Published commit | Tests after increment |
| :--- | :--- | ---: |
| Part A fixes, separately | `cdc6532` | 162 |
| Policy/error contract | `1d81880` | 168 |
| Git identity and single-file commits | `bf9ef89` | 174 |
| Proposed graph validation/serialization | `8a4d905` | 179 |
| Persistence and failure recovery | `a74dfde` | 182 |
| Versioned update | `d332f28` | 187 |
| Create | `a457f29` | 198 |
| Human commit | `6fe5a10` | 205 |
| Scoped authorization preflight | `abd3ac9` | 215 |
| Real-process AC3 and crash proof | `50db1b6` | 217 |
| CLI write commands | `ec5f84f` | 224 |
| Hidden dirty-edit guard and final regressions | `24ddcc7` | 236 |

Direct Git authentication was unavailable. The connected GitHub API verified the
starting main, published each completed increment with its expected parent and no
force, and returned Git objects checked against the staged tree and reconstructed
commit SHA. The uploaded handoff was an older Step 1 snapshot; the accepted
repository checkpoint governed Step 3. No existing work or history was replaced.

This is the historical Step 3 checkpoint. Step 4 evidence and the current gate are above.

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
| 3 | Stale write rejection, version bump, Git commit | **Passed Step 3** at `24ddcc7`: two real processes, exactly one commit, structured stale rejection, agent attribution, and installed CLI proof |
| 4 | Filled initiative template | **Passed Step 4** at `176478a`: six populated sections, shared transaction, one attributed commit, library and installed CLI proof |
| 5 | Ridgeview rendered on Miro | Pending optional Miro export in revised Step 8 |
| 6 | MCP status update changes one card | Pending Step 5 and optional Miro export in Step 8 |
| 7 | Unchanged render has zero writes | Pending planner Step 7 and optional Miro export Step 8 |
| 8 | Delete-frame behavior observed | Pending optional Step 8 scratch probe; no result has been inferred |
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
This was the Step 2 checkpoint. Step 3 evidence and the next gate are recorded above.
