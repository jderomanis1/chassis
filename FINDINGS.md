# Findings

## Step 1: observed

- All 13 fictional records pass schema and relationship validation.
- The working-tree validator sees edits before they are committed.
- Safe YAML loading alone does not reject duplicate keys; Chassis rejects them.
- Pydantic accepted numeric timestamp strings as Unix time. Explicit ISO parsing
  closes that loophole; regression tests cover unsigned, signed, and decimal forms.
- The Obsidian UI check remains unverified after a desktop launch problem.

## Step 2: observed

- Implementation checkpoint: `39b5b2ee2efbdc272fdd33b479a4884c6b65cfc7`.
  Step 1 review fixes were published first, separately, as `9f2dc28`.
- A clean detached checkout passed `uv sync --locked`, all **151 tests**, and
  `chassis validate` for all 13 records. The installed CLI rebuilt 13 records.
- AC9 passed with 15 fixed library queries and six CLI commands. Deleting the
  index and rebuilding produced byte-identical results. Source files were unchanged.
- All six filters, combined filters, null parent/assignment, title/next-step/body
  search, Unicode case folding, and no-match cases passed. Restricted records
  appear in list/get/search with `sensitivity`; no access-isolation claim is made.
- Every read observes additions, edits, and removals. Same-size edits preserving
  mtime still refresh through content hashes; mtime-only changes refresh metadata.
- Invalid source records and broken relationships block reads with a filename.
  Missing or invalid policy also fails validation. Write authorization is pending.
- Missing, non-SQLite, truncated, incompatible-schema, and damaged-payload caches
  rebuild. An actual exclusive SQLite lock is reported without replacing the file.
- SQLite quick_check alone passed after cached body, filter, and JSON values were
  changed. Four regression cases failed before row-content digests were added;
  all now rebuild from source, including restoration of missing sensitivity.
- Reads scan all source bytes and validate the graph. Large-vault performance and
  atomic snapshots across concurrent multi-file edits have not been established.
- The Obsidian UI check remains open. No MCP client, Miro API, deployment, record
  mutation, or live business-account check was run in Step 2.

The preceding observations describe the historical Step 2 boundary.

## Step 3: observed

- Started from accepted `main` at `f8856e7`, confirmed through the connected
  GitHub API. The uploaded handoff described the older Step 1 checkpoint; current
  repository instructions/evidence governed. Part A was published separately as
  `cdc6532`. Final implementation checkpoint: `24ddcc790a228a822bb6b4b57829302116211811`.
- A fresh detached checkout passed `uv sync --locked`, **236 tests**, validation
  of all 13 sample records, and an installed index rebuild. Working tree, source
  record bytes, policy bytes, and dependency lock remained unchanged.
- AC3 passed with two real OS processes using the same expected version: exactly
  one successful write and one structured conflict, one new record-only commit,
  version 2, and matching winner content/author. No simulated scheduler supplied
  this result. Both processes used the real shared lock and Git executable.
- Source/cache replacements now use the single fsynced `atomic.write_atomic`
  path. A forced process exit before replace preserved the original complete
  source, cache, and HEAD; a subsequent update acquired the released kernel lock.
- Stale, immutable, invalid-schema, missing-reference, and cyclic proposals leave
  source/cache bytes and HEAD unchanged. Create validates a complete proposed
  graph, including a cycle involving a new record, before writing.
- Every agent write checks policy before target access and again after acquiring the
  lock. Unknown/read-only callers read policy only; denied scopes perform no lock,
  index, or Git access. Scope preflight necessarily reads the target's actual
  venture/type. Restricted Acme tasks follow the same grant rule as normal tasks.
  Policy revoked between preflight and lock entry is rejected.
- Successful writes preserve unrelated staging, advance version exactly once,
  set timestamps, and use configured agent attribution. Git hooks are honored.
  An actual rejecting pre-commit hook restored original update bytes or removed a
  new file without moving HEAD. A post-commit cache failure reports the actual
  commit and current version, with `committed: true`.
- Final review found that `git status` can hide edits under assume-unchanged or
  skip-worktree. Two tests reproduced this before the content-hash guard; both
  now return `uncommitted human edit` and preserve the target and HEAD.
- `commit-human` validates the vault, commits only the selected record as the
  configured human, and preserves the manually edited bytes. It cannot commit
  permissions or nonrecord paths. It does not generate a new version; callers
  must reread after the explicit manual handoff.
- An installed-entry-point proof created an initiative, performed agent updates,
  refused stale and dirty writes, and committed a human edit. Four successful
  runtime commits each touched one record; the temporary repo ended clean and
  index results matched the files. Source fixtures in the clean checkout were unchanged.
- No template expansion, MCP client, UI, Miro API, deployment, real venture data,
  or live business-account write was run in Step 3.

Step 3 limits: the lock uses POSIX `flock` and has been verified on Linux only.
Ordinary editors and external Git commands do not honor it. File replacement and
Git are separate operations: a hard crash after replacement can leave a complete
uncommitted record requiring explicit recovery. A pre-replace crash can leave an
unused sibling temp file; record discovery ignores it. No claim of unrestricted
safe concurrent manual editing or data-access isolation is made.

A2 plus exact C3 grants require ventures to exist before policy can grant access.
Creating a new venture scope therefore requires human provisioning; record tools
cannot create their own permissions. Initiative/task creation in granted ventures
is implemented. This retains the approved explicit-grant policy.

The preceding observations describe the historical Step 3 boundary.

## Step 4: observed

- Started from accepted `main` at `9774ed4`; the attached handoff was an older
  Step 1 snapshot. Reran the 236-test baseline successfully. Part A was pushed
  separately as `9f02599`. Final implementation: `176478a0ae56c718c2683fd5fb5f885a15554508`.
- A fresh detached checkout with no environment/cache passed `uv sync --locked`,
  **343 tests in 13.83s**, validation of 13 records, and installed index rebuild.
  Original record bytes, policy, dependency configuration/lock, and Git status
  remained unchanged. The real-process concurrency and crash tests remain green.
- An unchanged file with skip-worktree can evade status and the earlier content
  comparison. The shared guard now rejects `S` and every lowercase ls-files tag
  before writes or human commits. Real `S`/`h` cases pass; uppercase `H` is allowed.
  `commit-human` also uses the hash fallback when status reports no change.
- Updates authorize current and destination scopes from frontmatter before body
  reads. Template creates deny ungranted callers after policy-only I/O; they read
  neither templates nor records and do not reach locks, index, or Git.
- AC4 creates all six exact GTM sections through `create_record`, with version 1,
  one attributed record-only commit, and a matching index payload. Missing/empty/
  placeholder content leaves records, cache, and HEAD unchanged.
- Review demonstrated that ordered tokens alone did not ensure correct section
  placement, and numeric list markers could count as content. Three regressions
  failed before the fix; source placement and rendered content are now checked.
- Agent templates create descriptive `agent` records with a fixed read-only notice.
  They do not register callers, grant permissions, or spawn agents. The new ID's
  actual write attempt is refused. A human must separately grant the author access
  to the `agent` record kind; checked-in `agents.yaml` remains unchanged.
- The installed CLI created one initiative and one agent document in a temporary
  fictional repository. Exactly two single-record commits were attributed to the
  configured agent; policy stayed unchanged, invalid sections made no writes, and
  deleting/rebuilding the cache restored all 15 records with identical new payloads.
- Joe's revised roadmap is recorded: real-client MCP, prototype-approved read-only
  portal, layout/change planner, optional Miro export, and separate later chat import.
  No implementation for those future steps was added or verified here.
- Portal health needs decisions on milestone/date, task due dates, blocker reasons,
  and derived activity/health. Human commits preserve `updated_at`; it cannot alone
  establish last activity. No proposed portal fields or health calculations were added.

Step 4 limits: structural validation cannot assess the business quality of section
prose. Agent documents remain distinct from policy identities. Existing POSIX,
ordinary-editor concurrency, crash-recovery, and read-isolation limits still apply.
Obsidian UI, real MCP client, portal, and optional Miro evidence remain pending.
Next chat, only after Joe's go: **Step 5, MCP tools via a real stdio client (AC2).**

## Miro frame-deletion experiment

**Not run. Outcome unknown.** Part of revised optional Step 8, on disposable scratch items.

Record the board ID, frame ID, child IDs, timestamp, deletion response, and each
child's subsequent GET result. Test actual frame-parent relationships. Distinguish
survived, deleted, and indeterminate responses. Do not infer survival from HTTP 204.
Never use the group-delete endpoint.

## Design limits to resolve in their approved steps

**Pending create without an item ID:** C1 forbids adopting unmapped items. A
fingerprint match is not proof of ownership. Preserve the pending entry and stop;
never blindly retry an ambiguous create or silently choose a matching board item.

**Normal becoming restricted:** Omitting the record from the next neutral graph
does not remove an older visible card. Define and test this transition, including
affected dependencies and hidden parents, before renderer acceptance. No automatic
board cleanup or deletion behavior has been implemented in Steps 1–2.

**Human edits:** Step 3 refuses dirty target files by name with
`uncommitted human edit`. `commit-human` supplies the explicit attributed commit.
Coordinate ordinary editor activity and reread after that handoff. The SQLite
index continues to read working-tree state, including uncommitted manual edits.
