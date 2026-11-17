# Chassis project chat setup

Use one build-step chat at a time inside the Chassis ChatGPT project. The private
repository is the durable engineering source; project files supply shared context.

## Current continuation

Use the latest next-chat prompt in `CHASSIS_PROJECT_HANDOFF.md`. Step 7 C1/C2 are
on the gated review branch and F1 is partial, blocked by the browser execution
environment. The source pack is supplied. Main remains unchanged pending SecOps.

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
data, live business-account writes, agent spawning, or deployment. Joe authorized Step 7
as a local React Flow command canvas over the Step 6 backend. Follow
docs/STEP7-CANVAS-SCOPE.md; it supersedes the P5–P8 dashboard plan. Keep unauthorized restricted records
completely hidden through the library, including counts, relations, and health.
Canvas view layout is in Step 7; C1/C2 writes require independent SecOps review
before merging to main. Miro is optional export and chat import is a later step. Complete only the named build step.
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

Suggested title: **Chassis Step 7 continuation: gated writes and command canvas**

C-1, C0, and C3 are complete; Step 7 remains open. Copy the full continuation
prompt from [the current handoff](../CHASSIS_PROJECT_HANDOFF.md#next-chat-starting-prompt).
Read [Joe's complete authorization](STEP7-CANVAS-SCOPE.md) and inspect current main.
Preserve every later documentation and evidence commit.

Supply the approved `portal-prototype/` package with `index.html`, `README.md`,
`tokens.json`, and `screens/`, plus `SECOPS-STEP6.md`, `ANDY-CHECK-02.md`, and
`CODEX_STEP6_REPORT.md`. The prototype is the visual source. Its fonts, theme
script, tokens, and contrast check cannot be reconstructed from the backend ADR.
Read the complete SecOps write requirements before implementing C1/C2 on
`step7-c1-write`. The existing authorization covers that work; the independent
SecOps merge gate remains required. Continue F1–F6 on that branch and stop when
Step 7 is complete. No model/ask endpoint, Miro, deployment, or real data.
