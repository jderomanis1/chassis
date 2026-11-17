# Codex Step 6 report (summary for CoS)
Written 2026-11-17 8:50 AM AZ by Mack's executor. Sources: Joe's pasted Codex handoff (via parent), repo `jderomanis1/chassis` main read through the GitHub connector at 523a8a5 (commit list, CHASSIS_PROJECT_HANDOFF.md first ~20 KB of 32.7 KB, FINDINGS.md first ~20 KB, README, agents.yaml, `src/chassis/portal/{app,api}.py`, `transactions.py`, static folder listing).
Limit: the connector truncated the handoff at about 20 KB, so I could not read its closing "next chat starting prompt" myself. Codex's NEXT below comes from Joe's paste as relayed by the parent. Mark as relayed, not read.

## DELIVERED
| Part | Commit | What |
|---|---|---|
| A (A1 mcp extra, A2 MCP hardening) | a02e37d | mcp optional extra; parse error, payload cap, SIGTERM test, exact asserts |
| S (S1-S6 read security) | f406487, follow-up 4854431 | Deny-by-default read grants, restricted HIDDEN in the library, not_found for unauthorized, body-free audit `.chassis/audit.jsonl`, token-hash identity `chassis agent-token create`. 4854431 fixed a hidden parser-cause leak found in final review |
| P1 app, config, CLI, bind guard, /api/version | 3ee59cb, static mount completed 7d152c5 | 127.0.0.1 only; empty package static dir mounted "for the approved P5 frontend port" |
| P2 snapshot / venture / initiative | 9a80d95 | Counts, progress, GTM sections. "Agent writes today" omitted (not faked) |
| P3 health | 82e4691 | ADR rules, Phoenix clock, 3/7/14-day thresholds, hidden children add nothing |
| P4 graph + search + error envelope | bf270b3 | Neutral graph, search, GET-only with Host/Origin checks |
| Docs / evidence | 16192ab, 523a8a5 | evidence/acceptance.md SecOps section, evidence/step6-verification.json, FINDINGS.md, handoff |

Runtime/test checkpoint: 7d152c5. Docs head: 523a8a5.

## VERIFIED (by Codex, engineering verification only)
| Check | Result |
|---|---|
| All extras, fresh detached checkout | 576 passed (53.87s) |
| Core only | 499 passed, 8 optional modules skipped |
| Portal only | 542 passed, 7 MCP modules skipped, 1 dev-only TestClient deprecation warning |
| `uv sync --locked --no-dev` | Core imports and missing-extra messages OK |
| Leak probe | 47-test run, literal ripgrep over 25 captured CLI/MCP/portal outputs: 0 matches for restricted id/title/owner/body (raw and JSON-escaped) |
| Visibility | Normal viewer: 12 records, 7 tasks, Acme progress total 2. Restricted+grant viewer: 13 records, Acme total 3 |
| No real data, frontend, ask endpoint, model call, Miro call, or deploy | Confirmed by handoff text |

## What I confirmed in the code (relevant to Step 7)
- The portal is strictly GET-only. Middleware in `portal/app.py` returns 405 for any non-GET, 403 on Host mismatch or an Origin other than `http://<bind>:<port>` (a missing Origin is allowed for GET).
- Routes: `/api/version`, `/api/snapshot`, `/api/ventures/{id}`, `/api/initiatives/{id}`, `/api/graph?venture=`, `/api/search?q=`. Headers `Cache-Control: private, no-store` and `nosniff` on every response.
- The portal reads as one configured viewer agent with a token (`config.viewer_agent`, `config.viewer_token`). No write path exists in the portal.
- Task projections (`TASK_FIELDS`) do NOT include `version`, and the snapshot card does not either. Canvas edits need `version` for optimistic writes, so Step 7 must add it.
- No layout/position storage exists anywhere ("position and change planning remain later work").
- No undo function exists in the library. Undo must be a compensating `update_record` (new attributed commit), not a git revert.
- `src/chassis/portal/static/` holds only `.gitkeep`.
- Sample policy: `chief-of-staff` (restricted clearance, write on both ventures) and `reviewer` (read only). Fixtures: Ridgeview HOA (2 initiatives, 5 tasks, 2 edges) and Acme D2C (1 initiative, 3 tasks, 1 restricted).

## RISKS-OPEN
- Real data and agent-to-agent channel: still NO-GO.
- This is Codex verifying its own work. It is not an independent SecOps, QE, or Code Reviewer verdict.
- Portal serves one local viewer only. Store, git history, and SQLite index are plaintext on disk.
- The handoff still describes the "read-only command-center portal" and the P5-P8 dashboard port. Andy's 11/16 pivot (canvas primary, edit in place) is not in the repo docs yet. Step 7 must update them.
- Obsidian UI check is still pending from Step 1 (desktop launch problem).
- Miro AC5-AC8 remain pending; now optional per Andy.

## NEXT (Codex's, as relayed)
P5-P8: port the approved prototype (overview, venture, initiative, map, ask bar) with XSS escaping, empty/loading/error states, and Playwright tests. No frontend, ask endpoint, model calls, Miro, or deploy yet.
CoS disposition: superseded by CODEX_STEP7_CANVAS_PROMPT.md. We keep XSS escaping, states, Playwright, tokens/theme, self-hosted fonts, etag poll, hover cards, keyboard. We replace the dashboard screens with the canvas, defer the ask endpoint, and add a gated local write path.

## Independent reviews still owed for Step 6
Step 6 has not been reviewed by our own lanes. Before Step 7 merges anything that writes, or before anything is called accepted:
1. Code Reviewer: Step 6 diff 384931f..523a8a5, focus on `policy.py`, `identity.py`, `audit.py`, `read_model.py`, `portal/`.
2. QE: fresh-checkout rerun of 576/499/542, and re-run of the 47-test leak probe from `evidence/step6-verification.json`.
3. SecOps: checkpoint 2 on S1-S6 (deny by default, hide, not_found parity, audit body-free, token hashes) and on the 4854431 parser-cause fix.
These can run in parallel with Step 7 F-increments, but C1 (the write endpoint) must not merge before SecOps has looked at it.
