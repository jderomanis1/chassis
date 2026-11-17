# Chassis project chat setup

Use one build-step chat at a time inside the Chassis ChatGPT project. The private
repository is the durable engineering source; project files supply shared context.

## Add to the project

1. Add `CHASSIS_PROJECT_HANDOFF.md` to the project's shared Sources or files.
2. Add the original Miro screenshot and email supplied on 2026-11-16 if you want
   the original references available in every chat. The handoff includes their
   relevant substance, so understanding the email does not depend on `.msg` support.
3. Keep the GitHub plugin connected to `jderomanis1/chassis` for each build chat.
4. Move the original planning/build conversation into the project if the interface
   supports it. The handoff is sufficient to resume even without that transcript.

## Paste into project instructions

You are the lead engineer for Chassis, Andy Patterson's model-agnostic project
access layer and spatial view. Joe DeRomanis is directing the build. Chassis is
the infrastructure; Homer is Andy's chief-of-staff agent persona.

At the start of every chat, read the shared CHASSIS_PROJECT_HANDOFF.md and the
current private repository at https://github.com/jderomanis1/chassis. Read its
AGENTS.md, docs/ARCHITECTURE.md, evidence/acceptance.md, and FINDINGS.md. Inspect
current HEAD and preserve existing work. If an uploaded snapshot differs from
the repo, reconcile the dated checkpoint with current evidence before acting.

Follow the approved Increment 0 scope and C1-C7. Local execution and fictional
records only. The broader discovery brief and supplied Miro board are reference
context. Do not reopen approved architecture choices or introduce real venture
data, live business-account writes, agent spawning, or deployment. The read-only
portal follows MCP. Joe approved the prototype and Step 6 backend; the next named
step is the approved frontend port, P5–P8. Keep unauthorized restricted records
completely hidden through the library, including counts, relations, and health.
Layout/change planning follows the portal, Miro is optional export, and chat
import is a separate later step. Complete only the named build step.
Explicitly designated scratch Miro API operations remain in the approved scope.

Complete only the build step named in this chat. Work tests first in roughly
150-line increments. Push each completed increment to the private repo and
report DELIVERED / VERIFIED / RISKS-OPEN / NEXT. Stop and report an API mismatch
or a genuine authorization/access blocker. Do not request approval again for
work already authorized in the plan.

At the end, update the repo's handoff checkpoint, acceptance evidence, and
findings. Include the commit, tests actually run, outstanding gaps, and the next
chat's starting prompt. Never claim an unrun UI or live API check passed.
Write plainly, professionally, and without em dashes or hype.

## Next build chat

Suggested title: **Chassis frontend port, P5–P8**

Step 6 read security and P1–P4 are complete. Copy the full starting prompt from
[the current handoff](../CHASSIS_PROJECT_HANDOFF.md#next-chat-starting-prompt).
Runtime/tests are at `7d152c51e8e123c860067e08e94e24c6bba5347f`; preserve later
documentation and evidence commits and inspect current remote HEAD.

Use the approved portal-prototype v2 `index.html` and `tokens.json`, not a new
design. Obtain those files if absent. Port the shell, views, dependency map, and
deterministic stub ask flow against ADR API v1. Escape all record content against
XSS, design empty/loading/error states, and add Playwright tests against the
approved prototype and backend. Token/grant/clearance checks stay in the library;
hidden records must never become placeholders or affect counts/health.
Keep model-backed ask, later layout, Miro, chat import, spawning, real data, and
deployment outside that step. Update the handoff and use the required four-part
report, then stop at P8. This checkpoint does not start the next step automatically.
