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

Next chat, only after Joe's go: **Start Step 3 only. Read the current handoff and
repository instructions; implement C3/C6 record mutations, version checks,
attributed Git commits, and commit-human with tests first.** The complete starting
prompt and outstanding gates are in `CHASSIS_PROJECT_HANDOFF.md`.

## Miro frame-deletion experiment

**Not run. Outcome unknown.** Scheduled for Step 6 on disposable scratch items.

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

**Human edits:** Later mutations must name the file and say `uncommitted human edit`.
The planned `commit-human` command is the explicit path for attributed human changes.
It is not available yet; the SQLite index now reads working-tree state.
