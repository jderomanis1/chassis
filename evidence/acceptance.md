# Acceptance evidence

**Snapshot:** Monday demo UAT fixes are on `cursor/uat-canvas-fixes-8f6d`, based on `step7-c1-write` at `06a53bc`. The pull request targets `step7-c1-write` and is not merged. Main remains `42f0fa0`. C1/C2 are not independently reviewed. **Date:** 2026-11-17.

## UAT fixes

These runs used the working tree on this branch. They are not a fresh three-mode checkout, and they are not SecOps, QE, or Code Reviewer approval. Python 3.12.3. Node 24.22.1 and npm 11.9.0. uv 0.13.9. The lock file was not edited. Playwright used `/usr/bin/google-chrome`.

| Command | Result |
| :--- | :--- |
| `uv sync --locked --all-extras` then `.venv/bin/pytest -q` | **718 passed in 62.72s** |
| `uv sync --locked` then pytest | **523 passed, 9 skipped in 25.74s** |
| `uv sync --locked --extra portal` then pytest | **682 passed, 8 skipped, 1 warning in 38.63s** |
| `npm test` | **19 passed**, 0 failed |
| `npm audit --omit=dev` | 0 vulnerabilities |
| Playwright, `CHASSIS_CHROMIUM=/usr/bin/google-chrome` | **22 passed (1.0m)** |

Core skips are the portal module and 8 MCP modules. Portal skips are the 8 MCP modules. The warning is the existing `StarletteDeprecationWarning` for `TestClient` at `tests/portal/conftest.py:6`.

The new tests cover:

1. `/api/version` returns 304 for a matching `If-None-Match`, and the poll interval plus one second of request time is under 3 seconds. A Playwright disk edit appears within 3 seconds.
2. Undo derived from editor commits restores the prior title as a second commit. `HEAD^` is the edit. A cached version conflicts after a newer edit.
3. Resending a stored hidden dependency, alone or with a visible id, matches a missing id: 400, identical body, no commit. A visible-only list still keeps the hidden id.
4. A title edit after the hidden dependency file is deleted saves, drops that id, and does not mention it.
5. Adding and removing a restricted task leaves snapshot counts, initiative progress, task-card totals, and graph task counts unchanged. The Acme tile, zoomed cards, and progress total are all 5.
6. A duplicate `depends_on` list returns `{error:{code:"validation", message:"Record update could not be completed"}}` and does not echo the id.
7. Playwright checks focus return, 44 pixel controls, the minimap at 1280 after zoom-back and resize, wrapping a long title, one commit for a save started mid-typing, and a 1 pixel camera tolerance.

## R1 hidden dependencies and CI

These runs used the working tree on this branch. They are not a fresh three-mode checkout, and they are not SecOps, QE, or Code Reviewer approval. Python 3.12.3. Node 24.22.1 and npm 11.9.0 for the frontend commands. The lock file was not edited.

| Command | Result |
| :--- | :--- |
| `uv sync --locked --all-extras` then `.venv/bin/pytest -q` | **709 passed in 70.53s** |
| `uv sync --locked` then pytest | **519 passed, 9 skipped in 30.18s** |
| `uv sync --locked --extra portal` then pytest | **673 passed, 8 skipped, 1 warning in 44.12s** |
| `npm test` | **16 passed**, 0 failed |
| `npm audit --omit=dev` | 0 vulnerabilities |
| Playwright, `CHASSIS_CHROMIUM=/usr/bin/google-chrome` | **14 passed (57.8s)** |

Core skips are the portal module and 8 MCP modules. Portal skips are the 8 MCP modules. The warning is the existing `StarletteDeprecationWarning` for `TestClient` at `tests/portal/conftest.py:6`. The new stdio test is one of the MCP skips until the mcp extra is installed. It passed in the all-extras run.

The behavior covered by those new tests:

1. A title PATCH, and an MCP update that omits `depends_on`, saves. The stored hidden dependency stays in the file. The response and the initiative read omit it.
2. A visible `depends_on` list, including the canvas link payload and the undo payload, merges with the stored hidden ids. Clearing the visible list still leaves the hidden id on disk. Reads omit it.
3. A newly added hidden id and a newly added missing id return the same 400 body, `{"error":{"code":"validation","message":"invalid dependency"}}`, with neither id in the body, and with no commit. Library and MCP handler errors match each other the same way. `create_from_template` rejects a new hidden dependency and a missing one with the same `invalid dependency` error and writes nothing.

## Step 7 canvas loop

The command canvas now renders a separate `chassis demo-init` vault. Playwright
launched Google Chrome and exercised the built portal. This is not a SecOps, QE,
or Code Reviewer approval, and it is not a merge to main.

| Increment | Commit | Result |
| :--- | :--- | :--- |
| Font-face check | `30d2ae5` | Scaffold browser check loads Chakra Petch 500 and the other two families |
| Post-commit audit recovery | `8033bf2` | Middleware audit failure after a successful PATCH keeps committed, commit, and current_version |
| Restricted layout cleanup | `4f87fc3` | A read removes invisible ids from a valid layout file; corrupt files stay untouched |
| Live canvas | `60f91d1` | Seven tiles, zoom, drag, edit, undo, conflict, search, and stdio MCP refresh |

Executed on this working tree, not a fresh three-mode checkout:

- `.venv/bin/pytest -q`: **696 passed** in 1116.78s.
- `npm test`: 8 passed.
- `npm run contrast`: dark 64 pairs, 0 failures, lowest 5.11; light 64 pairs, 0 failures, lowest 4.74.
- `npm audit --omit=dev`: 0 vulnerabilities.
- `npm run build` twice: all 21 static files matched. Production dependencies are unchanged, so the existing 30-entry license list still applies.
- Playwright with `CHASSIS_CHROMIUM=/usr/local/bin/google-chrome`: scaffold 5, canvas 4, and the live walk-through passed. One live run timed out while the full Python suite was also running; a later solo run passed in 11.5s.
- The built bundle and the Playwright DOM/layout checks had 0 matches for `task-launch-budget`, the restricted title, owner, and partial body sentence.

Screenshots at 1440x900 are in `evidence/step7-ui/`: dark and light overview with hover, zoomed Ridgeview, edit, and the conflict message.

## Step 7 stretch

| Item | Evidence |
| :--- | :--- |
| Hover strip and one camera fit | `6b99c3a`. The tooltip box does not intersect the venture tiles. The viewport is stable after fonts are ready. |
| X1 hide | `d2c96b5`. H and a drag to the pane edge hide cards. Show hidden restores them. Git HEAD does not move. Screenshots: `dark-x1-hidden.png`, `light-x1-hidden.png`. |
| X2 command bar | `f544ea4` plus the later link commit's filter fit. Six commands, fuzzy venture match, unknown list. Screenshots: `dark-x2-command.png`, `light-x2-command.png`. |
| X3 task links | Task-to-task PATCH, cycle message, non-task rejection. Screenshots: `dark-x3-link.png`, `light-x3-link.png`. |

Playwright after these additions: 13 passed (scaffold, canvas, live loop, X1, X2, X3). Focused graph and portal write tests passed. This is not an independent review.

### Review fixes at a5cd405

Detached worktrees of `a5cd40597253659dde0af819e17719f19d17bd34` each removed `.venv`, ran `uv sync --locked`, then `.venv/bin/pytest -q`. The lock SHA-256 stayed `68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`. Source status was empty. This is not a SecOps, QE, or Code Reviewer approval.

| Command in that worktree | Result pytest printed |
| :--- | :--- |
| `uv sync --locked --all-extras` then `.venv/bin/pytest -q` | **701 passed in 59.29s** |
| `uv sync --locked` then `.venv/bin/pytest -q` | **515 passed, 8 skipped in 24.46s** |
| `uv sync --locked --extra portal` then `.venv/bin/pytest -q` | **666 passed, 7 skipped, 1 warning in 35.64s** |

Core skips are 1 portal module and 7 MCP modules. Portal skips are the 7 MCP modules. The warning is `StarletteDeprecationWarning` for `TestClient` and httpx at `tests/portal/conftest.py:6`.

Before fixture and demo repositories set `commit.gpgsign` false, two all-extras runs on `520a639` were not clean: `1 failed, 699 passed in 1093.37s (0:18:13)` (`test_sigterm_finishes_active_transaction_and_releases_lock` exceeded 5 seconds) and `699 passed, 1 error in 1120.67s (0:18:40)` (`git commit` exit 128, `Couldn't find key in agent?`). The counts in the table are the later clean runs.

A fourth detached worktree at `520a639`, whose frontend sources and 21 static files match `a5cd405`, used Node 24.22.1 and npm 11.9.0:

| Check | Result |
| :--- | :--- |
| `npm test` | **15 passed**, 0 failed |
| `npm run contrast` | dark 64 pairs, 0 failures, lowest 5.11; light 64 pairs, 0 failures, lowest 4.74 |
| `npm audit --omit=dev` | info 0, low 0, moderate 0, high 0, critical 0, total 0 |
| `npm run build` twice | both builds matched the committed 21 static files, and matched each other |

Playwright then ran alone from `frontend/` with `CHASSIS_CHROMIUM=/usr/local/bin/google-chrome npx playwright test` against the same tree: **14 passed (52.2s)**.

### Fresh locked checkout at 1cb92f4

Three detached worktrees of `1cb92f44e82d55e46cc69aac69ace6b06a7d0a34` started with no virtual environment. Each used `uv sync --locked` and `.venv/bin/pytest -q`. The lock SHA-256 stayed `68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`. Source status was empty in all three.

| Installation | Result |
| :--- | :--- |
| `uv sync --locked --all-extras` | **698 passed in 1090.89s (0:18:10)** |
| `uv sync --locked` | **513 passed, 8 skipped in 1384.70s (0:23:04)** |
| `uv sync --locked --extra portal` | **663 passed, 7 skipped, 1 warning in 1006.48s (0:16:46)** |

The core skips are 1 portal module and 7 MCP modules. The portal skips are the 7 MCP modules. The one warning is the existing Starlette `TestClient` deprecation.

A fourth detached worktree, Node 24.22.1 and npm 11.9.0, ran `npm ci` then:

| Check | Result |
| :--- | :--- |
| `npm test` | **14 passed**, 0 failed |
| `npm run contrast` | dark 64 pairs, 0 failures, lowest 5.11; light 64 pairs, 0 failures, lowest 4.74 |
| `npm audit --omit=dev` | info 0, low 0, moderate 0, high 0, critical 0, total 0 |
| `npm run build` twice | both builds matched the committed 21 static files, and matched each other |

Playwright then ran alone in that worktree after `uv sync --locked --all-extras`, with `CHASSIS_CHROMIUM=/usr/local/bin/google-chrome`: **13 passed in 49.3s**. No product code changed.

## Earlier Step 7 resume: C1/C2 and partial F1

All source records and people are fictional. AC2, AC3, AC4, and AC9 pass; later gates remain pending.
The notes below describe the browser-blocked checkpoint and are kept as history.

**At that checkpoint, Step 7 was not complete.** Main remains at `42f0fa0`. The new code is on
`step7-c1-write`, gated from merge by independent SecOps review. The runtime/test
checkpoint is **`83b8d61b06b7b6d04f44d1fcb42f13641b140f38`**; later commits preserve
sources and update documentation/evidence only. The complete approved source pack
is under `docs/reference/step7/`; every manifest hash was checked before use.
Its older dated status/deadline notes are historical. The current demo target is
Monday, November 23, 2026, morning, America/Phoenix.

### Delivered on the review branch

| Increment | Commit | Test-first evidence and result |
| :--- | :--- | :--- |
| C1 shared guard | [d3af932](https://github.com/jderomanis1/chassis/commit/d3af9324a2bfa10f65e412b6e8967d33043a2c72) | New checks first produced 1 failure/51 setup errors; 76 guard/read-boundary checks then passed |
| C1 record PATCH | [639d607](https://github.com/jderomanis1/chassis/commit/639d6079ad3cfdbda8c3613df8a7a4d9dcc40583) | 28 new checks failed first; 148 portal/update/permission/concurrency checks then passed |
| C2 layout | [1bcdf60](https://github.com/jderomanis1/chassis/commit/1bcdf60a158d206d0311b7d4832e4a7e9f8607ef) | 16 new checks failed first; 39 layout/visibility checks then passed; full development suite passed 695 |
| F1 partial scaffold | [83b8d61](https://github.com/jderomanis1/chassis/commit/83b8d61b06b7b6d04f44d1fcb42f13641b140f38) | Node test first failed on absent module; 4 JavaScript checks pass; browser launch blocked |

C1 writes are off by default, require a separately authenticated normal editor,
and use the existing library transaction. Tests cover wrong/missing origin,
wrong host, form/non-JSON content, missing/wrong/cross-launch CSRF, fetch metadata,
actual byte cap, field allowlist, invalid IDs/paths, revocation, rate limit,
current-version conflict, dirty target, body cap, uniform hidden/missing/ungranted
refusal, a single record commit, editor attribution, and etag change.
Normal-only clearance is rechecked under the record lock. Library committed-error
recovery facts are preserved by the route's tested error mapping.

C2 tests cover per-viewer layout, no record commit, hidden-ID removal before disk
and response, newly hidden parents/descendants, missing/corrupt input, coordinate
validation, symlink refusal, and credential rechecks inside the vault lock.
A previously stored ID that becomes hidden is not returned; the next save removes
it from the file. This does not provide direct-filesystem isolation.

### Clean locked verification

Three fresh clones of `83b8d61` started with no virtual environment. Each installed
from the unchanged uv.lock and ran `.venv/bin/pytest -q`.

| Installation | Observed result | Isolation |
| :--- | :--- | :--- |
| `uv sync --locked --all-extras` | **695 passed in 158.27s** | MCP and portal installed |
| `uv sync --locked` | **512 passed, 8 modules skipped in 69.26s** | MCP, Starlette, uvicorn absent |
| `uv sync --locked --extra portal` | **660 passed, 7 modules skipped, 1 warning in 101.51s** | MCP absent; existing TestClient development warning |

All three stayed clean. Records, agents.yaml, pyproject.toml, and uv.lock remain
unchanged from `523a8a5`. Lock SHA-256:
`68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`.
The earlier accepted 598/512/563 checkpoint remains historical evidence below.

### Restricted-content and actual HTTP checks

The extended transport probe passed **95 tests in 71.88s**, with **zero matches
in 31 captures / 200 output segments** for restricted ID/title/owner/full body/
partial sentence, including raw and JSON-escaped forms. Capture totals: CLI 3/66,
real stdio MCP 10/90, portal 18/44 (files/segments). Session CSRF is checked in
memory and redacted from persisted captures by the existing evidence helper.

A separate actual uvicorn/CLI smoke check used `chassis demo-init` to create a
new 63-record fictional vault. It exercised all eight GET routes, gated PATCH,
and layout PUT. All 21 built assets were served byte-identically over loopback.
One HTTP record update produced exactly one record-only commit by
`canvas-editor <canvas-editor@chassis.local>`. Hidden/missing writes returned
identical 404 bytes. Fourteen API/layout capture segments and the static bundle
had zero restricted-pattern matches; no generated agent credential appeared in
assets. These are backend/static-delivery checks, not browser or canvas evidence.

The [verification JSON](step7-resume-verification.json) contains counts, hashes,
provenance, and the actual HTTP result without credential values or response bodies.
To repeat the transport probe, append `tests/portal/test_record_writes.py` and
`tests/portal/test_layout.py` to the earlier 50-test Step 7 command below.

### F1 build evidence and browser blocker

- Exact pins: React/React DOM 18.3.1, React Flow MIT core 12.12.1, Vite 8.3.8,
  Playwright 1.65.1, and the pinned layout/font packages in package-lock.json.
- Chakra Petch, IBM Plex Sans, and JetBrains Mono are self-hosted in the build.
  The copied visual CSS and generated theme tokens come from the approved pack.
- Four JavaScript checks pass. Both original 64-pair contrast checks pass:
  dark minimum 5.11:1 and light minimum 4.74:1.
- A locked `npm ci` followed by build reproduced all **21 static asset hashes**.
  This proves the scaffold build, not the future F2-F6 bundle.
- `npm audit --omit=dev` reports **0 vulnerabilities**. The license list contains
  30 production packages, with full notices preserved and served.
- All five Playwright scaffold cases failed at browser launch before page
  navigation. `/usr/bin/chromium` could not create its local Unix socket:
  `socket() failed: Operation not permitted (1)`.
- The execution policy automatically rejected the elevated browser-test request
  because sandbox permission requests are disabled. An isolated Playwright
  headless-shell fallback also failed to download a valid archive. No workaround
  changed or bypassed that policy.

**No UI pass is claimed.** There are zero implementation screenshots, no DOM leak
check, no proved live refresh, and no real stdio MCP/canvas loop. F1 contains only
an API/theme/loading/empty/error shell. F2-F6 and X1-X3 have not started. The
original source screenshots are reference artifacts, not pictures of this build.

### Remaining gates and review follow-up

Resolve the browser execution environment, finish F1 tests, then continue F2-F6.
Independent SecOps must review C1/C2 before merge; QE and Code Reviewer verdicts
are still outstanding. Engineering tests do not substitute for those reviews.
One exception-path follow-up is specifically recorded: fault-inject the final
middleware audit append after a successful record commit and preserve recovery
facts if that append fails. That case has not been tested; do not infer its result
from the tested library committed-error mapping.

The current user instruction requires stopping on a genuine access blocker.
Feature work stopped at this checkpoint; there is no claim of Step 7 completion
or readiness for the Monday demo. No real data, Miro, model call, ask endpoint,
gateway, hosting, deployment, or agent spawning was used.

## Earlier Step 7 executed checks: partial checkpoint

Started from verified private main **523a8a58b9a28c9d977d0512b14fc4b995ac5d21**.
Joe's [Step 7 scope](../docs/STEP7-CANVAS-SCOPE.md) supersedes the older P5–P8
port. C-1, C0, and C3 are delivered. C1/C2/F1–F6 remain unimplemented because the
required security/design sources are absent. **Step 7 is not complete.**

Final runtime is **6e1ec10ced4688d98c40f9ec33661a17dbfcd9cd**. Final tests/evidence
are **f297db302150cc2f991c84e97b0234ab2e9b0828**. Three new detached checkouts
started without virtual environments and installed the unchanged dependency lock.
The [verification JSON](step7-verification.json) records counts and provenance,
without record bodies or credentials.

| Clean installation | Observed test result | Isolation |
| :--- | :--- | :--- |
| `uv sync --locked --all-extras` | **598 passed in 136.91s** | MCP and portal present; no skips or warnings |
| `uv sync --locked` | **512 passed, 8 modules skipped in 67.08s** | MCP, Starlette, and uvicorn absent |
| `uv sync --locked --extra portal` | **563 passed, 7 modules skipped, 1 warning in 77.75s** | MCP absent; portal present |

Each suite ran with `.venv/bin/pytest -q` in its clean checkout. All three Git
statuses stayed empty. `uv.lock` SHA-256 remains
`68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`.
Records, sample policy, pyproject.toml, and lock are unchanged from 523a8a5.
The portal-only warning is the existing development TestClient/httpx warning.

### Delivered increments and test-first evidence

| Increment | Commit on private main | Executed checks |
| :--- | :--- | :--- |
| C-1 review fixes | [45be742](https://github.com/jderomanis1/chassis/commit/45be7427780ed066cc47f9fbd200d51429cfc503) | 18 regressions failed first; 29 focused checks passed, then **588 passed** in one in-tree pytest run |
| C0 session and versions | [cb26ed9](https://github.com/jderomanis1/chassis/commit/cb26ed926da7d670f1943c2128db55159f80097b) | 6 contract checks failed first; all **50 portal tests passed** |
| C3 demo generator | [6e1ec10](https://github.com/jderomanis1/chassis/commit/6e1ec10ced4688d98c40f9ec33661a17dbfcd9cd) | 4 regressions failed first; focused checks and **594 full-suite tests passed** |
| Partial-body/CSRF evidence controls and demo API | [f297db3](https://github.com/jderomanis1/chassis/commit/f297db302150cc2f991c84e97b0234ab2e9b0828) | 3 evidence checks failed first; **4 focused checks passed**, then the **50-test leak run passed** |

The initial 576-test baseline also passed. Its ordinary in-tree collection
worked in this environment; a deliberately reversed conftest search order
reproduced the reported import collision. Moving issue/EphemeralToken/git into
`tests/portal/helpers.py` removes that dependency without weakening assertions.

C-1 rejects all binds except 127.0.0.1 (localhost normalizes to it), even with the
legacy override set. Normal etags stay unchanged after hidden uncommitted edits,
hidden commits, and unrelated documentation commits; privileged etags observe
hidden edits when authorized. Visible changes still refresh and concurrent-read
retry remains tested. A real index symlink returns generic internal_error over
all three MCP read tools, with no absolute path in protocol or stderr. Six
handler tests cover the error mapping for every tool.

C0 checks current versions throughout snapshot/detail/graph responses, task
next_step, and the exact session shape. CSRF is fresh per app launch, stable
within it, absent from disk/audit, and distinct from the viewer credential.
The session is subject to the existing Host/Origin/method/identity checks.
Writes remain disabled and there is no PATCH or layout endpoint.

C3 generates 7 ventures, 14 initiatives, 42 tasks, and 29 dependency edges,
including one cross-venture edge and one restricted task. CLI validate passes
all 63 records. Normal API viewers see 62 nodes and 41 tasks, with 7 venture
cards and green/yellow/red health. Existing destinations are refused. Only token
hashes persist, mode 0600; no credentials enter the single fictional baseline
commit. A normal editor's library update succeeds and its restricted update is
refused. This is backend/library evidence, not a canvas edit demonstration.

### Expanded restricted-content probe

The 50-test CLI/MCP/portal run passed in **34.44s**. It checks raw and JSON-escaped
restricted id, title, owner, full body, and a partial body sentence. A planted
partial snippet is detected by a positive regression. Session responses are
checked in memory before CSRF redaction for evidence capture.

| Surface | Captured files | Output segments | Literal matches |
| :--- | ---: | ---: | ---: |
| CLI | 3 | 66 | **0** |
| Real stdio MCP | 10 | 90 | **0** |
| Portal API, including session and demo vault | 16 | 42 | **0** |
| Total | **29** | **198** | **0** |

Reproduce after `uv sync --locked --all-extras`:

```bash
PYTHONPATH=evidence CHASSIS_LEAK_PROBE_DIR=/tmp/chassis-step7-leaks \
  .venv/bin/pytest -q -p step6_leak_probe \
  tests/test_security_cli.py tests/test_mcp_read_security.py \
  tests/portal/test_api.py tests/portal/test_graph_search.py \
  tests/portal/test_boundary.py tests/portal/test_static.py \
  tests/portal/test_session.py tests/portal/test_demo.py
```

### Open gates

The approved prototype index/README/tokens/screens, SECOPS-STEP6.md section 4,
ANDY-CHECK-02.md, and CODEX_STEP6_REPORT.md were not provided or located. The
older ADR and SecOps checkpoint are available and are not substitutes for them.
No write branch, C1/C2 implementation, frontend build, Playwright run, screenshot,
UI/MCP live loop, npm/license check, or DOM/layout/bundle leak pass is claimed.
C1/C2 still require independent SecOps review before merging to main.

All commits were published with an expected-parent check and no force, with local
Git tree and reconstructed commit-object hashes matching the remote objects.
Joe's reported Step 6 reviews remain distinct from these engineering checks.
No independent Step 7 Code Reviewer, QE, or SecOps signoff is claimed. Continue
only Step 7 once its required sources are supplied; no real data or deployment.

## Step 6 executed checks

Started from accepted private `main` at **`384931f23562bbf23b39451953874cb18d8df311`**.
Joe supplied Code Reviewer PASS WITH NITS and QE PASS, including 431 tests twice
and M9 20/20, as the accepted Step 5 evidence. Those are not new Step 6 review verdicts.
The supplied [portal ADR](../docs/PORTAL-ADR.md) and
[SecOps checkpoint](SECOPS-CHECKPOINT-1.md) were read before implementation.
Joe's decision overrides ADR masking: unauthorized restricted rows are absent,
including their status, existence placeholders, relations, counts, and health inputs.

Final runtime/test revision: **`7d152c51e8e123c860067e08e94e24c6bba5347f`**.
It includes the final-review fix for hidden parser diagnostics and the ADR's P1
package static mount. The final development run passed **576 tests in 53.23s**.
Three new detached checkouts of this
exact revision then installed from `uv.lock`, starting without a virtual environment.
The [verification JSON](step6-verification.json) records results without bodies or credentials.

| Clean-checkout installation | Full applicable suite | Isolation evidence |
| :--- | :--- | :--- |
| `uv sync --locked --all-extras` | **576 passed in 53.87s** | MCP and portal integration included; no skips |
| `uv sync --locked` | **499 passed, 8 modules skipped in 25.79s** | MCP, Starlette, and uvicorn absent; optional integration modules skip explicitly |
| `uv sync --locked --extra portal` | **542 passed, 7 MCP modules skipped in 29.43s** | MCP absent; portal works independently; one development-only TestClient deprecation warning |
| `uv sync --locked --no-dev`, after the core run | Core/library/CLI imports and CLI help pass | MCP, Starlette, uvicorn, anyio, httpx, and pytest all absent; both optional entry points give install messages with exit 1 and no trace |

The suite command after each install was `.venv/bin/python -m pytest -q`.
All three checkouts retained empty Git status and an unchanged lockfile. Lock SHA-256:
`68c9c88f407c84e838c5db81889db37dbb4d378229c0603c58c3c22573640932`.
Runtime: Linux/POSIX, Python 3.12.14, MCP 2.3.0, Starlette 1.10.0, uvicorn 0.54.0.

### SecOps evidence: S1–S6

| Requirement | Observed result and executable evidence |
| :--- | :--- |
| S1 default-deny reads and grants | `test_read_security.py`, `test_mcp_read_security.py`, and portal boundary tests: unknown/empty identities and missing/wrong tokens return no records; exact venture/type read or write grants scope list/read/search; revocation is rechecked, including under the lock |
| S2 complete hiding | Normal sample viewers see **12 records, 7 tasks, and 2 Acme tasks**. Restricted clearance plus grants sees **13 records and 3 Acme tasks**. Library tests remove hidden parents/descendants and hidden dependency IDs; portal tests confirm no hidden node, edge, search hit, parent count, color, or reason |
| S3 indistinguishable reads and generic write denials | Hidden and missing IDs return the same `not_found`; unauthorized writes contain no venture/type details. Normal writers cannot declassify a restricted record. `test_read_error_safety.py` and real CLI/MCP tests contain hidden schema/graph diagnostics during reads and all write paths |
| S4 body-free audit | One JSON line per public library operation records UTC time, agent, tool, outcome, and returned IDs or counts. Tests assert entries, exact call sequences, no bodies/tokens, symlink refusal, read refusal on append failure, and retained post-commit recovery metadata |
| S5 proven identity | `test_agent_tokens.py`: local create/rotation prints once, stores SHA-256 only with mode 0600, and keeps credentials ignored. Missing/wrong tokens deny access; startup rejects invalid MCP/portal viewers. Tests generate ephemeral credentials at runtime; no reusable token literals are committed |
| S6 actual transport checks | All six tools exercised with real stdio subprocesses. Normal caller output and audit are leak-scanned; restricted/scoped callers and live revocation are verified. Additional real stdio cases use each protected field as an invalid hidden source key and verify generic results across all six tools |

`agents.yaml` now defaults clearance to normal and unknown agents to deny. The
sample chief-of-staff explicitly has restricted clearance; the reviewer does not.
The only record change in Step 6 gives the restricted fixture a unique fictional
owner, making an owner-string leak scan meaningful instead of matching a public
row that previously shared that name. No real venture data was added.

Final review found a real cause-chain leak: the tool formatter could traverse a
generic library error into its private Pydantic cause. Five first regressions
failed, including real stdio tests for id, title, owner, and body. The separate
`4854431` fix cuts that cause at the library boundary, contains whole-vault write
validation, and denies unreadable target metadata generically. A legacy human
commit test now expects the generic source error while retaining its unchanged
bytes and no-commit assertions. The final full suites include these regressions.

### Literal restricted-content leak grep

The separate evidence run passed **47 tests in 16.80s** at `7d152c5`. The
[probe](step6_leak_probe.py) observes the tests' actual normal-caller output and
runs `rg --fixed-strings --multiline --files-with-matches` against the restricted
id, title, owner, and complete body, including their JSON-escaped forms. It checks
stdout/stderr, real MCP wire output and audit, and every portal endpoint. It also
captures hidden schema/graph error paths and static-path refusals. Every grep
returned 1, meaning no match.

| Surface | Captured files | Output segments | Literal matches |
| :--- | ---: | ---: | ---: |
| CLI record operations, including validation/rebuild and write refusals | 3 | 66 | **0** |
| Real stdio MCP, startup refusals, audit, and malformed hidden-source paths | 10 | 90 | **0** |
| Portal endpoints, graph, generic errors, and static-path refusals | 12 | 30 | **0** |
| Total | **25** | **186** | **0** |

The committed report contains counts and provenance only. Raw captures remain
temporary sample-data artifacts. Reproduce from the repo with `rg` installed:

```bash
uv sync --locked --all-extras
PYTHONPATH=evidence CHASSIS_LEAK_PROBE_DIR=/tmp/chassis-step6-leaks \
  .venv/bin/python -m pytest -q -p step6_leak_probe \
  tests/test_security_cli.py tests/test_mcp_read_security.py \
  tests/portal/test_api.py tests/portal/test_graph_search.py \
  tests/portal/test_boundary.py tests/portal/test_static.py
```

### Part A and portal P1–P4

| Check | Observed result |
| :--- | :--- |
| Optional MCP and exact assertions | `mcp = ["mcp>=2.3,<3"]` is an extra; minimal core imports without it. Missing-extra messages verified on installed commands; MCP result assertions use exact expected values |
| Stdio hardening | Malformed JSON produces -32700; default 1 MiB and configured caps produce structured oversize errors; bounded input recovers; SIGTERM during a real active write leaves no orphan children and frees the lock |
| P1 server and version | Only Starlette and uvicorn are portal runtime extras. Bind refusal, configured authenticated viewer, etag after commit/edit, ignored audit/cache stability, and a real uvicorn loopback GET/shutdown pass. Package-only static serving refuses vault/policy/token paths; the wheel contains the empty asset directory |
| P2 API v1 | Exact snapshot/card, venture/initiative, GTM/progress, and task shapes pass. Counts derive from library-visible rows. A concurrent commit retries rather than labeling old data with a new etag. "Agent writes today" is omitted |
| P3 health | Frozen Phoenix clock tables cover first-match task rules, 3/7/14-day boundaries, parent milestones, unknown/completed children, and waiting_on without a color change. HTTP tests prove hidden children add no color/reason |
| P4 graph/search/errors | Exact neutral node/edge and search-hit shapes; dependency direction/blocking; no layout or masked nodes. Hidden/missing scopes have identical not_found responses. Invalid IDs and internal failures use generic envelopes without traces |
| HTTP boundary | All six routes accept GET only; POST/PUT/PATCH/DELETE/OPTIONS/HEAD are refused. Host/Origin mismatch and token revocation are refused. GET `/api/ask` is 404; no ask endpoint exists |
| Previous acceptance gates | AC2/3/4/9 remain green, including real-process and real-MCP concurrency tests. The Step 5 M9 20/20 report was not repeated as a separate 20-run batch in this step |

### Publication record and limits

| Increment | Private main commit | Full suite after increment |
| :--- | :--- | ---: |
| A: optional MCP and hardening | `a02e37d5b79527ad9bedf8cdaeddb17291617474` | 437 |
| S: library read security | `f4064874eeadb910fa004ba6ea656c19eab4f0aa` | 466 |
| P1: local authenticated portal server | `3ee59cbd0a0b76c48d47d43276d52c6f9149bea9` | 476 |
| P2: snapshot and drilldowns | `9a80d954ac7606eb4f1d6a940a000beac6989163` | 482 |
| P3: pure health | `82e4691b2d9ca0bfd444970fbd55fb936b1dd24b` | 532 |
| P4: graph, search, and HTTP boundaries | `bf270b374d7e6b651f5d86102ab02baba6e86780` | 559 |
| Final review: hidden source error containment | `4854431f43ea73a7c5c4c4a00471cc191b59a331` | 575 |
| P1 follow-up: package static mount and API fallback | `7d152c51e8e123c860067e08e94e24c6bba5347f` | 576 |

Each implementation part was published separately with an expected-parent check,
no force push, and Git tree/object identity verification. S preceded every portal
implementation commit. P2 tests first failed on absent endpoints; P3 on the absent
health module and then an explicit empty-parent rule; P4 on missing routes and
validation behavior. Required exception-path regressions failed before their fix.
Subsequent closing commits update documentation, evidence tooling, and handoff only.

**Real data and agent-to-agent channels remain NO-GO pending SecOps review.**
Local token/grant/clearance controls do not encrypt Markdown, Git history, or the
cache, and do not authenticate separate browser users. Remaining checkpoint work
includes disclosure/prompt-injection boundaries, rate limits, and retention,
backups, encryption, and hosted authentication. POSIX locking and existing
ordinary-editor/file-versus-Git crash boundaries remain. No independent Step 6
Code Reviewer, QE, or SecOps verdict is claimed here.

No frontend, browser/UI, Playwright, model ask, live Miro, real-data, or deployment
check was run or claimed. Stop at Step 6. The next named step is the approved
frontend port P5–P8, with escaped record content, empty/loading/error states, and
Playwright tests against the approved prototype and backend.

## Step 5 executed checks (historical)

Start: accepted `main` at **`a26a093f959824a0df4db3a79433fc39fc17c1bc`**.
Remote HEAD matched that SHA and the existing working tree was clean. The uploaded
handoff was the older Step 1 snapshot; current repository guidance and Joe's Step 5
request governed. The accepted 343-test baseline was rerun and passed in 13.32s.

Part A fixes were pushed separately as **`c3cb10680a8853a8447ec3ba4df9dc427bcb7b7a`**.
Part B portal fields were pushed separately as **`42a80567a24cda55d4b19292800108851923e810`**.
Final runtime/test checkpoint: **`6ab3b14a759e1e3d5f8e9beae08bf8943b7c8d5d`**.
Connection documentation and the real session transcript follow at **`b2fc347`**.

Final verification used a fresh detached worktree at `6ab3b14`, initially containing
neither `.venv` nor `.chassis`. Runtime: Python 3.12.14, Linux, official MCP SDK
2.3.0. Subsequent commits change documentation/evidence only.

| Check | Observed result |
| :--- | :--- |
| `uv sync --locked` | Passed from the clean checkout; committed dependency lock unchanged |
| `uv run pytest -q` | **431 passed in 29.94s** |
| `uv run chassis validate` | 13 records, 2 ventures, 3 initiatives, 8 tasks, 2 dependencies |
| `uv run chassis index rebuild` | All 13 authoritative records indexed |
| Clean checkout/source boundary | Empty Git status and `git diff --exit-code`; sample policy unchanged from `a26a093`; only sample-record change is Ridgeview's required blocker reason |
| Installed entry point | Clean environment's `.venv/bin/chassis-mcp --help` exited successfully |
| Part A metadata | Owner, sensitivity, and assignment rejected before expansion when invalid; same record constraints used; valid metadata roundtrips |
| Part A placeholders | FIXME, XXX, fullwidth/compatibility tokens and letters rejected after NFKC matching; no file/cache/commit changes |
| Portal schema | Strict date-only parsing; fields scoped to record types; blocked reason required and must be cleared on unblocking; derived activity rejected as source metadata |
| Migration/index/filters | Optional fields may be omitted; old cache schema rebuilds; stored portal-field filters through library/CLI and null activity filtering pass; existing blocked fixture migrated |
| Git activity | Agent and human commits count; uncommitted/unrelated changes do not advance activity; byte/mtime-identical restore still refreshes; no history yields null |
| Earlier gates | AC3, AC4, and AC9 regressions remain green, including real-process races and crash recovery |

### AC2: real stdio process and client proof

The adapter uses the official Python SDK, not a simulated server. The acceptance
client launches a real subprocess, sends newline-delimited JSON-RPC over stdin,
and parses every stdout line. Its single session initializes protocol `2025-11-25`,
lists exactly six tools, and exercises every operation. A separate official SDK
`Client` also connects to a real stdio process, lists tools, and reads a record.
No in-process transport supplies these results.

| Required proof | Observed result and executable location |
| :--- | :--- |
| M1 initialize and tools/list | `tests/test_mcp_stdio.py`: one client initializes, lists exactly the six named tools, and verifies strict schemas without caller identity arguments |
| M2 six tools end to end | `tests/test_mcp_session.py::test_real_stdio_session_all_six_tools`: list/read/search/create/template/update on one client; each of the three writes has exactly one parent-to-child, record-only commit by `Fictional Homer <homer@chassis.local>` |
| M3 stale version | Same session returns `conflict`, expected version 1/current version 2; all record bytes, cache bytes, and HEAD unchanged |
| M4 invalid input | Same session returns `validation` with field `due_at` and a reason, with unchanged records/cache/HEAD; strict argument/schema and impersonation refusals also pass |
| M5 existing protections | `tests/test_mcp_refusals.py`: dirty/staged targets, unchanged/edited skip-worktree and assume-unchanged flags, unknown/read-only/wrong-scope callers, missing/invalid/revoked policy, and a symlink lock are refused through MCP |
| M5 shared lock | `tests/test_mcp_concurrency.py`: both server handlers begin their writes while another process holds the real vault lock; neither returns or writes until release |
| M6 protocol-clean stdout | `tests/mcp_client.py` parses every stdout line as JSON-RPC; the full session also verifies startup, all six tool logs, and shutdown appear on stderr |
| M7 shutdown | Closing client stdin ends each tested server with exit 0; its process group has no survivors; the kernel lock can be reacquired immediately; no Git index lock or write temp remains |
| M8 recorded session | `evidence/mcp-session.jsonl`: 25 actual wire messages, including initialization, tools/list, all six tools, stale/invalid/missing refusals; no environment secrets |
| M9 two-client race | Two real server subprocesses with distinct fictional author names race expected version 1: exactly one success, one structured conflict/current version 2, one record-only commit, and matching winning source/index/author |
| Error safety/recovery | `tests/test_mcp_error_safety.py`: a real rejecting Git hook's traceback stays on stderr; record rollback holds; committed/unknown outcome details survive error mapping |

The persistent `.chassis/write.lock` file is the stable shared inode, not an active
lock. Tests verify release of the kernel lock; they intentionally do not unlink
the inode, which would let concurrent waiters lock different files.

### Transcript provenance

The clean checkout ran the full-session test again with
`CHASSIS_MCP_TRANSCRIPT` pointing to the evidence file: **1 passed in 1.56s**.
The recorder saved actual requests/responses rather than constructing a sample
conversation. There are 13 client messages (including the initialized notification)
and 12 server responses; request/response IDs pair exactly. All six tool names
appear. Size: 22,403 bytes. SHA-256:
`5a9f2d35b232837c766f71b8c98d8e72316e91967fec0df43fc14320c36bd07c`.

### Test-first and publication record

Eighteen Part A regressions failed before the fix. Ten portal-schema checks and
eight index/activity checks failed before their implementations. Handler tests
first failed on the absent module; both initial subprocess tests failed before
the server existed. Later end-to-end/refusal tests exercised the shared paths
without introducing another persistence implementation. The two-client race passed;
three final diagnostic/recovery regressions failed before the containment fix.

| Increment | Published commit | Full-suite tests after increment |
| :--- | :--- | ---: |
| Part A, separately | `c3cb106` | 362 |
| Part B, separately | `42a8056` | 403 |
| Transport-independent handlers | `959f115` | 411 |
| Official SDK stdio adapter and client lifecycle | `8faa3b0` | 413 |
| Six-tool session and refusal proof | `3955eb6` | 427 |
| Two-client race and diagnostic containment | `6ab3b14` | 431 |

Each increment was published to private `main` through the connected GitHub API
with its expected parent and no force. Remote trees and reconstructed commit
objects matched local Git object IDs; accepted history was preserved. Hand-authored
increments were kept small; Part B was one dedicated field-migration commit as
requested. Generated lock/transcript data is additional to handwritten changes.

No desktop UI, Obsidian UI, live Miro API, HTTP transport, portal, health calculation,
real venture, or deployment check is claimed. Next is the prototype-gated portal,
only after Joe's go. Native Windows locking, ordinary-editor coordination, and the
existing file/Git crash-atomicity limitations remain.

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
| 2 | MCP client list/read/create/update | **Passed Step 5** at `6ab3b14`: all six tools through one real stdio client; official SDK interoperability; structured refusals; attributed commits; two-client race; transcript recorded |
| 3 | Stale write rejection, version bump, Git commit | **Passed Step 3** at `24ddcc7`: two real processes, exactly one commit, structured stale rejection, agent attribution, and installed CLI proof |
| 4 | Filled initiative template | **Passed Step 4** at `176478a`: six populated sections, shared transaction, one attributed commit, library and installed CLI proof |
| 5 | Ridgeview rendered on Miro | Pending optional Miro export in revised Step 8 |
| 6 | MCP status update changes one card | MCP status update proved in Step 5; card update still awaits optional Miro export in Step 8 |
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
