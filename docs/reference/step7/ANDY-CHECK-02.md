# Andy Check 02: Andy's 11/16 8:13 PM AZ reply (claude.ai artifact)

Source: Outlook msg received 2026-11-17T04:13:05Z, "Re: Chassis | The build spec + Miro notes". Andy links https://claude.ai/artifact/EbtbrEjoKpGju5Pdj86Zsn ("Chassis - Build Direction & Context") and asks us to confirm soon that we can open it. Box browser opened it with no sign-in (screenshot /workspace/chassis-andy-artifact/top.png). It is a static doc of Andy's notes with his AI advisor "Homer".

## What changed (Andy's decisions)
1. Primary interface = agent-rendered spatial card canvas (the command portal), React Flow-class: drag and rearrange, click to zoom, flick off view, edit in place, parent/child and card-to-card links, no freehand drawing, reconfigurable by voice/prompt ("zoom into a venture", "clear all but active"). "The Tony Stark concept is the draw, not Miro."
2. Miro demoted to optional share/export. The Miro write-fidelity test is no longer load-bearing.
3. Store: endorses plain files in a private repo Andy owns, Obsidian optional.
4. Gateway (orange zone) skipped for the MVP. Desktop/deep work happens inside Chassis. Mobile (~30-40%) goes through a Chassis-connected bot in the native Grok app that writes to the store. Fallback: a manual end-of-day export into a Chassis intake.
5. Direct question: can we prove read > write > render with desktop in Chassis plus mobile via a Grok-hosted bot, with no gateway?
6. Verify ask: confirm a Chassis-connected bot can run inside the native Grok app and write to his store through the connection layer.
7. Next: pin down cost, timeline, and first concrete deliverable, then run the render test.
Signal: Homer called our update the "strongest response of the four developers we've talked to." We are in a competitive field.

## Andy check
1. Moves his loop? Yes, if we pivot the render target from Miro to the portal canvas. Step 8 (portal front end) is now the critical path. Step 7 (Miro probe) drops to optional.
2. Did what Joe said first? Joe said Miro test first. Andy has released us from it, so we need to acknowledge that explicitly.
3. Polish before proof or upkeep risk? Dropping the gateway removes about 10-11 effort-days and the $5,500 add-on, which lowers upkeep. Risk: a canvas UI shown without live store data behind it would read as a "beautiful static mockup". It has to render real store state.
4. Jargon? His notes say "React Flow-class". Our reply can match that but should stay plain.
5. Security story? Simpler with no internet-facing door. The Grok bot path still needs an internet-reachable MCP endpoint (UNVERIFIED), so a small "door" may come back for mobile. Say so honestly.
6. Visual first? Our reply should lead with an updated v5 picture: orange zone removed, Grok mobile bot path added, canvas as the primary window.

## Open / unverified
- Whether the native Grok app can host a custom connected bot that writes through MCP. Homer asserts it; we have not verified it. A remote MCP connector normally needs a public HTTPS endpoint with auth, which is a slimmer version of the gateway.
- Voice reconfiguration scope for the mock.
- Cost and timeline restated without the gateway. Joe's Fri Nov 20 mock commitment stands.
