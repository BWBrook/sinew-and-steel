# P1 report (orchestrator)

Clanfire, *Emberfall*, Grak and Tarra. The session finished in 10 beats over two acts, with no stalls, no harness failures that blocked play, and no leaks of hidden material. These are the orchestrator's notes. Astra's audit decides rules questions.

## What happened

The pair met a lone wolf on the calf run and fought it off in a short fight (beats 1–3). They rested and bound Grak's leg, and Tarra read an omen at dawn. Act 1 ended when Grak and Hesk were seen by strangers on the ridge (beat 5).

In Act 2 they parleyed with the Ysre, a starving southern band. The Custodian added that the calf the clan had taken was the Ysre's kill. The pair paid the debt openly, won the elders over to shelter the band, and broke a sick child's fever. Through a blizzard, Tarra's long-burning rite held the pack off until dawn (beat 10). There was one milestone and the session closed.

## Stalls and invented rules

- **No stalls.** The stall prompt was never used.
- **No invented rules.** The Custodian's additions were fictional:
  - the calf as Ketha's kill;
  - the Ysre's backstory;
  - the boons, chosen and not drawn.
- **Judgement calls the Custodian flagged itself,** each for the audit:
  - Grak's tracker tag was denied twice (a wolf; human tracks);
  - Advantage and Disadvantage cancelled twice;
  - Advantage came from the ochre pouch, the cloth scrap and the flute;
  - Spirit, not Cunning, for a gestured parley;
  - one Shadow for the whole Ysre contact;
  - Hunger +1 for the debt-gift;
  - Pack Learns ticked twice without a roll;
  - combat order set by the stated stakes instead of initiative.
- **For the audit:**
  - **Milestone pace.** The Quickstart says to award a milestone every 3–4 perilous beats. Seven of the ten beats were perilous, but the only milestone came at the session's end.
  - **The rest.** Grak recovered 2 Stamina and 1 bead.

## Harness gaps and errors

- **One malformed command:** `--actor` was placed before the subcommand. It drew no dice, and the Custodian retried it with the same seed and event ID, as the protocol requires.
- **One pending roll at a time.** Two players acting at once had to be settled one after the other. This was workable, but it made the Custodian hold back one player's action to narrate later.
- **Empty inventories.** The pregenerated sheets carry no inventory. Grak's and Tarra's gear existed only in the handout and the prompt. A resume from the sheets alone would lose it, which matters for P2.
- **The Custodian's own margin error** in a Luck offer was caught before sending. The harness computes margins, so the error was in the prose, not the state.

## Brief compliance (protocol, not rules)

- **Turn 1.** The first Custodian reply narrated without deferring rolls or offering Luck. Two orchestrator notes, interventions 1 and 2 in the manifest, restated the brief's defer-show-settle instruction, and the Custodian followed it from then on.
  - These notes are procedure, not rule corrections.
  - They still mean P1 does not show the brief working unaided.
  - **For the programme:** put the PUBLIC block format and a worked defer-and-settle example in the Custodian brief itself.
- **Reply length.** Replies ran 209–405 words, mostly 300–400, against a 300-word guide. The overrun came from replies that carried a settlement, a clock tick and new narration together.
- **A ruling request.** The Custodian once asked the orchestrator to rule on rolling versus narrating. **For the brief:** add that the orchestrator gives no rulings.
- **Player replies.**
  - Within two to five sentences.
  - Consistently cooperative.
  - Formulaic, almost every one ending "I'd roll X, keep my beads and decide after the dice".
  - Players mixed first and third person.
- **Continuity.** One continuity slip by a player (Hesk's location) got an orchestrator note (intervention 7). The Custodian then made Hesk present in the cave scenes.

## Pacing against Almanac 9

This is a description, not a target.

| Measure | P1 |
|---|---|
| Beats | 10 (Act 1: 5, Act 2: 5) |
| Perilous beats | 7 as logged (4 + 3); 6 counting the fight once |
| PC rolls | 14 (9 + 5), at most 3 in a beat |
| Fights | 1, one round (logged across beats 2 and 3; see the post-audit note) |
| Rests | 1 |
| Milestones | 1, at the close |
| Shadow | peaked at 1; 1 gained; no crisis |
| Luck | Grak spent 2 and Tarra 6; both were full again at the close |

The act structure worked as written: the act break fell at a natural turn (strangers sighted), and the session close at a natural pause (dawn after the storm).

**Pressure barely moved.** Shadow peaked at 1, against Almanac 9's "a crisis every session or two". Two causes are visible:

- **Shadow came only from failed rites and a parley.** Tarra turned both failed rites into successes with Luck. Rite failure was Shadow's only ongoing source in this scenario.
- **The refill at the close made Luck free.** Tarra spent 5 of her 11 beads in the last two beats, knowing a milestone would refill them, and both spends were made to avoid +1 Shadow.

This is one session and not balance evidence. It is a dynamic for the programme to watch: Luck spent late, just before a refill, suppresses Pressure.

**The spotlight was uneven.** Tarra made 9 of the 14 PC rolls, all of them Spirit, and Grak made 5. The Custodian's option lists repeatedly offered Spirit rites, and the scenario's spiritual threat suits the shaman. Grak's best moments were narrative: the parley sign, the debt and the watch.

## Coherence and fun

The fiction was coherent and had a moral shape:
- the calf the clan ate belonged to the starving strangers;
- paying the debt openly opened the way to sheltering them;
- the storm then tested that choice.

The Custodian used clocks as costs, as the scenario advises: Hunger for the gift, and Pack Learns for the crowded cave. It narrated cut-forwards well once reminded. Its options lists were clear and always offered "something else".

The weakest part was the players' sameness. Their replies were sensible but alike, and they rarely surprised the Custodian.

## Procedures offered but not exercised

- the Shadow crisis and `roll.py table` (no crisis);
- a Custodian-called Luck test (Test Instinct);
- Beast Bond and `--fund`;
- the vision shard;
- initiative dice (the order was set by the stakes);
- a group combat against the pack (it never closed in);
- the Totem Mark was used once, so its once-per-session limit was never tested.

## Secrecy and access

- **Hidden material.** None reached the players: the twist, Pack Learns and the Storm clock all stayed private.
- **Shadow.** The players saw the Shadow level, on the reading that Shadow is public. Once, the Custodian also stated what Shadow 2 and 4 would do. That text is on Clanfire's Shadow track, outside the player packet's lines, but it is not secret.
- **Hunger.** The Hunger clock was shown publicly. The scenario does not say whether its clocks are public.
- **Players' tool use.** Each player agent made one tool call, its packet read, and nothing else.
- **The limit.** Access was instructed only, so these checks show compliance, not isolation.

## What to change before the programme

1. **The Custodian brief.** Include the PUBLIC block format, a worked defer-show-settle example, and "the orchestrator gives no rulings".
2. **Inventory on the sheets.** Give the Emberfall pregenerated sheets their inventory, through `update_sheet.py` in setup or in `command_snippets.md`, so a resume carries the gear.
3. **Packet delivery.** Accept a one-time packet read as the access method on Claude Code, and state it in the protocol.
4. **What the programme should record.** Two measures:
   - late Luck spending before a refill;
   - the share of rolls per character.

## Post-audit note

Astra's audit (`audit.md`) corrects two points in this report. The historical log and transcript are left unchanged.

- **The fight was one round, and one beat.** The wolf fight was one round, not two. It was also logged across beats 2 and 3, against "a fight is one beat" (Almanac 9). Counted correctly, P1 had nine scenes, six of them perilous.
- **The milestone came late.** One milestone in total is compatible with six perilous scenes. Its first valid window was the third or fourth perilous scene (C9–C12), not the close at C16.

Use these corrected counts in any later analysis of P1.

**Evidence added after the audit.** It is held in `playtests/runs/P1/tool_trace.jsonl`, recovered from the platform's stored subagent transcripts. It lists every tool call by every P1 agent:
- **Custodian:** 52 Bash, 6 Read and 16 hand-backs. None touched `campaigns/`.
- **Each player:** exactly one Read of its own packet, then hand-backs only.

The trace covers the agents' tool calls, which are the only way they reach the filesystem, so it is a full player-tool trace. It closes the access question the audit marked not assessable. It still shows compliance, not enforced isolation.
