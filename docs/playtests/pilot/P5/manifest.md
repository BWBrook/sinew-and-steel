# P5 — Rust & Domes pilot manifest

Status: play complete; cross-team audit pending Fable. Normal two-act close at beat 7, with no cap or early-stop intervention.

- Protocol: revision 2, SHA-256 `78bc7e842c6d204c659652d6640958db562b95db698dc6c33447237509597a9b`.
- Rules/harness commit: `b89ad90e0e1f7fd4e9e4b2a402a9a703d40207cb`.
- Orchestrator: Astra in this Codex conversation; exact model ID and reasoning setting not exposed by the available orchestration tools.
- Custodian: `gpt-6-sol`, reasoning `medium`, fresh history; agent `p5_custodian`.
- Players: separate `gpt-6-sol`, reasoning `medium`, fresh histories; `p5_rhea` and `p5_jori`. No player tools permitted by instruction; actual tools/filesystem remain available. This is not enforced isolation.
- Character generation: Rhea Voss seed 510031 with bought M-field sensitive; Jori Vale seed 510032 with bought Life-support technician. Standard 6-point budget. No score rerolls or post-generation adjustments.
- Kit: service pistol (edge +1), reinforced vac-suit (soak 1), tether, water/rations/comm each; Rhea has two reseal patches; Jori has life-support tools and a datapad. No optional Injury, gritty or Wealth module.
- Master dice seed: 51003; Nth dice-drawing command uses 51003000+N; command/receipt evidence is retained. Character seeds are independent of this schedule.
- Setup started (UTC): 2026-10-03T07:47:29.865383+00:00. Public opening recorded 2026-10-03T08:15:02.552757+00:00. Final public reply recorded (UTC): 2026-10-03T08:51:55.943370+00:00. Final snapshot frozen: 2026-10-03T08:53:13.292283+00:00.
- Hidden scenario frozen before play: `playtests/runs/P5/frozen_hidden_scenario.md`, SHA-256 `6902e288e8520dc2b8678afb2be505ac7d3ad3457fbcd244d5d13e8ad8b55716`.
- Initial campaign snapshot: `playtests/runs/P5/initial/`. Final snapshot: `playtests/runs/P5/final/p5_rust/`.
- Public source packets preserved in `playtests/runs/P5/packet_rhea_voss.md` and `packet_jori_vale.md`. Inline delivery used a compact transcription for Rhea and a fuller textual transcription for Jori, with illustrations omitted. This delivery difference is a protocol implementation limitation for the audit, not a claim of byte-identical context.
- Exact public exchanges: `playtests/runs/P5/messages.jsonl` and `transcript.md`. Per-turn checkpoint comparisons: `checkpoint_checks.jsonl`.
- All CLI evidence: `playtests/runs/P5/commands.jsonl`; recorder is P5-local and invokes repository tools unchanged.
- Token usage by role: unavailable from the live collaboration tool; do not infer exact usage from account-level limits. Wall-clock timestamps are recorded; waiting and setup included separately where possible.
- Orchestration interventions during play: none. No rules corrections, stall prompt, malformed-command repair or substituted player decisions. From G004, completed player dialogue accompanied subsequent public relays; before that players received Custodian summaries. This delivery change is recorded in `report.md`. A Custodian debrief was requested only after the final reply and session close.

## Predeclared Custodian policies

# P5 Custodian policies

- **Luck tests:** call one only for pure blind chance, never as a substitute for a character's method. Aim for one or two in this session, with the consequence stated before rolling. Current Luck tokens set the target. No forced test to satisfy a count.
- **Heat purges:** use the skin's actual costs: a credible bribe that loses credits or an item, lying low for an entire session, or a substantive favour for the controlling corp. Declare the cost and amount before applying it, record it through `play.py pressure`, and never erase a crisis's lasting effect with a reset.
- **Shared hazards:** charge Heat once per beat to the party when one storm, delay, or common alarm affects both characters together, rather than once per character. Individual traced hacks, failed covert actions, psi misses, and public gunfire remain individual triggers. At a shared crisis, choose the target the fiction points to and record the consequence before reset. Step-4 risky-test Heat is charged per attempted test under the skin rule.

## Recorded cost and completion evidence

- Setup to first public reply: 27m 32.7s; public opening to final reply: 36m 53.4s; setup to final reply: 64m 26.1s. These are elapsed orchestration times, including waiting, relaying and concurrent P1 audit work, not model compute time. Report production and the external audit fall outside these intervals.
- Per-role compute time, token counts and monetary costs: unavailable for Custodian, Rhea, Jori, orchestrator and future cross-team auditor. Public reply counts are 15, 12 and 11 for Custodian, Rhea and Jori respectively; they are not token estimates.
- Seven recorded beats (four perilous), act breaks at 4 and 7, two finalized PC tests and one opposing NPC result, no combat, no crisis, no Luck spending. One milestone per character at beat 5. Final Heat 1; pools full; two build points banked each.
- All 15 per-reply checkpoint comparisons passed. All 20 log event sequence numbers are consecutive; final event is `session_end`. Final campaign validator returned `ok`. The recorder captured 83 CLI commands with no nonzero exit status.
- New gameplay dice commands used seeds 51003001 and 51003002 in order. Character generation used its separate declared seeds. The preserved command arguments and receipts support replay; narrative is not deterministic.
- Source protocol and frozen scenario hashes remain unchanged. Public transcript SHA-256: `2d658fef3addee36212188f80876de67e83a8aed8f03a9983ac45971e818f027`.
- Recording checks: `playtests/runs/P5/record_checks.json`. Post-session Custodian account: `playtests/runs/P5/custodian_debrief.md` (self-report, not an independent audit).
- The command recorder covers harness calls, not a complete agent-tool/access trace. Player tool-use compliance and absence of private-context access are not independently established by this bundle. The external audit must distinguish public-text observations from those limits.
