# P6 cross-team audit: Candlelight Dungeons, *The Bell Beneath Saltmere*

Auditor: Fable (`claude-opus-5-5`), for the Claude team. Protocol revision 3; rules at `515f598`. I did not run commands against the campaign.

**Evidence** (in the ignored `playtests/runs/P6/`):
- the committed transcript and the `gm_NNN.md` reply files;
- `checkpoint_checks.jsonl` and `checkpoint_versions/`;
- `commands.jsonl`;
- the frozen scenario, the policies and the spellbook;
- the initial, suspended and final snapshots (the log is `final/p6_candlelight/state/logs/session_001.jsonl`, 12 events);
- the Custodian's notes.

**References.** "Event N" is the log's `sequence`; G, B, I, M and P numbers are message IDs.

**Scope.** P6 has fewer than ten consequential rulings, so all are audited:
- the one roll and its settlement;
- the recovery;
- the zero-Fatigue outcome;
- the six beat boundaries and two act boundaries;
- the no-roll resolutions;
- the recap threads.

## Verdicts

**No crisis occurred.** Fatigue stayed at 0 throughout. There is no crisis, purge or table draw to grade.

**Correct: Pip's lock test (G007–G009, events 4–6).**
- **Stakes and commitment.** G007 stated the stakes publicly and invited a change of approach. Pip committed in P007, and only then was the roll made (`p6-check-001`, `--stakes`, seed 61003001). This is the full stakes → commitment → deferred roll → choice → settlement sequence the protocol asks for.
- **Advantage.** The lockpick satchel's Advantage applies to "DEX tests to open locks … when you have access" (`skins/candlelight_dungeons.md:142`). Pathfinder was correctly excluded.
- **The roll.** Dice 17 and 18 kept 17 against DEX 16, a failure by 1. Neither die was a natural 20, so the picks were safe.
- **The Fortune offer.** One coin turns the roll (17 to 16, margin 0). The Custodian also checked Jack-of-Trades, which acts after the roll and before Fortune (`skins/candlelight_dungeons.md:130`). It correctly found that no other score of Pip's exceeds 16, so swapping the stat could not help.
- **Settlement.** `settle --nudge -1` gives Fortune 10 → 9, with no reroll.

**Correct: the hearth recovery (G012, event 9).** A short rest restores 1 coin "only at a warm hearth" (`skins/candlelight_dungeons.md:41`). The village hall's warm hearth qualifies, and Pip returns to 10/10.

**Correct: zero Fatigue.** The scenario and policies tie Fatigue to specific triggers (`policies.md`; `frozen_hidden_scenario.md`, "Pressure and adjudication"):
- threatened time under the unstable ceiling;
- a long forced retreat;
- a loud bell;
- real wounds.

None occurred. The party took the dry route, bargained with Nib, never rang the bell, never stood under the ceiling, and was never hurt. Careful talk and mapping are explicitly excluded from Fatigue, and the Almanac never makes Pressure mandatory without a trigger. Zero is the right result for this play.

**Correct: the no-roll resolutions.** None of these carried meaningful uncertainty once the players chose their method:
- Nib's bargain (G003–G004), taken on stated terms;
- the oak door, opened as Nib described (G005);
- the papers, the mark and the crawl, all examined by observation (G006);
- the return trips along a marked, clear route (G011, G015);
- Edrin's peaceful exchange (G012–G014).

The scenario says competent preparation can remove a roll.

**Judgement call: beat 3 marked perilous (event 7).** Failure at the niche would have left it shut and needing "a different method or the keeper key" (G007). That is a setback toward the goal, not a loss of it. Almanac 9's definition is "could cost Stamina, a life or the goal" (`rules/core/custodians_almanac.md:190`). The Custodian's note says failure "could deny the register", which overstates the stated stakes. The flag is defensible but generous.

**Judgement call: beat 6 marked perilous (event 11).** The salt-eaten ceiling over the bell was a real, visible hazard to life (G012). The party chose positions that kept them out from under it. The revision 3 handbook, as amended by Astra, lets "a genuine hazard resolved through preparation" qualify, so the flag is defensible. No milestone depended on it, since only two perilous beats were recorded.

**Wrong, without consequence: beat 6's scope.**
- A beat "ends when the question is answered … or when the story cuts to another place or time" (`rules/core/custodians_almanac.md:190`).
- Beat 6 runs from the descent (G012) through the crypt exchange (G013–G014), then cuts back to the village and the entering of the names (G015).
- Edrin's names answer the crypt scene's question. The village entry is a new place, so it belongs to its own beat.
- Beat 5 ("village hearth and inquiry") is thin by the same test: it holds the rest and two questions to the reeve, then the descent opens beat 6.
- The counts change only slightly: 7 beats instead of 6, and Act 2 has 3 beats instead of 2. No milestone or summary threshold changes.

**Not a rule question: Act 2 has two beats.** Almanac 9's four to six beats per act are illustrations ("never steer a scene to hit them"). The party reached its own objective, and closing there was right. The six-beat session is short; that is a description, not a violation.

**Procedure note, not a rules error: distinctive capabilities.** The revision 3 handbook asks the Custodian to name a character's distinctive capability when the fiction suits it. Three moments fit:
- **At G006–G007, the locked niche.** The frozen scenario names "stone magic" as one way to open it, and Iona's Stone Passage fits. The option lists named the lock, the keeper's key and the crawl, but not the spell.
- **At G012, the dead sexton.** Ward the Threshold and Turn Undead were plausible precautions, though Edrin was not hostile.

No spell, knack or Fortune test was used in the session, so P6 gives no evidence on spell costs or backlash. This is a coverage gap, not a ruling error.

**Harness gap (memory hygiene): recap threads.**
- `state/memory/session_001.yaml` keeps superseded open threads beside the later lines that resolve them: the bell promise, the register payment and the unnamed dead.
- `recap.py --thread` only appends, and has no way to close or replace a thread.
- A cold resume could read the resolved threads as still open.
- This belongs in the Stage 4 backlog. The Custodian handled it reasonably within the tool's limits.

## Record and access checks

- **Checkpoints.** The recorder reports all 15 comparisons as true, and `checkpoint_versions/` holds each version. I compared only the last directly: `gm_015.md` is byte-identical to the final `last.md`.
- **Log.** The 12 log events are consecutive and end in `session_end`. The single draw used seed 61003001.
- **Packets.** The four packet hashes match their reader receipts. The packets include the Pressure steps and triggers and the agreed spellbook, and exclude the crisis table and the Custodian section, consistent with revision 3.
- **Access.** Instructed, not enforced. P6 has no agent tool trace, so player isolation is not assessable. No premature use of hidden information was observed. Edrin's unfinished duty was revealed lawfully in play (G013–G014), and lawful discovery is not a leak. The skipped sluice trap and the collapse mechanics stayed undisclosed.
- **Setup errors.** Two of the three failed setup calls were unquoted-colon metadata values. That is the same `update_sheet` parsing gap P2 hit with notes.
- **Interventions.** The formatting-only correction at G006 (a control character) and the diagnostic interrupts during the platform failure are disclosed. They involve no ruling, die or state.

## Summary for the programme

P6's mechanics are clean:
- one roll, correctly staged, settled and recovered;
- zero Fatigue, correctly, because nothing triggered it;
- checkpoints that all match.

The findings concern scene recording and coverage:
- beat 6 spans a change of place;
- one perilous flag is generous;
- the signature magic was never surfaced as an option;
- recap threads cannot be closed.

The session was coherent and humane, and nearly free of dice: one roll in six beats, against Almanac 9's sketch of about six beats in ten having a roll. With four careful players, the risk-averse table that P1, P5 and P2 suggested is clearer still. The joint review takes this up. Like the Pressure question, it concerns how the AI table plays, not a rules defect.
