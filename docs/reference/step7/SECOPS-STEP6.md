# Chassis SecOps Step 6

Pinned: `523a8a58b9a28c9d977d0512b14fc4b995ac5d21` (docs close of runtime `7d152c51e8e123c860067e08e94e24c6bba5347f`).
Reviewed 2026-11-17, 8:48 AM MST (America/Phoenix).
Read-only. No pushes, no PRs, no deploys, no signups, no outside contact.
Codex evidence in `evidence/acceptance.md#secops-evidence-s1s6` was treated as claims, not a verdict.

**Verdict: S1-S6 are GO for the local, sample-data backend.**
The checkpoint-1 read-path failures are closed in this tree.
**Real Andy data remains NO-GO** until the canvas write endpoint is built to section 4 and the should-fix items below are addressed.
**A Chassis bot in the Grok app is NOT APPROVED.** It is a design-review item (section 5). Sample canvas work may continue on this backend.

---

## 1. How this was verified

Files were fetched via the GitHub MCP (`user-GitHub-xai` `get_file_contents` and `get_repository_tree` at `523a8a5`). A /tmp tree was assembled only from blobs whose `git hash-object` matched the official tree: 106 files, including all `src/`, `tests/`, `records/`, `templates/`, `agents.yaml`, `pyproject.toml`, and the updated `records/tasks/task-launch-budget.md` (`acbcaf53`). Key security blobs matched: `policy.py` `b0f25839`, `identity.py` `7c9fd108`, `audit.py` `41e4ae01`, `index.py` `a00c119d`, `tool_handlers.py` `9845c02c`, `store.py` `d84c3e62`, `mcp_transport.py` `12594974`, `portal/app.py` `5f77a879`, `portal/config.py` `b9f66991`.

Tests ran offline against that tree with `PYTHONPATH=src` and an existing local venv (`mcp 2.3.0`, `starlette 1.10.0`, `uvicorn 0.54.0`):

- Official suite: **576 passed in 53.37s**.
- Official leak probe (`PYTHONPATH=evidence CHASSIS_LEAK_PROBE_DIR=... pytest -p step6_leak_probe` on the six files named in the evidence): **47 passed in 16.43s**, 25 capture files (3 CLI, 10 MCP, 12 portal), **0 literal matches** for the restricted id, title, owner, and body (raw and JSON-escaped). `rg` exit 1 on every file.
- Independent checkpoint-1 attack set (`/tmp/secops-s6-attacks.py`): **9 passed**. Empty, unknown, wrong-token, and cross-agent token spoofing are denied. Reviewer sees 12 records; chief-of-staff sees 13, including `task-launch-budget`. Search is not a body oracle for a normal-clearance caller. Hidden and missing `read_record` responses are identical `not_found`. Write refusals are the generic `Write not permitted` / `unauthorized` for hidden, missing, and out-of-scope targets. Tool arguments cannot supply identity (`extra=forbid`). Audit lines have only `time`, `agent_id`, `tool`, `outcome`, and `count` or `record_ids`; no bodies, tokens, or hidden ids. Token file is mode 0600 and stores SHA-256 only. Portal: wrong `Host` 403, cross-origin GET 403, form POST and JSON POST 405, no `Access-Control-*` headers, snapshot hides the restricted record. `validate_bind("0.0.0.0")` raises unless the remote-bind escape hatch is set.

---

## 2. Evidence claims

Reproduced:

- S1-S5 library controls (deny by default, token auth, library-level restricted hide with no row/count/status/edge/search hit/error oracle, generic write denial, body-free audit).
- S6 official MCP 2.3.0 adapter and GET-only loopback portal with Host/Origin checks.
- Full suite **576 passed** (53.37s vs claimed 53.23s / 53.87s).
- Leak probe **47 passed**, 25 files, **0 matches** (16.43s vs claimed 16.8s).
- Visible totals: reviewer 12 records (7 tasks, 2 Acme tasks); restricted-clearance 13 (8 tasks, 3 Acme tasks). Restricted owner is now unique (`Fictional Private Reviewer`).

Not reproduced in this pass (environment limits, not contradictions):

- `uv sync --locked` core matrix **499 passed, 8 modules skipped**, and `--extra portal` **542 passed, 7 MCP modules skipped**. Extras were already present in the venv used; packages were not uninstalled, and `uv.lock` was not independently hash-matched (the official recursive tree fetch truncated before that path).
- Minimal-core `--no-dev` import and wheel-asset checks were not re-run.
- The Step 5 M9 20-run batch was not repeated; the evidence already discloses that.

No evidence security claim that I did re-run failed.

---

## 3. S1-S6 findings

No blockers in this backend for local sample-data use.

### Should fix

1. Remote-bind escape hatch. `validate_bind` allows any host when `CHASSIS_PORTAL_ALLOW_REMOTE=1` (`src/chassis/portal/config.py:21-29`, `cli.py` `--host` default 127.0.0.1). That can bind `0.0.0.0` and publish the authenticated-viewer API. Do not carry this override into the write-enabled canvas. Bind `127.0.0.1` only, with no env escape hatch, before real data or any mutating route.

2. Version etag is a hidden-edit oracle. `version_etag` hashes every cached or untracked, non-ignored path, including restricted records the viewer cannot see (`src/chassis/portal/config.py:49-61`, used by `/api/version` and `read_state` in `src/chassis/portal/api.py:21-29`). A normal-clearance canvas that polls the etag can learn that a hidden record changed. Compute a per-viewer etag over `visible_records` only (or over the already-filtered snapshot payload).

### Note

1. `chassis agent-token create` is an unauthenticated local operator command (`src/chassis/identity.py:46-64`, `src/chassis/cli.py` `agent-token`). Anyone who can run it in the vault can mint a `chief-of-staff` token. That matches a single-user laptop. For real data, keep the vault directory mode 0700, and document that token issuance is an operator action, not an agent tool.

2. Tokens are unsalted SHA-256 of a 32-byte `token_urlsafe` secret, compared with `hmac.compare_digest` (`src/chassis/identity.py:34-43,60-63`). Entropy is enough; a salt is optional.

3. Joe's hide rule means a parent's health and `waiting_on` omit hidden children (`src/chassis/portal/health.py:80-110`, `src/chassis/policy.py:63-71`). A restricted blocked child will not redden a parent for a normal-clearance viewer. That is the accepted tradeoff, not a leak.

4. Missing `Origin` is allowed on GET (`src/chassis/portal/app.py:51-52`). That is acceptable for read-only GET. The write endpoint must reject a missing Origin (section 4).

5. Record `body` still has no size cap (`src/chassis/store.py:96-97`, `models.py` has no body max_length). Add a limit on the canvas write schema, and prefer the same cap in the library write path before real data.

6. Restricted markdown remains plaintext on disk, in Git, in Obsidian, and in `.chassis/index.sqlite`. S1-S6 protect MCP, CLI, and the portal for a configured agent. They do not protect another process of the same OS user.

---

## 4. Requirements for the one local canvas write endpoint

The step 7 prompt calls this a gated local PATCH; this review was asked for a POST. The rules apply to the single mutating HTTP route, whatever the verb. Implement it in the portal process, then call `RecordStore.update_record` (or the existing library write path) with the S1-S5 identity already bound at launch. Never take agent id or token from the request body (`src/chassis/tool_handlers.py:70-74,116-120`; `src/chassis/store.py:84-86,99-103`).

Build and test every item before merging to the main branch and before any real data:

1. Bind `127.0.0.1` only, never `0.0.0.0`. Remove or hard-fail `CHASSIS_PORTAL_ALLOW_REMOTE` (`src/chassis/portal/config.py:21-29`). Test: process listen address is loopback; bind to `0.0.0.0` fails.

2. Host header allowlist against DNS rebinding. Keep the exact `host:port` check already used for GET (`src/chassis/portal/app.py:47-53`). Test: `Host: evil.example:<port>` is 403 even when it resolves to loopback.

3. Strict Origin check on the write route: exact match to `http://127.0.0.1:<port>` (and IPv6 loopback if you bind it). A missing Origin is rejected on POST/PATCH. Also require `Sec-Fetch-Site: same-origin` when the header is present; reject `cross-site` and `same-site`. Test: cross-origin POST is 403; missing Origin is 403; wrong Site is 403.

4. CSRF token: synchronizer (preferred) or double-submit, tied to a per-launch random session secret. Issue it from `/api/session` over the same origin. Test: missing token, empty token, and token from another launch are 403.

5. `Content-Type` must be exactly `application/json`. That blocks simple-form CSRF. Send no CORS headers at all (no `Access-Control-Allow-Origin`, no `Access-Control-Allow-Credentials`). Test: `application/x-www-form-urlencoded` and `multipart/form-data` POST are 415 or 403 and do not write; response has no `Access-Control-*` headers.

6. If any other local process must call the endpoint, require a per-launch bearer or launch token in `Authorization`, independent of the Chassis agent token. Do not reuse `CHASSIS_AGENT_TOKEN` in browser JS. Test: missing and wrong bearer are 401/403 and do not write.

7. Server-side authz is the library write path with the launch identity (`authorize_writer`, `require_grant`, `require_clearance`, `_check_scopes`). Request JSON must not contain `agent`, `token`, or a clearance override. Test: body field `agent: chief-of-staff` cannot escalate a reviewer session; out-of-scope and hidden targets return the same generic refusal as missing IDs.

8. Pydantic schema, `extra=forbid`, allowlisted fields only, and size limits (id pattern already in `models.py:10-12`; add a body byte/char cap, bounded title/owner/next_step, max object size). Test: unknown fields 400; oversized body 400; no write.

9. Optimistic concurrency with `expected_version` or an etag. Reuse `update_record`'s version check (`src/chassis/store.py:107-108`). Test: stale version is 409 and does not write.

10. Path and ID validation: `RecordId` only, no path traversal, no raw filesystem paths. Test: `../agents`, URL-encoded slashes, and over-long ids are 400 and do not touch the vault.

11. Canvas output encoding: render strings with `textContent`, never `innerHTML`. Sanitize any markdown before display. Serve a CSP with no `unsafe-inline` and `connect-src 'self'` (and no wildcard hosts). Test: a record body containing `<script>` or markdown image/html does not execute; CSP header is present.

12. Restricted hide applies to canvas reads too: no row, count, status, edge, search hit, or error oracle, including after a write. Use `RecordIndex` / `visible_records` (`src/chassis/index.py:189-235`, `src/chassis/policy.py:57-71`). Test: reviewer snapshot, graph, search, and write errors still have zero hits for the restricted id, title, owner, and body.

13. Audit every write through the existing body-free logger (`src/chassis/audit.py:22-30,49-87`). Test: a successful and a denied write each append an entry with `tool`, `outcome`, and id or count, and the log contains no body or secret.

14. Rate limiting per launch (and per token if a bearer exists), conservative for a local UI (for example a small burst and a low per-minute cap). Test: excess writes are 429 and stop mutating.

Required negative tests, at minimum: cross-origin POST/PATCH, form POST, wrong Host, and missing CSRF (and missing bearer if one is used). Also: missing Origin, wrong `Content-Type`, stale version, hidden vs missing id, and identity-in-body escalation.

The current portal is GET-only (`src/chassis/portal/app.py:48-50`). That is correct until the items above land together.

---

## 5. Grok-app phone path: NOT APPROVED (design review)

A Chassis bot inside the Grok app is a hosted, off-machine path. Andy's phone suggestion does not change that. Do not build, connect, or demo it against any vault, sample or real, until this review is reopened and Joe approves a written design.

Before any approval could be considered:

- Data leaves the local machine, so the hosted-gateway requirements return in full: real auth (not env plus a hashed local token), exact audience, per-request kill switch, short-lived access tokens, and the WorkOS/gateway rules already accepted on HOSTING-GATEWAY-ADR v2.
- Grok's terms, training, retention, and whether a custom or consumer bot is a no-training commercial path are unverified. Do not assume they are safe.
- The bot's tool permissions must be least privilege and read-only by default. Write access would need a separate, explicit approval.
- Record bodies are untrusted input. The bot must treat them as data, wrap them before any model context, and must not follow instructions found in a title, body, or next_step.
- Restricted records must never reach the bot: library hide plus a gateway or policy approval record, same rule as section (c) of the hosting review. `redact()` is not enough.
- The 5:20 PM MST consumer-plan attestation rule applies: Andy's per-app attestation, 90-day fail-closed reconfirm, no feedback buttons, and NDA or third-party data treated as restricted. Personal Grok stays off for all data.
- A lost or stolen phone is a live session and token risk. There must be a revocable grant and a kill switch that actually ends access, including refresh tokens.
- Nothing goes to xAI or any other third party before the user (and Joe, for anything that goes to Andy) explicitly approves that path.

This conflicts with "personal Grok off" and with skipping the hosted gateway for v1. Keep it off the Friday sample demo.

---

## 6. Bottom line

S1-S6 at `523a8a5` hold up under an independent hash-matched retest. The sample local canvas can sit on this backend. Do not load real Andy data, and do not ship or merge the canvas write route, until section 4 and the should-fix items are done and retested. The Grok-app phone path stays NOT APPROVED.
