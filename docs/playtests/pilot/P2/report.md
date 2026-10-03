# P2 report (orchestrator)

P2 is Clanfire, Emberfall session 2. A fresh Custodian resumed P1's campaign, and P1's two players continued under protocol revision 3. The session finished in 10 beats over two acts. There were no orchestrator reminders, no stalls, and no reach into restricted files. All 23 checkpoints matched. These are the orchestrator's notes. Astra's audit decides rules questions.

## What happened

**Act 1 (beats 1–6):**
- Tarra brewed bark tea for the coughing Ysre children.
- Grak's natural 20 while tracking let the wolf pack see him first. In a fight in the birches he held a narrow place with Ketha's darts and Tarra's flute, and the pack withdrew.
- The pair crossed the ice to Orun's stranded party. Tarra named the sickness (a chest-rot, which meat would ease).
- Grak's failed haul brought a second fight on the ice. Flute and spear broke the pack.
- A milestone was awarded on time.
- Grak tracked and killed a stranded woolly rhino calf, the great hunt.
- Tarra's vision shard foresaw a safe return.

The act closed at the hearth.

**Act 2 (beats 7–10):**
- Tarra stopped the chest-rot at one child.
- At dawn the clan chose to feed the she-wolf, the lame wolf, now revealed as a mother with pups, rather than kill her.
- Ketha revealed that her band is forty, not nineteen.
- Both players advised settling the Ysre in the winter caves on Grak's remembered path, with a relief party south.

Shadow was purged from 1 to 0, and the session closed.

## Did revision 3 work?

| Change | Evidence in P2 |
|---|---|
| **Custodian brief** (PUBLIC block, no rulings from the orchestrator, defer and settle) | Followed unaided from the first reply. The Custodian used the no-choice shortcut correctly about 15 times, each with its reason, and checked its Luck offers with `settle --dry-run`. It asked the orchestrator for nothing. |
| **Handbook: a fight is one beat** | Both fights were single beats (2 and 4). |
| **Handbook: milestone timing** | The milestone was awarded when the third perilous beat since P1's award ended (beat 4). |
| **Handbook: name distinctive capabilities** | The Custodian offered the Totem Mark twice, the flute four times (all used), the vision shard (used), Beast Bond (declined), and the great hunt (taken), and set out a purge path. |
| **Handbook: Luck offers only when they matter** | Every offer could change the result. The pointless offers seen in P5 did not recur. |
| **Handbook: record promises as threads** | The close lists the relief party, the dawn gift, the chest-rot and the forty Ysre. |
| **Relay of completed dialogue** | The players addressed each other by name and gave each other tasks. |
| **Drives** | Grak reconsidered his own drive ("the wounded wolf I swore to finish is a mother") and chose to feed her, not kill her. |
| **Gear reconciliation** | Gear was correct at the resume. The herbs stayed used up, and the boons carried through. |

**What did not change:**

- **Pressure did not move.** No Shadow was gained in 10 beats. Shadow started at 1 and was purged to 0 at the close. The session had two pack fights, a screeching drag across open ice, a storm night and a spreading sickness, yet the Custodian charged nothing for noisy desperation or for time under threat.
  - Shadow's only live sources were failed rites. Tarra paid Luck to save the one that failed.
  - The new handbook line ("apply Pressure when the fiction triggers it") did not change the Custodian's behaviour.
  - Across P1, P5 and P2, the Pressure gained per session has been 1, 1 and 0.
- **Simultaneous declarations still clashed.** It happened three times: both players crossing the ice (P009), the flute target (P013), and who holds the bank.
  - The Custodian resolved each one inside the same reply, which is better than P5's loop.
  - The cause is structural: the players declare independently, so neither sees the other's current plan before choosing.

## Stalls and invented rules

- **No stalls.**
- **No invented rules.** The Custodian invented content but labelled all of it:
  - NPC statlines (three wolves and the rhino calf);
  - Orun's party, Ila, and the forty Ysre;
  - the boons, chosen from the seed table and said to be chosen.
- **For the audit:**
  - **Stakes stated late.** In G002 two rolls were made and settled with no public stakes beforehand, and the natural-20 cost (Pack Learns +1) was stated only privately. In G003 the stakes, labelled "as stated", first appeared in the same reply as the roll.
  - **Ketha's dart.** It gave Advantage on four spear thrusts. The Custodian flagged this as generous each time.
  - **Two rests close together.** At dusk Grak got +2 Stamina and +1 bead, and Tarra +1 Stamina (G018). Overnight, Grak got +1 Stamina and +1 bead, and Tarra +1 bead (G020). This may be two recoveries in one pause.
  - **Perilous flags:**
    - beat 3, the ice crossing, was marked perilous and is borderline by the Custodian's own note;
    - beat 7, a child's sickness, was marked not perilous; is a child's life "a life"?
  - **The vision shard.** The answer was committed before Grak's roll, but the Custodian added detail beyond yes or no ("four hurt wolves lie in the den").
  - **The Beast Bond.** It was offered on an adult wild wolf.
  - **The Shadow purge.** It was taken at the close, after the great hunt three beats earlier.
  - **A narrated effect stronger than the mechanics.** In G008 the cowed wolf "cannot turn its guard" yet defended normally. The Custodian corrected this itself at G014, where a flute win now stops the wolf's attack.

## Harness gaps and errors

1. **Combat roster.** `combat-start` cannot add a late-arriving PC to a fight in progress. The Custodian ended combat and restarted it with both PCs, then recorded passes for wolves that had already acted, so the log numbers that round as 1.
2. **Negative nudges (not a gap).** The Custodian believed a negative nudge needed `--nudge=-N`. Testing shows `--nudge -4` parses correctly, and P6 used it, so this is not a harness gap.
3. **NPC death.** There is no command to mark an NPC dead or removed; the rhino calf stays at Stamina 1.
4. **Weapon edge.** It is not on the sheet, so the obsidian point's edge +2 is supplied by hand on each roll.
5. **Notes with a colon.** `update_sheet.py --append notes=…` rejects text containing ": " ("'notes' requires a list of text"), because the value is parsed as YAML.
6. **Campaign paths.** A bare relative path such as `playtests/campaigns/p1_clanfire` resolves under `campaigns/`, so pilot runs must use absolute paths.
7. **Act counter.** After P1's closing `--act-end`, the tracker showed "Act 3 / beat 10" until the next session opened.
8. **One pending roll at a time** (noted in P1 too). Simultaneous rolls were settled one after another within a reply; this worked well.

None of these blocked play or corrupted state; each has a workaround.

## Rules-text gap

**Beast Bond.** Clanfire's Beast Bond describes a bonded beast ("such as a wolf raised from a pup") and its pool, but never says how a bond is gained: a tag, a boon or a test. The Custodian improvised a single Spirit test. This needs a sentence in Stage 3 wording; it is not a rule change.

## Pacing against Almanac 9

This is a description, not a target.

| Measure | P2 |
|---|---|
| Beats | 10 (Act 1: 6, Act 2: 4) |
| Perilous beats | 5 (4 + 1) |
| PC rolls | 24, including defence rolls (22 + 2); the fights account for most |
| Fights | 2, one beat each |
| Rests | 3 recoveries (dawn, dusk, night) |
| Milestones | 1, on time, after beat 4 |
| Shadow | 1 → 0; none gained; one purge; no crisis |
| Luck | Grak spent 10 and Tarra 3; both were near full at the close |
| Custodian replies | 23, about 270–450 words each |

The acts read well: the turn came with the rescue, then a pause at the hearth, then a closing turn with the reveal. Act 1 carried nearly all the dice; Act 2 was mostly talk and choice.

## Resume

The fresh Custodian kept continuity using only the campaign's files:
- the Ysre and Ketha;
- the lame wolf, which became the she-wolf;
- Old Orra and Hesk;
- the empty herb bundle;
- Grak's remembered path, which was in his sheet notes and was offered as the closing option.

It also refreshed the Totem Mark for the new session and carried Hunger, Pack Learns and Shadow across.

The resume had two rough edges: the absolute-path requirement, and the act counter.

## Coherence and fun

This was the strongest session of the three so far.
- The moral thread from P1, the calf that was the Ysre's kill, ran on into feeding a hungry she-wolf.
- The drives gave both characters arcs.
- The reveal at the close sets up the next session's question.

Weaknesses:
- Replies were long; the 300-word guide was routinely exceeded.
- Grak declined three expensive Luck saves in a row, so fights ran several round trips longer.
- Coordination clashes still happened. The Custodian resolved them, which cost words but no extra turns.

## Procedures offered but not exercised

- the Shadow crisis and its table;
- a Custodian-called Luck test;
- the Totem Mark (offered twice);
- Beast Bond (offered once, and declined);
- Tarra's amber pendant and her last unspent build point.

## What to change before the next round

1. **Pressure.** Handbook wording alone did not move Pressure. Three options:
   - Make "noisy desperation" and "time under threat" concrete in each skin's trigger list. That is Stage 3 wording, for Barry.
   - Add to the brief: "when a stated failure cost fits, name +1 Pressure among the options".
   - Accept that low Pressure is a result, and let the programme measure it.

   I recommend the brief change for the next round, plus a flag on the PLAN reopen trigger.
2. **Declarations.** Keep them simultaneous, but add to the Custodian brief: "When players' declarations conflict, resolve them by each player's own declared action and say so, in the same reply." P2 shows this works.
3. **Harness backlog for Stage 4.**
   - Fixes:
     - allow adding a combatant mid-fight;
     - add an NPC remove or defeat command;
     - accept notes containing a colon;
     - make a relative `--campaign` path resolve against the current directory.
   - Checks:
     - the act counter after the close;
     - weapon edge on sheets.
4. **Rules text.** One sentence on how a Beast Bond is gained.
