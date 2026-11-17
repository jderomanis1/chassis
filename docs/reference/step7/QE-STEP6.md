# QE Step 6 report

QE Lead, 2026-11-17 8:53 AM MST (America/Phoenix).
Read-only check of https://github.com/jderomanis1/chassis at HEAD 523a8a58b9a28c9d977d0512b14fc4b995ac5d21 (runtime 7d152c51e8e123c860067e08e94e24c6bba5347f). No push, no PR, no product-code changes. S1-S6 and P1-P4 taken from CODEX_STEP6_PROMPT.md.

## Verdict: PASS

A1, A2, S1-S6, and portal P1-P4 hold on an independently materialized tree. Codex's extras-matrix counts and the 47-test leak probe match QE re-runs, with one 3-byte CLI capture difference. Step 5 A2 carryovers (SIGTERM test, 1 MiB payload cap, -32700 parse error, exact asserts) are in the suite. Must-fix items below are for the canvas step and for real data, not a fail of this sample-data backend increment.

## DELIVERED

- Report: this file.
- Tree: `/workspace/chassis-qe6` at HEAD `523a8a5`. 95 required source, test, template, record, and config blobs SHA-matched to GitHub. `uv.lock` was regenerated with `uv lock` from the SHA-matched `pyproject.toml` (connectors truncate the lock); the result was byte-identical to GitHub (150803 bytes, git blob SHA `6274e376d474ac7ad9e4b68bef38913c7b458768`, sha256 `68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`, matching `evidence/step6-verification.json`).
- `evidence/acceptance.md` (43076 bytes, blob SHA `98a6671fe3ed62398c93053b9f099200157b14a3`) was confirmed by SHA, but connector fetches truncated the body, so QE did not re-read the whole file. Claims were checked against `evidence/step6-verification.json` (SHA-matched) and a live re-run.
- STATE.md and TEST_PLAN.md updated with this result.

## VERIFIED

Implementation window after Step 5 HEAD `384931f`, times in MST:

- `a02e37d` 4:33 PM MST: A1/A2, MCP optional extra and bounded stdio.
- `f406487` 4:45 PM MST: S1-S6 library read security.
- `3ee59cb` 4:51 PM MST: P1 loopback JSON server.
- `9a80d95` 4:54 PM MST: P2 snapshot and drilldown.
- `82e4691` 5:00 PM MST: P3 health with injected clock.
- `bf270b3` 5:04 PM MST: P4 graph, search, error envelope.
- `4854431` 5:24 PM MST: hidden-source diagnostics contained.
- `7d152c5` 5:34 PM MST: package static mount (final runtime).
- `523a8a5` 5:40 PM MST: docs and evidence only (handoff, FINDINGS, ARCHITECTURE, acceptance, verification JSON, leak probe script). No `src/` or `tests/` changes after `7d152c5`.

QE Python is 3.13.5. Codex evidence used 3.12.14. Installed extras match the evidence: mcp 2.3.0, starlette 1.10.0, uvicorn 0.54.0. Command: `.venv/bin/python -m pytest -q`.

Claim vs observed:

| Config | Claimed | Observed |
| --- | --- | --- |
| `uv sync --locked --all-extras` | 576 passed, 0 skipped, 0 warnings, 53.87s (dev 53.23s) at `7d152c5` | 576 passed in 53.50s, then 576 passed in 57.39s. Zero failed, zero skipped. |
| `uv sync --locked` (core) | 499 passed, 8 skipped modules, 0 warnings, 25.79s; mcp, starlette, uvicorn absent | 499 passed, 8 skipped, 25.31s. Those three modules absent. Skips: portal conftest (1), mcp_client (6), test_mcp_stdio (1). |
| `uv sync --locked --extra portal` | 542 passed, 7 skipped, 1 warning, 29.43s; mcp absent | 542 passed, 7 skipped, 1 warning, 28.05s. Warning is Starlette TestClient deprecating httpx for httpx2. mcp absent. |
| Leak probe | 47 tests, 0 matches, 25 captured files (cli 3, mcp 10, portal 12), bytes 14278 / 36572 / 33075, segments 66 / 90 / 30, all rg exits 1, at `7d152c5` | Same 47 tests passed in 15.82s (claimed 16.8s). 25 files, same surface split, mcp and portal bytes exact, segments exact, all rg exits 1, matching_files 0. CLI bytes 14275 vs claimed 14278 (off by 3). |

Leak probe command reproduced: `CHASSIS_LEAK_PROBE_DIR=... PYTHONPATH=evidence .venv/bin/python -m pytest -q -p step6_leak_probe` on `tests/test_security_cli.py`, `tests/test_mcp_read_security.py`, `tests/portal/test_api.py`, `tests/portal/test_boundary.py`, `tests/portal/test_graph_search.py`, and `tests/portal/test_static.py` (47 collected). Patterns are the restricted record's id, title, owner, and complete body, plus JSON-escaped forms, via `rg --fixed-strings --multiline --files-with-matches`.

Plant on a scratch copy: a file containing the title `Set the internal launch test budget`, the owner `Fictional Private Reviewer`, or the complete body produced a match (rg exit 0). A clean file did not. A unique body sentence alone (`Keep this record out of every rendered graph and board.`) did not match, because the body pattern is the complete body, not a substring sentence.

### S1-S6 and P1-P4 coverage

- **A1.** `mcp` and `portal` are optional extras. `tests/test_optional_mcp.py` and `tests/test_optional_portal.py` cover the install message. Core-only sync cannot import mcp, starlette, or uvicorn.
- **A2.** `tests/test_mcp_hardening.py`: malformed JSON returns `-32700` Parse error and the session recovers; payload cap is configurable (1024 and 1 MiB) with `-32000` / `payload_too_large`; SIGTERM during an in-flight write waits for the hook, exits 0, and `assert_lock_released` plus `StdioClient.__exit__` check the process group. Session asserts now use exact `blocker_reason`, `last_activity_at`, and validation `reason` values.
- **S1.** `tests/test_read_security.py` and `tests/test_mcp_read_security.py`: unknown, empty, missing, and wrong-token callers get nothing; grant-scoped agents see only their ventures. Enforced in the library (`authorize_reader`, `visible_records`), so CLI, MCP, and portal inherit it.
- **S2.** Normal reviewer: 12 records, 2 Acme tasks, no restricted row, search, count, or graph edge. Restricted clearance plus a grant sees `task-launch-budget`. Hidden ancestors hide descendants. Portal leak tests confirm no row, count, status, or edge for a normal viewer. Filtering is in `policy.can_read_record` / `visible_records`, not a portal-only redact.
- **S3.** Hidden and missing reads share `not_found`. Unauthorized writes are the generic `Write not permitted` with no venture or type. Portal hidden vs missing venture envelopes match.
- **S4.** Audit lines are JSON, gitignored under `.chassis/`, include UTC time, agent id, tool, ids or count, and outcome, and contain no bodies or tokens.
- **S5.** `chassis agent-token create` prints the token once and stores only a SHA-256 digest (`tests/test_agent_tokens.py`). `.chassis/agent-tokens.yaml` is gitignored. `docs/agent-tokens.example.yaml` is placeholders only (`<SHA256_HEX_DIGEST_ONLY>`). No tokens in the git blobs QE checked.
- **S6.** The cases above run through the real stdio MCP client as well as the library and CLI. The 47-test leak probe is the S6 grep over CLI, MCP, and portal outputs.
- **P1.** `tests/portal/test_bind_version.py`: non-loopback bind refused unless `CHASSIS_PORTAL_ALLOW_REMOTE=1`; `/api/version` etag tracks commit and uncommitted bytes; real loopback HTTP; viewer goes through S1-S5.
- **P2.** `tests/portal/test_api.py`: snapshot, venture, and initiative contracts; visible counts only; hidden task does not change counts or health; built from library reads.
- **P3.** `tests/test_health.py` and `tests/portal/test_health_api.py`: ADR rules as a pure function with a frozen clock; thresholds 3 / 7 / 14 days in config; invisible restricted children add no color and no reason.
- **P4.** `tests/portal/test_graph_search.py` and `test_boundary.py`: neutral graph, search, GET-only, Host/Origin checks, no ask endpoint, error envelope `{error:{code,message}}` with no stack traces.

### Mutations (copy only; `/workspace/chassis-qe6` left unmutated)

1. Restricted hiding removed in `can_read_record`: caught. Library count, CLI leak, and portal leak tests failed (13 vs 12; `task-launch-budget` appeared in API JSON).
2. Stale conflict mapped to a generic `internal_error`: caught. Session and M9 tests failed (`internal_error` != `conflict`).
3. Version check skipped in `store.update_record` so a stale write can proceed: caught. Session stale assert raised `KeyError: 'error'`; `test_stale_version_returns_current_version_without_file_cache_or_commit_change` failed.
4. `authorize_reader` skipped the token check: caught. Missing/wrong token library tests and the four MCP unproven-identity cases failed.

s5-style blob SHAs for `policy.py`, `tool_handlers.py`, and `store.py` still matched on the unmutated qe6 tree after this work.

### Step 5 must-fix carryovers

- SIGTERM test: present and passing.
- Payload size cap: present, default 1 MiB, configurable, structured error.
- `-32700` parse error: present; session recovers.
- Truthiness-only session asserts: replaced with exact values.
- `evidence/mcp-session.jsonl` is still in the repo (SHA `1733fd94…`, unchanged) and is still not pinned in CI. There is no `.github` workflow in this tree.

## RISKS-OPEN

- MCP `IndexFileError` can return an absolute vault path. Independent probe: after replacing `.chassis/index.sqlite` with a symlink, `ToolHandlers.call("list_records", {})` returned `validation` with reason `/tmp/.../vault/.chassis/index.sqlite: index paths cannot be symlinks`. This is a path leak, not a restricted-content leak. The portal maps it to a generic `internal` envelope; MCP does not. Code Reviewer S1. Must-fix before real data.
- The leak probe will miss a partial body leak that does not also include the id, title, owner, or the complete body.
- CLI leak-capture bytes were 14275 vs claimed 14278. Not a content match.
- Code Reviewer S3: `tests/portal/conftest.py` does `from conftest import issue`, which can fail to collect portal tests under some in-tree pytest import modes (CR saw 533 passed and 46 portal tests uncollected). QE's runs from `/workspace/chassis-qe6` collected and passed 43 portal tests as part of 576 and 542. QE could not reproduce the collection miss, and could not find 46 official portal nodeids in this tree (43 collected). The import is still brittle and should be moved to a helper module.
- No CI pin of `evidence/mcp-session.jsonl`.
- Portal P1-P4 is a read-only JSON API. XSS escaping and empty/loading/error UI states are not in this increment. Canvas writes are not in this increment.
- GTM section names remain UNVERIFIED against the original prompt. Obsidian open-and-browse remains PENDING for Joe (AC1). SecOps real-data and agent-channel NO-GO remains.
- QE did not re-read the full truncated `evidence/acceptance.md` body.

## Must-fix (canvas step and pre-real-data)

These are not a Step 6 fail of the sample local backend.

1. Close the MCP `IndexFileError` path leak (CR S1) before real data.
2. Make portal test collection import-safe (CR S3: move `issue` out of `conftest`).
3. If the canvas adds a write, use the same library `update_record` path only (lock, auth, `expected_version`, one commit). No direct file writes. Tighten Host/Origin before opening POST (CR S2).
4. Show a stale-version conflict in the UI, with no overwrite (AC2, AC3).
5. Keep S2 hiding in the UI: no row, count, status, edge, search hit, or health effect for restricted records the viewer cannot see.
6. Escape all record content against XSS (title, owner, body, blocker_reason, search hits, health reasons).
7. Empty, loading, and error states, including auth failure and generic backend envelopes.

## NEXT

Canvas front-end Playwright tests the next step must add (numbered, traced to S/P and AC1-9):

1. XSS: record title, owner, body, blocker_reason, search hits, and health reasons are escaped in the canvas. (S2/P2 content; prompt heads-up; AC1 fields.)
2. Empty, loading, and error states, including auth failure and `{error:{code,message}}` from P4, against the approved prototype. (Prompt heads-up; P4.)
3. Restricted records are fully hidden in the canvas: no row, count, status, edge, search hit, or health reason. (S2, P2, P3; Joe's hide-restricted decision.)
4. A stale `expected_version` is shown as a conflict in the UI and does not write. (AC2, AC3; C1 if writes land.)
5. Canvas writes call library `update_record` only: one attributed commit, lock and dirty-record refusals still apply, no direct file I/O. (AC2, AC3, S1-S5.)
6. Unproven or out-of-grant viewers are denied; hidden and missing ids look the same. (S1, S3, S5, P1.)
7. Snapshot and venture/initiative drilldown match the P2 contract and visible counts only. (P2, AC1 sample set.)
8. Health colors and reasons use only visible children and the 3 / 7 / 14 day thresholds. (P3.)
9. Graph is rendered from `/api/graph` (neutral data, no server layout) and omits restricted edges. (P4, S2.)
10. Search is rendered from `/api/search` and returns no restricted hits for a normal viewer. (P4, S2, S6.)
11. Once a write method exists, Playwright covers Host/Origin and method rules so a foreign origin cannot POST. (P4; CR S2; AC2.)

Chief of Staff can proceed with the canvas step. Real Andy data stays blocked until the path leak is closed and any write endpoint meets the SecOps bar.
