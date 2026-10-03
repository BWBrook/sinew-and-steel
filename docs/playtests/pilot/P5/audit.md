# P5 cross-team audit: Rust & Domes, *The breath ledger*

Auditor: Fable (`claude-opus-5-5`), for the Claude team, under pilot protocol revision 2. Audited against the rules at `b89ad90`. I did not run commands against the campaign.

**Evidence.** Everything is in the ignored `playtests/runs/P5/`:
- the committed transcript;
- `messages.jsonl` and the `gm_NNN.md` reply files;
- `commands.jsonl` (83 recorded calls);
- the frozen scenario and policies;
- the initial and final snapshots, including `final/p5_rust/state/logs/session_001.jsonl` (20 events);
- `checkpoint_checks.jsonl`;
- the Custodian's debrief.

**References.** "Event N" is the log's `sequence`. G, R and J numbers are message IDs.

**Scope.** P5 has fewer than ten consequential rulings, so all of them are audited:
- two tests;
- one Heat charge;
- the milestone and both boons;
- the seven beat and two act boundaries;
- the no-roll decisions that carried stakes.

## Verdicts

**No crisis occurred.** Heat went from 0 to 1 at event 7 and ended at 1. There is no crisis, purge, step effect or table draw to grade (`skins/rust_and_domes.md:101-118`).

**Correct: Jori's bypass repair (G005–G007, events 3–4).**
- The stakes were stated before the roll, and the alternative approach was left open.
- The roll was made with `--defer` (seed 51003001) and settled without a reroll.
- Life-support technician gives Advantage, a square fit for freeing a scrubber valve (`rules/core/adventurers_manual.md:143-150`).
- Dice 3 and 2, keeping 2 against Skill 10, give margin 8: a success.
- G006's offer of a 1-chit nudge that "would not change the declared repair outcome" is legal but pointless. It cost a round trip and no rule.
- The scenario allowed competent preparation to remove the roll. Rolling a risky repair under a live CO₂ load is a defensible **judgement call**.

**Correct: the tamper-alarm Heat (G009–G010, event 7).**
- G009 offered a choice between a Skill race against the purge and a certain +1 Heat for pulling the lead, and stated the cost before either.
- This is the Almanac's "Pressure as a lever" pattern exactly (`rules/core/custodians_almanac.md:41,75,85,95-97`). The skin's list of Heat triggers does not need to name it.
- Both players chose it, and the Custodian charged it once to the party track. That is correct for a single shared alarm (`rules/core/custodians_almanac.md:60,82`) and matches the declared shared-hazard policy.

**Correct, with judgement on the modifier: Rhea's opposed Mind test against Saye (G011–G013, events 9–12).**
- Saye was created with MND 12 (`p5-npc-saye-001`) after the stakes were offered and before the roll, by a recorded command. His score was not stated publicly, which is normal NPC practice.
- An opposed test is correct where the target actively resists (`rules/core/adventurers_manual.md:215-217`).
- Advantage from the signed ledger and a witness is a **judgement call**; it is a square fit for pressing a liar.
- Rhea kept 11 against 10 (a failure by 1). Saye rolled a natural 1, which is locked, with margin 11. When only the defender succeeds, the defender wins.
- The Luck analysis in G012 is right:
  - A nudge to 1 would not be natural (`rules/core/adventurers_manual.md:167`).
  - Even ten chits give margin 9, below 11.
  - So no spend could change the winner (`rules/core/adventurers_manual.md:42-50,164-171`).
- The loss applied exactly the stated consequence: corporate legal froze the bin, and the copies stayed safe.

**Correct: milestone timing and contents (G013, events 14–17).**
- Beats 2, 4 and 5 were marked perilous, so the award at the third falls inside "every 3–4 perilous beats" (`rules/core/custodians_almanac.md:121-131`).
- Beats 4 and 5 had no physical danger, but the Almanac defines a perilous beat as one where "failure could cost Stamina, a life or the goal" (`rules/core/custodians_almanac.md:190`). Losing the archive or the buyer's trail is the goal, so both qualify.
- Each character received 2 build points, a boon (an ally favour, a listed boon type) and a full pool. Both pools were already full.
- Jori's escort favour was spent in G014 and noted on his sheet (`update_sheet.py --append notes=…`). Its spent status lives in notes and the recap; the advancement entry still shows the award. That is acceptable with the current tools.

**Judgement call: beat 6 marked perilous (G013–G014, event 18).**
- The departure carried a real threat to the goal: an officer flagged the alarm and could have taken the datapad.
- The Custodian resolved it without a roll, through Arda's boon.
- "Could cost the goal" covers it in principle. But nothing was put at risk on a die or a choice, and the Almanac excludes "danger staged on purpose" from milestone credit (`rules/core/custodians_almanac.md:36`).
- It earned nothing here, since the milestone came earlier, but in a longer session it would bring the next award forward. I'd score it not perilous.

**Correct: beat and act boundaries (events 2, 5, 6, 8, 13, 18, 19).**
- Each recorded beat is one scene with one question:
  - preparation and arrival;
  - the airflow;
  - testimony and Arda's arrival;
  - the purge;
  - the confrontation;
  - departure;
  - the evidence handoff.
- Act 1 ends at a turn (beat 4, the archive secured and Saye arriving), and act 2 at a pause (beat 7).
- **Note on beat 1.** It covers G001–G004, including the two-reply argument over the crawlway, and it was recorded before Jori's roll. G002 is a cut from the berth to the dome, which would ordinarily end a beat. Folding the departure into a single beat 1 is a defensible **judgement call**, given how little happened in the berth.
- **Act 2 had three beats.** That is below the Almanac's four to six, which are illustrations, not quotas (`rules/core/custodians_almanac.md:186-201`). Closing at the players' chosen exit was better than padding.

**Correct: no-roll rulings with stakes.**
- **G002:** the clerk's call and the cached data. It was safe and certain, so it needed no roll.
- **G007–G008:** Arda yields to live meter evidence. The scenario says concrete evidence persuades him.
- **G014:** the checkpoint was resolved by the boon the players had earned.
- **G015:** the handoff.
- None of these created or removed a cost.

**Judgement call (continuity): the salvage claim.**
- G001 offers a salvage claim if the party confirms the workers are alive and gets the air moving. Both conditions were met by G007.
- Saye's bribe in G010 and G011 repeats the claim, but neither the close nor the recap's threads mention it.
- Leaving it open is legitimate; the scenario says "leave unresolved consequences as threads". However, the reward the hook promised should have been recorded as an open thread. Without it, a continuation will lose it.

**Not exercised: psionics.**
- Rhea's bought *M-field sensitive* tag unlocks the four powers (`skins/rust_and_domes.md:73-95`).
- The frozen scenario names applications at the valve, the camera and Saye. The source packet lists the powers (`packet_rhea_voss.md:622-644`).
- In play, the Custodian never offered an activation, and Rhea never attempted one. The debrief confirms the Custodian chose not to name them.
- It cannot be determined whether Rhea's actual compact inline packet included the power list. The manifest says the delivered packet was a compact transcription, not the preserved file. Rhea's choice not to use psi may therefore reflect what she was given, not what she decided.
- This is a coverage gap, not a rules error. P5 provides no psi evidence.

## Record and access checks

**Checkpoints.**
- `checkpoint_checks.jsonl` reports 15 of 15 matches, each made before the next reply was forwarded.
- I verified the last directly: `gm_015.md` is byte-identical to `final/p5_rust/state/checkpoints/last.md`.
- The earlier 14 rest on the recorder's comparisons; their checkpoint versions were overwritten. This is stronger evidence than P1 has.

**Log and commands.**
- The 20 log events are consecutive and end in `session_end`.
- The two gameplay draws used seeds 51003001 and 51003002 in order, both deferred and then settled.
- `commands.jsonl` shows the Heat, NPC, award and beat commands in the same order as the transcript.

**Leaks.**
- No hidden-scenario material appears in the public text:
  - the M-field sensor's echo of Keel's thoughts;
  - Saye's private priorities;
  - the scrutiny thresholds;
  - Arda's being misled, until he says so himself in the fiction.
- G014's "a reckless leak would add 1 Heat" restates a trigger printed in the player packet (`packet_*.md:665`), because Astra's packets include the skin's Heat track.
  - P1's packets excluded the equivalent Clanfire section.
  - Harmonise this prospectively. See the joint review.

**Player access.**
- Access was instructed, not enforced.
- The bundle has no player tool trace, so isolation is **not assessable**.
- The public text shows no use of hidden information. That supports only a no-observed-leak claim.

**Delivery deviations.**
- Packets were delivered as unequal compact or full transcriptions, not verbatim. This limits comparability between the two players.
- Before G004, each player received the Custodian's reply but not the other player's words. That is consistent with the protocol's text. It caused the G002–G004 coordination loop, in which both players claimed the crawlway twice. The stall threshold was not reached, because G004 resolved it.

## Summary for the programme

P5's mechanics are clean:
- both tests are correct;
- the Heat charge is correct;
- the milestone is correct, at the third perilous beat;
- all checkpoints match.

The material findings are about procedure and coverage:
- the Custodian never surfaced the party's distinctive capability (psi);
- the promised salvage reward was dropped from the record;
- beat 6's perilous flag was generous;
- the coordination loop came from players not hearing each other.

Pressure stayed at 1, and the session had two rolls in seven beats. That is low against Almanac 9's sketch, as in P1, and is taken up in the joint review rather than here.
