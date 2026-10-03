# Pilot review 1: P1 and P5

Fable, with Astra's review and amendments, 3 October 2026. This review sets the two cross-audits side by side (P1 audited by Astra, P5 by Fable) and records the agreed changes before the second round, P2 and P6, under Barry's instruction to review and approve the updates. Under the protocol, no rule changes follow from the pilot alone; the changes below concern the protocol, the briefs, the AI guidance or setup. Judgement calls remain identified rather than becoming rules through agreement.

## The two runs

| | P1 Clanfire | P5 Rust & Domes |
|---|---|---|
| Table | Sonnet ×3, Fable orchestrating | Sol ×3, Astra orchestrating |
| Scenes | 10 logged (9 counting the fight once); acts 5 + 5 | 7; acts 4 + 3 |
| Perilous | 7 logged (6 corrected) | 4 (3 if beat 6 is not perilous) |
| PC rolls | 14 | 2 |
| Pressure | Shadow 0→1, from one parley | Heat 0→1, from one chosen cost |
| Crises, Luck tests, purges | none | none |
| Luck spent | 8 | 0 |
| Milestones | 1, late | 1, on time |
| Signature procedures | Totem Mark once; no Beast Bond, vision shard or Luck test | technician Advantage; psi never offered |
| Orchestrator interventions | multiple; 3 classified as beyond format in the manifest | none |
| Public play time | about 23 min | about 37 min |

Both sessions closed through the harness. Neither audit found a dice-arithmetic or resulting mechanical-state error. P1 had early deferred-choice procedure deviations and later orchestrator reminders. Neither public transcript showed a hidden-scenario leak; this does not prove isolation or absence of private access. P1's subsequently supplied tool trace supports one packet read per player, while P5 has no comparable player-tool trace. P1 also disclosed Pressure step effects omitted from its packet, a boundary judgement that revision 3 resolves prospectively.

## What the audits found

The audits distinguish clear errors from judgement calls:

- **P1:** the wolf fight was split across two beats, against "a fight is one beat", and the milestone came at the close instead of when the third or fourth perilous scene ended.
- **P5:** the promised salvage reward was dropped from the open threads. Fable would not count beat 6 as perilous; Astra considers a genuine checkpoint threat resolved by spending an earned boon potentially eligible. The Almanac does not require dice or a new risky choice. Whether this particular scene exposed the goal to real danger remains a judgement call, and the historical count stays intact.

All other rulings were correct or defensible judgement calls.

## Shared patterns

These two sessions are procedure evidence, not balance evidence. The following observations suggest guidance and recording improvements; not every issue appeared throughout both runs, and their causes are not all established.

1. **Pressure hardly moved.** Each session gained one point. Almanac 9 sketches Pressure rising in about one beat in three, and a crisis every session or two, but these are not quotas. Both stories had weather approaching; neither recorded a Pressure charge for "time passing under threat" (Almanac 4). That is a reason to check actual fictional exposure and the shared-hazard policy, not proof that every elapsed scene required a charge. P1 charged Shadow for parley, used threat clocks, and offered failure costs that successful nudges avoided; P5 paid a shared alarm cost and left before the dust front. The trials exercised a small Pressure change but not its escalating steps, purges or crises. Custodian choices, player choices and the dice may all contribute.
2. **Signature coverage was incomplete.** P1 used Totem Mark, while Beast Bond and vision-shard procedures were not exercised; their availability must follow the character's actual fictional resources. P5 had a sensitive but no psi activation, and its frozen sensor clue never appeared publicly. Naming a capability when it is available and relevant may improve visibility without forcing its use. Packet omissions or unequal delivery can also affect what players propose.
3. **Public dialogue delivery was incomplete.** P1 players received Custodian summaries of one another's actions. P5 did this through G003, then relayed completed player dialogue from G004 onward. In its opening, both players claimed the crawlway twice before the Custodian divided the work. Missing dialogue plausibly contributed to that friction, but similarity persisted after delivery improved. Relay complete dialogue consistently and test whether distinct character drives help; do not treat either as a demonstrated cure.
4. **Beat and milestone recording slipped.** There was a split fight, a late milestone and a generous perilous flag. The rules are clear (Almanac 5 and 9), but the Custodians did not apply them under load.
5. **Some round trips added no meaningful choice.** P5 twice offered Luck that could not change the declared outcome. P1's early replies settled deferred draws before a player decision, followed by two orchestrator reminders. A prospective no-choice shortcut should still use a deferred draw, explain the dice and preserve all meaningful post-roll abilities and payment decisions.
6. **The source packets set different boundaries.** P5's preserved source packets included the skin's Pressure track, with steps and triggers; P1's excluded that section. P5's actual transcribed delivery is not captured by those files. State the public boundary prospectively and distinguish a packet-boundary disclosure from a hidden-scenario leak.

## Proposed changes before P2 and P6

**A. AI guidance (`skills/agent_dm_handbook.md`).** Each item restates or applies an existing rule; none adds one:
- Apply Pressure for actual fictional triggers, including time under an active threat (Almanac 4), using the skin and declared shared-hazard policy. Neither real-world deliberation nor a desired rate is a trigger.
- When the fiction suits a character's distinctive capability, name it among the options; never require it.
- Offer meaningful legal Luck choices. Auto-settle without discretionary spending only when no eligible player has any meaningful post-roll decision, including abilities and payment alternatives. Candlelight's Jack-of-Trades and Spell payment choice are reasons to check beyond the nudge arithmetic.
- A fight is one beat, however many rounds it runs.
- Award a milestone when the third or fourth perilous beat ends.
- Assess peril by actual fictional stakes: failure could cost Stamina, a life or the goal. A boon or preparation can resolve genuine danger without dice; safe chores, rests and danger staged for milestone credit do not qualify.
- Record promises made in the fiction (rewards, debts, favours) as recap threads until they are settled.

Because the handbook is what any AI Custodian reads, the improvement reaches real play, not only the pilot.

**B. Custodian brief (protocol).**
- Add the public-text block format, with routing outside it and the checkpoint containing exactly the public body.
- Add "the orchestrator relays and keeps records; it gives no rulings".
- Point to the handbook's table discipline.

**C. Player brief and packet (protocol).**
- Add "speak to the other characters as well as the Custodian".
- Add a one-line *drive* for each character, fixed at setup and recorded, so that players differ in what they want.
- Every packet includes the skin's Pressure track, with its steps and triggers, but never the crisis tables or Custodian advice.
- Deliver the packet verbatim, either as text or as one read of the file, and record its hash.

**D. Turn loop (protocol).** Once all addressed players have answered, relay their completed answers and the Custodian's public replies to every player. Queuing for an idle player is allowed, but deliver the complete chronological public dialogue before their next decision. Pending answers stay private until all addressed players have answered.

**E. Records (protocol).** Adopt P5's method for both teams:
- save each Custodian reply as its own file;
- compare it with the checkpoint before forwarding;
- keep a command record.

Where available, keep a tool trace and token usage per role, stating what each export actually contains. P1's recovered trace supports invocation counts, but has no tool results, usage counters or saved intermediate checkpoints; its usage figures remain attributed to Fable's separate extraction. Sol's live collaboration tools expose neither per-role usage nor a full tool-trace export, so these fields remain unavailable unless another supported source is established.

**F. Setup.** Give newly created Emberfall pregens their handout inventory in `examples/command_snippets.md`. For P2, reconstruct what the characters actually retained at P1's close from its fiction and receipts; do not restore consumed or traded starting gear merely because the historical sheets were empty. Record the migration before opening session 2 and preserve P1's frozen snapshot.

## Not proposed

- **No rule changes.** Nothing seen so far bears on balance.
- **No changes to Pressure's cadence.** The low observed Pressure does not establish a causal explanation or a balance defect. Apply the existing triggers consistently and gather more evidence before changing numbers.
- **No probes.** A forced psi or crisis test would be a separate, labelled probe, not part of a pilot run.

## Second round

- **P2:** a fresh Custodian resumes P1's campaign under the revised protocol.
- **P6:** Candlelight with four players under the revised protocol.

P2 also tests whether a cold resume preserves the open threads, such as the Ysre and the wounded wolf. P6 tests the relay change at a larger table, where coordination matters most.
