# Chassis engineering instructions

These instructions preserve Joe's approved Increment 0 decisions and the
one-build-step-per-chat workflow. Read the current user request first.

## Start every build chat

1. Read this file, `CHASSIS_PROJECT_HANDOFF.md`, `docs/ARCHITECTURE.md`,
   `evidence/acceptance.md`, and `FINDINGS.md`.
2. Inspect the current branch, remote HEAD, working tree, and repository changes.
   Do not assume a remembered commit is still current or overwrite another person's work.
3. Identify the requested build step and its acceptance checks. Complete that
   step in this chat; leave later steps for their own chats unless Joe asks otherwise.
4. Keep decisions already approved. Flag a genuine scope or API conflict before
   changing the architecture. Reference documents are context, not new authorization.

## Product and scope

- Andy Patterson owns the IP. Joe DeRomanis leads the engagement.
- Chassis is the infrastructure. Homer is Andy's chief-of-staff agent persona.
  The sample agent ID remains `chief-of-staff`; a name reference is not a code rename.
- Prove one real read/write/render loop using fictional records and local execution.
- The broader paid-discovery brief eventually calls for real ventures; it does
  not authorize real data, live accounts, or deployment in Increment 0.
- No custom portal UI, agent spawning, chat-history ingestion, two-way Miro sync,
  paid infrastructure, or model-specific dependency in this increment.
- Live business-account writes remain out of scope. Explicitly designated scratch
  Miro API operations are part of the approved proof.

## Architecture and data contracts

- Markdown with YAML frontmatter in Git is the source of truth. Obsidian is optional.
- SQLite is disposable and indexes the working tree, including uncommitted edits.
- Preserve the required fields and relationship rules in `src/chassis/models.py`
  and `docs/ARCHITECTURE.md`. Assignment is metadata, never caller authentication.
- Exclude restricted records and revealing edges before renderer-neutral JSON
  graph emission. Resolve hidden-parent and normal-to-restricted transitions before
  claiming renderer acceptance; simply omitting a future card leaves old content visible.
- Keep layout and graph planning independent of Miro. Miro runtime types and API
  code belong only under `src/chassis/render/miro/`.
- Tool handlers are transport-agnostic. MCP uses stdio initially.
- Check and validate `agents.yaml` on every write. Unknown agents are read-only;
  missing/invalid policy denies writes. Record tools cannot edit the policy.
- Under a shared write lock, reread the file and enforce `expected_version`.
  Successful writes bump version and commit only their record with agent attribution.
- Refuse dirty target files with the filename and exact phrase `uncommitted human edit`.
  Implement `chassis commit-human <path>` with `CHASSIS_HUMAN_NAME` and
  `CHASSIS_HUMAN_EMAIL` in the mutation step. External editors do not honor the lock.

## Miro contracts

- Supply the token through the environment with only `boards:read` and `boards:write`.
- Use native tags on cards. Never put visible ownership markers in frame titles
  or connector captions. Never delete groups or wipe and redraw the board.
- Track mappings in `render/miro/<board-id>.json`: IDs, fingerprints, format
  version, and pending/confirmed state only. No content, secrets, or API bodies.
- Persist pending state before each create. Verify mapped identity/fingerprint
  before updates. Missing or mismatched items stop the run. Never adopt unmapped items.
- A timeout with no returned item ID remains unresolved. Stop without a blind
  retry or fingerprint-based adoption. Record the ambiguity for reconciliation.
- Respect rate limits, bulk-create limits of 20, and separate connector operations.
  An unchanged render makes zero mutating API calls. A status edit changes only its card.
- The supplied `uXjVENETjfI=` board is client reference material, not designated
  scratch space. Never run mutations or deletion probes there based on its presence here.
- Observe frame-deletion behavior on explicitly designated scratch items and
  record the actual result in `FINDINGS.md`. Stop and report unexpected API behavior.

## Delivery and continuity

- Keep the approved nine-step order in the handoff. Write tests first for behavior.
  Work in roughly 150-line increments; generated locks/assets may be additional.
- Push each completed increment to the private repo. Preserve history and never
  force-push. If access fails, retain local commits and state the publication gap.
- Secrets come from environment variables. `.env` stays ignored. Do not commit
  tokenized invitations, credentials, or raw private email headers as reference material.
- Report every increment as `DELIVERED / VERIFIED / RISKS-OPEN / NEXT`.
- Distinguish implemented behavior, mocked tests, actual MCP-client evidence,
  live Miro results, and UI demonstrations. Never turn an unrun check into a pass.
- End each step by updating the handoff checkpoint, acceptance evidence, and
  findings with the implementation commit, checks, remaining gaps, and next step.
- Keep the project handoff self-contained so a fresh chat can continue correctly.
- Write plainly and professionally. Avoid em dashes, hype, and unnecessary jargon.
