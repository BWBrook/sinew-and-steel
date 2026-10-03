# Pilot review 2: P2 and P6

Fable, 3 October 2026. This review sets out the second round's cross-audits:
- P2, audited by Astra (`P2/audit.md`, with the qualification at board 865);
- P6, audited by Fable (`P6/audit.md`).

It reads them against round 1 (`review-1.md`) and proposes changes before round 3 (P3 and P7). These changes need Astra's view and Barry's approval. No rule changes follow from the pilot alone.

## The four runs so far

| | P1 Clanfire | P5 Rust | P2 Clanfire (resume) | P6 Candlelight |
|---|---|---|---|---|
| Protocol | rev 2 | rev 2 | rev 3 | rev 3 |
| Party | 2 | 2 | 2 | 4 |
| Beats (acts) | 10 logged (5+5); 9 by audit (4+5)* | 7 (4+3) | 10 (6+4) | 6 logged (4+2); 7 by audit** |
| Perilous | 7 logged; 6 by audit* | 4 | 5 logged; 6 by audit | 2 |
| PC rolls | 14 | 2 | 24 | 1 |
| Rolls per logged beat | 1.4 | 0.3 | 2.4 | 0.2 |
| Pressure gained | 1 | 1 | 0 | 0 |
| Crises | 0 | 0 | 0 | 0 |
| Fights | 1 | 0 | 2 wolf fights and the rhino-calf combat exchange | 0 |
| Spells, psi or bonds used | Totem once | none | flute ×4, vision shard | none |
| Orchestrator reminders | 3 | 0 | 0 | 0 |
| Checkpoints matched | last only | 15/15 | 23/23 | 15/15 |

\* The audit counts the wolf fight as one beat. The logs and summaries are unchanged.
\*\* The audit splits beat 6 at the change of place.

## What held or improved in these runs

- **Procedure.** Neither run needed a ruling or pacing reminder. Both handled the public blocks and deferred settlement. P2 applied the no-choice shortcut with its reasons; P6, with a single roll, never needed it.
- **Records.**
  - The recorded checkpoint comparisons all matched.
  - P2's fights were one beat each.
  - P2's milestone fell in the printed window.
  - P2's recorded tool inputs support the one-read claim for players, but not OS isolation. P6 has packet receipts, not a tool trace.
- **Players.** Drives accompanied clear character choices, most clearly Grak feeding the she-wolf he had sworn to kill, and players addressed each other. Four varied sessions cannot show that the drives caused those choices, or that they cured the coordination problem.
- **Resume.** This is the concrete continuity evidence. A fresh Custodian resumed from the campaign's files alone, including a boon that existed only in sheet notes (P2).

## What it did not fix

**1. The AI table avoids risk, and Pressure does not move.** Pressure gained across four sessions was 1, 1, 0 and 0, with no crisis. Almanac 9 sketches Pressure rising in about one beat in three and a crisis every session or two. The audits established no mandatory Pressure omission: zero is correct when nothing triggers Pressure. Other rulings did go wrong: P2's pre-roll stakes and a perilous flag, and P6's beat boundary. These are plausible contributors to the low Pressure, not established causes:
- **Players choose the safe line**, and the Custodian-written scenarios offer one. Examples:
  - the dry route and bargaining (P6);
  - declining a Beast Bond (P2);
  - leaving with the evidence (P5);
  - spending Luck to avoid a failed-rite Pressure point (P1 ×2, P2).
- **The scenarios were passive.** The Custodians wrote hazards that are signposted, avoidable and waiting to be engaged. "Never forces a procedure" does not require passive opposition: a signposted threat can still advance. P2's Pack Learns clock sat at 3/4 for half the session, and P6's ceiling only threatens anyone who stands under it.
- **Custodians charge Pressure only when it is offered as a price or comes from a failure.** None charged for time under threat, although the Almanac lists it. The revision 3 handbook line did not change this.

Rolls per beat varied 0.2–2.4 across sessions, depending mostly on whether a fight happened.

**2. Stakes stated in the same reply as the roll.** The P2 audit found five such checks wrong (G002 twice, G003 once, G016 twice). P6 shows the correct pattern (G007): state the stakes, wait for commitment, then roll. P1 and P5 had milder versions.

**3. Scene boundaries.** P6's beat 6 spans a cut from the crypt to the village. P2's beat-7 flag was wrong on the declared stakes.

**4. Distinctive capabilities.** The P2 Custodian named them readily. The P6 Custodian never named a spell, though the scenario's own text says one opens the niche. Across Sonnet and Sol the handbook line works unevenly.

**5. Simultaneous declarations still clash.** There were three clashes in P2 and two in P6. The P2 Custodian resolved each one inside the same reply, which costs no extra turn.

## Proposals before round 3

**A. Custodian brief, protocol revision 4.** These are the proposals as first made. The wording actually adopted is in the protocol, amended after Astra's review (board 869), and is summarised at the end of this review.
- "Threats and clocks move on their own. When time passes under an active threat, tick its clock or charge Pressure (Almanac 4), whether or not anyone rolls. Signposting a danger does not make it wait forever."
- "Put the stakes in your option list, or state them and ask for commitment before rolling. Never introduce stakes in the same reply as their roll."
- "A cut to another place or time starts a new beat."
- "When declarations conflict, resolve each by the player's own declared action and say so, in the same reply."

**B. Scenario rule for Custodian-written scenarios (P3, P4, P7, P8).**
- Each scenario has at least one active threat with a clock that advances with time or the opposition's own moves, not only on player failure.
- It also names the skin's Pressure triggers that the threat can set off.
- This gives Pressure and crises a chance to occur. It is not a guaranteed outcome, and dice are never picked to produce one.

**C. Handbook.** This is superseded by Barry's decision below. The handbook now carries the same guidance as the revision 4 brief, for real play.

**D. Programme metrics.** Per session, each report gives:
- **Pressure gained,** which `playtest_summary.py` reports directly.
- **Rolls per recorded beat,** derived from its counts.
- **Luck spent to avoid Pressure.** The summary cannot classify nudges by motive, so this is derived in a short audited table with event and message references. It separates nudges that prevented a declared failure cost in Pressure from Luck paid as an optional price, and marks the uncertain cases.

They are the measures that decide whether proposal A is enough.

**E. For Barry, after round 3 (not now).** Suppose P3, P4, P7 and P8 still show near-zero Pressure under A and B. Then the question becomes design, not Custodian craft: should the skins' trigger lists include an automatic, time-based source of Pressure? That is a rules decision for Barry and for the programme, and it fits the reopen triggers in `PLAN.md`. Reopening needs evidence that the triggers actually arose and how they were applied; a low total alone is not enough.

## Backlog (not for this round)

- **Harness, Stage 4:**
  - add a combatant mid-fight;
  - an NPC defeat or remove command;
  - `update_sheet` values containing ": " (seen in P2 and P6);
  - relative `--campaign` paths that resolve under `campaigns/`;
  - the act counter shown after the close;
  - weapon edge on sheets;
  - closing or replacing recap threads, since the append-only threads could mislead a cold resume (P6).
- **Not a gap:** a negative `--nudge` parses fine; P2's report has been corrected.
- **Rules text, Stage 3 tally:** how a Clanfire Beast Bond is gained.

## The second tranche (Barry, 3 October 2026)

After P1–P8, Barry proposed a further tranche, "so we remember":

| Run | Team | Content |
|---|---|---|
| P9 | Fable | Briar Benedictine; it needs a mystery |
| P10 | Fable | Service Duct Blues |
| P11 | Fable | the base game with no skin, any story or theme |
| P12 | Astra | Time Odyssey |
| P13 | Astra | Candlelight with the Delvekit sidecar |

After that come targeted probes, such as simulated full-party combat encounters.

With P1–P8, this covers every skin file and the base game.

Two optional core modules would still be unexercised: Condition Tracks and Wealth & Attention (Almanac 7). P11, the base game, is the natural place for one or both. Gritty Injury can ride on P4 (Twilight, with Injury on).

## Barry's decision (3 October 2026)

Barry agreed proposals A–E, in his words: "Let's induce some more risk, tension, pace and Pressure." He added:

- **Cold opens.** Sessions should "jump right into something interesting, rather than having it build from a rather passive base", framed like a James Bond pre-credit scene or a Star Trek teaser. He judged that the better setup for testing, though a real campaign more often builds up gradually.
- **Pressure is likely fine.** "A human custodian would use it appropriately. We just need to be more directed in our advice and setup for the AI Custodians."
- **Characters with defined personalities.** Each NPC or retainer should have "a defined personality/trait suite that stops them all being rather beige". The same applies to AI players who may one day join a human table.
- **A fallback for later.** If advice and setup still fail, consider "a scripted mechanic that forces reminders", or background clocks that tick for the Custodian. He offered this as brainstorming, not a decision.

Protocol revision 4 and the handbook carry these changes:
- open in motion;
- threats and clocks move on their own;
- stakes before commitment;
- a cut starts a new beat;
- conflicting declarations resolved in the same reply;
- NPC wants, manners and lines;
- player temperaments with a risk appetite, at least one bold per party;
- scenarios with an active threat clock and named Pressure triggers;
- the Pressure metrics in each report.

**Amended after Astra's review (board 869–870):**
- **Clocks.** Each scenario declares in advance what fictional interval, action or opposition move advances its clock, what happens when the clock fills, and what can interrupt it. A clock tick is not automatically a Pressure charge, though both may apply when their triggers occur.
- **Stakes.** When the stakes are already public, the declared action counts as commitment. The stakes must never first appear in the reply that shows the dice.
- **Conflicting declarations.**
  - Preserve each player's intent, and adjudicate compatible actions in fictional or initiative order.
  - Ask only for the decision needed to settle a truly incompatible pair.
  - Never override one declaration to make another succeed.
- **Temperaments.** Temperaments differ only in multi-character runs; a solo character still gets an explicit one. Boldness is concrete: the risk the character will take, and the line they keep.
- **Cold opens.** Each opening carries an immediate, consequential situation, but honours rests and decisions already agreed. An act need not open with a forced fight.
