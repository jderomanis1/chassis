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
data, live business-account writes, custom UI, agent spawning, or deployment.
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

Suggested title: **Chassis Step 3 safe record mutations**

Step 2 is complete and AC9 passes. Start only after Joe's next go. Copy the full
starting prompt from [the current handoff](../CHASSIS_PROJECT_HANDOFF.md#next-chat-starting-prompt).

Start Step 3 only. Read the current handoff and repository instructions. Step 2
implementation is at `39b5b2ee2efbdc272fdd33b479a4884c6b65cfc7`, with 151 tests
passing from a clean checkout. Preserve later documentation and inspect current HEAD.
Implement local create/update, C3 policy enforcement, C6 version checks and locking,
record-only attributed Git commits, and `chassis commit-human`. Keep templates,
MCP, and Miro in their later steps. Use tests first, small increments, a push after
each completed increment, and the required four-part reports. Update the handoff
and stop at Step 3; this checkpoint does not authorize starting it automatically.
