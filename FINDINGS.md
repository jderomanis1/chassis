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

## Step 5: observed

- Started at accepted `a26a093`; remote HEAD and clean local tree matched. The
  uploaded handoff was an older Step 1 snapshot. The 343-test baseline passed.
  Part A was pushed separately as `c3cb106`, Part B as `42a8056`, and the final
  runtime/test checkpoint is `6ab3b14a759e1e3d5f8e9beae08bf8943b7c8d5d`.
- A fresh detached checkout with no environment/cache passed `uv sync --locked`,
  **431 tests in 29.94s**, validation of all 13 records, and an index rebuild.
  Git status remained empty. Sample policy is unchanged; the sole sample-record
  change is the blocked Ridgeview task's required reason.
- Template metadata now uses the same strict record constraints before expansion.
  FIXME/XXX and NFKC compatibility forms are rejected. Eighteen regressions failed
  before the fix. NFKC does not claim to recognize every possible Unicode homoglyph.
- Optional milestone/due fields validate strict date-only values. Task blockers
  are required when blocked and must be cleared with the status transition.
  Older records can omit optional fields; legacy blocked tasks need a reason.
- `last_activity_at` is derived at index time from the latest touching commit's
  committer timestamp, normalized to UTC. Both human and agent commits count.
  An unrelated commit or uncommitted edit does not advance it. A human edit and
  byte/mtime-identical restoration still refresh history. No commit history means
  null. Activity never enters frontmatter; schema-2 caches rebuild as schema 3.
- The official MCP Python SDK is locked at 2.3.0. Six strict tool schemas and
  transport-neutral handlers call the CLI's existing libraries. Caller identity
  comes from server environment configuration. Extra caller arguments are rejected;
  assigning a record to another known agent does not change commit attribution.
- One real subprocess/client session initialized, listed tools, and exercised
  list/read/search/create/template/update. Exactly three writes produced three
  single-record commits by the configured fictional author. Stale and invalid
  requests preserved every source byte, cache byte, and HEAD. A second integration
  test connects using the official SDK client over actual stdio.
- Dirty/staged targets, unchanged/edited hidden Git flags, denied scopes,
  unknown/read-only callers, missing/invalid/revoked policy, and unsafe lock paths
  all retain their refusals through MCP. No duplicate mutation path was introduced.
- Two real MCP clients were blocked by one held OS lock, then raced the same
  version: one success, one conflict/current version 2, exactly one commit, and
  source/index/author matching the winner. Both server process groups ended cleanly.
- Every stdout line parsed as JSON-RPC while startup/tool/shutdown logs went to
  stderr. Closing clients ended servers with exit 0 and no surviving process group.
  The kernel lock was immediately reacquirable. The stable lock inode remains by
  design; deleting it would split synchronization across concurrent waiters.
- Error review reproduced a Git hook traceback reaching the client and loss of
  uncertain-commit metadata. Three regressions failed before the fix. Raw hook/cache
  diagnostics now stay on stderr, with committed/current-version/SHA facts retained.
- `evidence/mcp-session.jsonl` records a real clean-checkout session: 25 paired
  wire messages, all six tools, and representative failures, with fictional data
  and no environment secrets. Its capture test passed again in 1.56s.
- README has a placeholder-only Claude Desktop configuration. No desktop UI,
  Obsidian UI, HTTP, portal, health calculation, Miro, or deployment pass is claimed.

Step 5 limits: Linux/POSIX execution is verified; native Windows locking is not
implemented. Reads still expose restricted records according to the existing
library contract; renderer/portal filtering remains a later gate. Ordinary editors
do not honor the process lock, and file replacement plus Git remain separate crash
boundaries. Source scans now also consult Git history; no large-vault benchmark
has been performed. Next: wait for Joe's go on the portal design prototype.

## Step 6: observed

- Work began at accepted `384931f` after reading the supplied portal ADR and SecOps
  checkpoint. Joe explicitly replaced masking with complete library-level hiding.
  Only fictional records and local execution were used.
- A `a02e37d` makes MCP optional, bounds stdio requests at a configurable 1 MiB,
  returns -32700 for malformed JSON, and proves SIGTERM cleanup during an active
  transaction. The core imports and its CLI work without the MCP SDK.
- S `f406487` verifies SHA-256 token hashes and exact venture/type read or write
  grants before returning records. Normal clearance is the default. Hidden rows,
  descendants of hidden parents, and identifying dependency edges are removed in
  the library. All public projections use those reads.
- Token provisioning is a local operator command, not a record or MCP tool. It
  prints a fresh token once and stores only its hash in the ignored credential
  file. Test credentials are generated at runtime, not checked-in reusable tokens.
- Audit appends record UTC time, caller ID, tool, returned IDs or counts, and
  outcome. Body/token exclusion, denied access, and audit failure recovery are
  covered. Appends use a separate file lock. A read cannot return its payload if audit
  append fails. A write already committed reports that fact if later audit fails.
- Final review reproduced a parser-cause leak: MCP's generic validation formatter
  could walk a library error's cause and expose a hidden source field. Five new
  regressions failed, including real stdio id/title/owner/body cases. Follow-up
  `4854431` removes that private cause, contains whole-vault write validation,
  and refuses unreadable target metadata generically. CLI and all six real MCP
  tools now cover malformed hidden sources. The full suite passes **575 tests in
  49.94s** after this security fix; clean-install results for the final revision
  are in acceptance.
- Portal P1 `3ee59cb`, P2 `9a80d95`, P3 `82e4691`, and P4 `bf270b3` were pushed
  separately. One optional Starlette/uvicorn process serves six GET endpoints.
  A real uvicorn process answered on loopback and shut down cleanly. Contract,
  wrong-host/origin/method, viewer-token, revocation, and generic-error checks pass.
- P1's static mount is completed by `7d152c5`: only the package asset directory
  is served, while vault/policy/token paths remain unavailable. API misses keep
  the JSON envelope. The built wheel contains the placeholder asset directory.
  No frontend UI is added. The final development suite passes **576 tests in 53.23s**.
- The normal viewer sees 12 records and 7 tasks. Acme contributes two visible
  tasks; a restricted-clearance viewer with the same grants sees its third task.
  Hidden task edits do not change visible counts or health. Search has no hidden
  hit, and the graph has no masked node, hidden edge, or layout coordinates.
- The restricted sample's owner is now a unique fictional name. The prior owner
  was shared with public rows, making an owner-string leak grep ambiguous. The
  revised fixture permits a literal zero-match check without exempting any output.
- Health is pure with an injected Phoenix date and 3/7/14-day constants. Tables
  cover priority, exact boundaries, unknown children, completed children, and
  dependency reasons. Parent status alone does not determine health. Snapshot
  reads retry a concurrent commit rather than attach a new etag to older data.
- "Agent writes today" is omitted. There is no invented activity value, frontend,
  ask endpoint, model call, browser/UI acceptance, Miro call, or deployment in this step.

Step 6 limits: these controls protect Chassis interfaces, not direct access to
plaintext Markdown, Git history, or SQLite. A malformed source can make a read
unavailable with a generic error; it cannot expose the hidden source diagnostics.
The portal serves one configured viewer to local clients and has no per-browser
user authentication. The original SecOps real-data/channel NO-GO remains pending
review and the remaining encryption/retention, rate-limit, disclosure, and
prompt-injection requirements. Existing POSIX, ordinary-editor, and file/Git crash
boundaries remain. Portal-only tests emit one development-only Starlette warning
about its compatibility with httpx; no runtime dependency was added to suppress it.

Next chat: **P5–P8, the approved prototype's frontend port**. Escape record content,
include empty/loading/error states, and run Playwright against the prototype and
backend. Keep hidden rows absent during refresh and after sensitivity changes.
Do not reopen the design or start P9/model ask, later layout, Miro, import, or deployment.

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
