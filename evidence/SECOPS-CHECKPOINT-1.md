# Chassis SecOps Checkpoint 1

Pinned: `384931f23562bbf23b39451953874cb18d8df311` (2026-11-16).
Reviewed 2026-11-16, 4:10 PM MST (America/Phoenix).
Read-only. No pushes, no PRs, no real Andy data, no outside contact.

**Verdict: NO-GO for real Andy data or an agent-to-agent channel.**
Building on fictional sample data can continue.

The write path is in good shape for a local tool: grants are checked server-side, deny-by-default, reloaded under the lock, and covered by tests. The read path is not. `agents.yaml` "read" grants and `sensitivity: restricted` are not enforced on list, read, or search. Caller identity is an environment variable.

---

## 1. MCP auth model

Identity is `CHASSIS_AGENT_ID` from the process environment (`src/chassis/mcp_server.py:62`). The library takes that string as a trusted caller (`src/chassis/tool_handlers.py:54-58`). Whoever launches the process can set any agent ID, including `chief-of-staff`. Tool arguments cannot override it (extra `agent` is rejected). That is not authentication. It is acceptable only while a single trusted human starts a local stdio server against fictional data.

The MCP server accepts an empty agent ID and still serves every read. The CLI write path refuses an empty ID (`src/chassis/cli.py:93-95`); the MCP server does not.

Grants in `agents.yaml` are **not** enforced on every tool, and reads are **not** deny-by-default.

- Write tools call `authorize_writer` and `require_grant`, which require an exact `write` grant (`src/chassis/policy.py:47-64`, `src/chassis/store.py:61-81`). Unknown and read-only agents are denied before record I/O. Tests cover this.
- Read tools call `RecordIndex` with no policy check (`src/chassis/tool_handlers.py:101-109`). `unknown_agent` is hardcoded to `"read"` and cannot be set to deny (`src/chassis/policy.py:24`). `agents.yaml:1` states that runtime enforcement is the mutation layer only.

### What leaks through the read tools

Restricted records are readable through the library, the CLI, and all three MCP read tools. Filtering does not happen at the query, the library, or presentation. `RecordIndex.list_records`, `get_record`, and `search` return the full record plus `body` and `last_activity_at` (`src/chassis/index.py:169-202`). README and `docs/ARCHITECTURE.md` document this: "the index is not an access-control layer"; "restricted records remain readable here"; C2 filtering is planned only for rendered graphs.

Offline tests on a /tmp copy of the sample vault, as `""`, `unknown-agent`, and `reviewer`:

- `read_record` returns title ("Set the internal launch test budget"), owner ("Avery Quinn"), body, `next_step`, IDs, timestamps, parent, venture, and `depends_on` for `task-launch-budget`.
- `list_records` with `sensitivity=restricted` returns that full record.
- `search` on a restricted title or body substring is a content and existence oracle.
- Unfiltered `list_records` returns all 13 records, so counts and relations of restricted rows are visible.

`.chassis/index.sqlite` stores those bodies in plaintext. The vault files and Git history do too. MCP grants cannot protect anyone with filesystem, Obsidian, or `chassis get` access.

### Other read/write notes

- **Should fix:** a caller with a write grant on some other scope can distinguish `not_found` from `unauthorized` on `update_record`. The unauthorized error includes `venture` and `type` (`src/chassis/store.py:36,50-54`; `src/chassis/policy.py:62-64`). Confirmed: `scoped-writer` got `not_found` for a missing ID and `unauthorized` + `venture-acme/task` for `task-launch-budget`. Use one generic refusal for both.
- **Should fix:** no audit log of who read what. `src/chassis/tool_handlers.py:82` logs only `Calling <tool>`. Writes have attributed Git commits; reads have nothing.
- **Note:** path-like IDs fail `RecordId` validation. List filters are allowlisted and parameterized; a SQL-looking value is an exact match, not injection. Symlink guards exist on record and index paths. `assigned_agent` is not used as identity. Record tools cannot edit `agents.yaml`. Git/hook diagnostics are kept off the MCP response (stderr only).

### Remediation (blockers)

1. Treat caller identity as untrusted until it is authenticated (per-agent token or signed identity), not an env var. Refuse empty or unknown IDs at MCP startup. (`src/chassis/mcp_server.py:62`)
2. Enforce grants on every tool, server-side, deny by default. Add `require_read_grant` (or equivalent) and call it from list, read, and search, not only from writes. Allow `unknown_agent: deny`. (`src/chassis/policy.py:24,47-64`; `src/chassis/tool_handlers.py:101-109`)
3. Filter restricted records in the library (index and store), not in a portal `redact()` or in client JS. Unauthorized callers must not see title, owner, body, `next_step`, `blocker_reason`, semantic IDs, or search hits. Decide whether status, counts, parent, and existence are allowed at all; default to hiding the row. Add tests that a `reviewer` without an explicit restricted-read grant cannot obtain those fields by list, read, search, error text, or relations on visible records. (`src/chassis/index.py:172-202`)

---

## 2. Portal restricted-record masking

**Answer:** Showing status while hiding title, owner, and body is an acceptable visual contract for unauthorized viewers, but only if those hidden fields never leave the server. Status plus existence, parent, venture, and counts still leak. The approved prototype is OK as a visual source of truth because it pre-strips the real record. That is not a production authz design.

What the prototype does well:

- The real restricted ID (`task-launch-budget`), title, and body are not in `portal-prototype/index.html`, `tokens.json`, or `README.md`. The placeholder is `restricted-1` (`index.html:439,548`). Semantic IDs would have leaked the topic.
- Hover and detail views do not include title, owner, or body (`index.html:540,611,650`).
- Masking is in the static payload, not a CSS hide of real fields.

What still leaks, even in the prototype:

- A restricted task exists under `initiative-d2c-launch` / `venture-acme`, status `planned`. Acme counts include it (1 initiative, 3 tasks, 1 masked).
- `restricted-1` is in the JS data, `data-task` attributes, and hash routes (`#/...?task=restricted-1` at `index.html:709`).
- The prototype has no portal authentication, no live search, and no export.

Production must-haves for this masking:

- **Should fix:** mask server-side in the same library the MCP uses. Never send title, owner, body, `next_step`, `blocker_reason`, or semantic IDs to the browser and hide them in client JS or hidden DOM. A portal-only `redact()` (as sketched in `PORTAL-ADR.md`) is not enough if `chassis-mcp` or `chassis get` still returns the raw record.
- **Should fix:** do not put real or semantic record IDs in URLs or `data-*` attributes for unauthorized viewers. Hash or ID enumeration would otherwise confirm existence.
- **Should fix:** apply the same library filter to search snippets, ask-the-agent answers, exports, and caches. No CDN or shared cache of a privileged payload. Cache-Control must be private and non-store for authenticated views.
- **Note:** "honest" status and counts are a policy choice. For deal-sensitive work, even "one planned restricted task on this initiative" can be a leak. Default to omitting the row, or to a coarse "some items hidden" with no status breakdown, unless Joe explicitly accepts the leak.
- **Blocker before real data:** the portal itself needs authentication and authorization. The prototype correctly has none.

---

## 3. Must-haves before real Andy data or an agent-to-agent channel

Do not load real records, and do not open an agent-to-agent channel, until all of these are done and tested.

For any real Andy data (MCP, CLI, portal, or vault):

1. **Authn, not env identity.** Per-agent tokens or signed identity. Startup refusal if identity is missing or unknown.
2. **Server-side authz with tests.** Grants enforced on every tool, deny by default, including reads. Tests for reviewer, unknown, empty, spoofed, and wrong-scope callers on list, read, search, and writes.
3. **Restricted filtering in the library layer.** One choke point used by MCP, CLI, portal, graphs, search, and exports.
4. **Audit log.** Who (authenticated ID), what tool, which record IDs, when, and whether access was denied. No secrets in the log.
5. **Secrets handling.** Keep `.env` out of git (already ignored). No tokens in records, chat, or logs. Confirm deploy and log redaction before any hosted process.
6. **Prompt-injection boundaries.** Record bodies and search hits returned to an agent must be wrapped as untrusted data. A disclosure firewall: the model may not exfiltrate restricted fields to another caller, tool, or channel.
7. **Rate limits** on MCP and portal.
8. **Data retention, backups, and encryption at rest.** The vault is plaintext Markdown plus Git history plus an unencrypted index. Encrypt the vault, restrict filesystem permissions, and do not give agents a raw path to it. Define how a restricted record is purged from history if it was written in error.
9. **Disclosure firewall** as a hard product rule: restricted fields never cross a trust boundary (other agents, the portal for unauthorized users, exported boards, logs, or ask-answers) without an explicit grant.

For an agent-to-agent channel, also:

10. **Message authentication** on every inbound message (not a displayed name or env ID).
11. **Allowlists** of peer agents and of tools each peer may invoke.
12. **No tool calls triggered by inbound content.** Inbound text is data, never a command.
13. **Least privilege.** New agent documents already grant no access (`docs/ARCHITECTURE.md`); keep it that way. Start specialists read-only, with no write grants to live records that carry budgets or deals.

---

## Verified

- Source at 384931f via GitHub MCP (`user-GitHub-xai` tree and file reads). Local copies of every `src/chassis/*.py` file and `agents.yaml` were git-hash-matched to that tree and assembled under `/tmp/chassis-secops-384931f`.
- Read of policy, index, store, tool handlers, MCP server, CLI, models, errors, graph, validation, git, markdown, transactions, `agents.yaml`, `.env.example`, `.gitignore`, `docs/ARCHITECTURE.md`, and README.
- Offline ToolHandlers and RecordIndex tests in `/tmp/chassis-secops-vault` (sample records only): 26/26 intended observations matched, including unfiltered restricted reads, search oracle, write existence oracle, path/SQL injection rejection, and the no-op read log.
- Portal prototype `index.html`, `tokens.json`, and `README.md`: real restricted ID/title/body absent; status, parent, counts, and placeholder ID present; no portal auth.

## Could not

- `gh` is unauthenticated, so no full `git clone`. Review used GitHub MCP plus hash-verified local file copies, not a single official checkout.
- Did not rerun the repo's 431 pytest file set (did not fetch the full test tree). Did not start `chassis-mcp` as a stdio process; ToolHandlers is the code the server calls.
- Did not open real Andy data, accounts, or remotes.
- Did not assess a hosted portal deploy; only the static prototype exists.
