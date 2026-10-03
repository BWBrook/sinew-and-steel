# Pilot protocol: simulated play

Revision 3, 3 October 2026. Drafted by Fable and amended by Astra under Barry's
instruction to review and agree the updates before the next games. Revision 2
governed P1 and P5; revision 3 applies their lessons (`pilot/review-1.md`) and
governs P2 and P6 onwards.

## Purpose

The pilot tests the procedure before the 40-run programme in `PLAN.md`. It asks
three questions:

- Can a table of AI agents play a full session of Hazardry through the harness?
- What goes wrong when they do?
- What does a session cost?

It is not balance evidence. The engine stays settled until the programme reports.

## Runs

| Run | Skin | Party | Scenario | Team |
|---|---|---|---|---|
| P1 | Clanfire | 2: Grak and Tarra | Emberfall, as published | Fable |
| P2 | Clanfire | the same 2 | P1's second session, resumed by a fresh Custodian | Fable |
| P3 | Mournful Shores | 1 | Custodian's own hidden scenario | Fable |
| P4 | Twilight of the Northlands | 3 | Custodian's own; combat positions and Injury on | Fable |
| P5 | Rust & Domes | 2 | Custodian's own | Astra |
| P6 | Candlelight Dungeons | 4 | Custodian's own; Delvekit off | Astra |
| P7 | Iron & Ruin | 1 | Custodian's own | Astra |
| P8 | Free Traders of the Drift Marches | 3 | Custodian's own | Astra |

Fable's subagents run on Claude Sonnet and Astra's on Sol. Each manifest pins the
exact model ID and settings for every role.

## The table

- **Custodian.** One agent, and the system under test: the rules, the harness and
  the quality of AI Custodian play together.
- **Players.** One agent per character, each keeping its own history. Where the
  platform limits concurrent agents, players take turns, but one model never
  plays the whole party.
- **Orchestrator.** Fable or Astra, not seated at the table. It passes public text
  between the agents, keeps the records and applies the stop rules.
- **Auditor.** The other team's model, after play. Astra's audits P1–P4, and
  Fable's audits P5–P8. The rules and the recorded evidence decide, not
  agreement between models.

## Access

Players start with no inherited history and receive their packet verbatim,
either as text or as one read of the packet file. Record the packet's SHA-256.
After that, players must not browse the repository or run tools.

On most platforms this is an instruction, not an enforced restriction, because
subagents share the filesystem and tools. Each manifest states which applies.
- Where players are only instructed, the pilot can show leakage or compliance; it
  cannot prove isolation.
- The audit checks for tool use where it can.
- A clean public transcript is not by itself evidence of secrecy.

**The player packet** contains:
- the Quickstart, The Adventurer and the Adventurer's Manual;
- the player-facing sections of the skin (its attributes, Luck, knacks or tags,
  equipment and abilities) and its Pressure track with the step effects and
  triggers, but not its crisis tables or Custodian advice;
- the character's public export (`resume_pack.py --public --character NAME
  --json`), completed with reviewed descriptions of its equipment, abilities,
  spells and the resources it controls;
- the character's drive: one line on what they want, fixed at setup;
- for P1–P2, the Emberfall player handout;
- the public narration, as play goes on.

Players never receive hidden notes, private state, crisis tables or the other
agents' instructions.

## Role briefs

**Custodian.** "You are the Custodian for a session of Hazardry, running the
campaign at PATH through the harness in this repository.
- Before you start, read `AGENTS.md` and `skills/agent_dm_handbook.md`, and
  rebuild and read the campaign prompt.
- Use `tools/play.py` and `tools/advance.py` for every roll, cost, Pressure change
  and milestone.
- Draw crisis and backlash tables with `tools/roll.py table`. Where a printed rule
  lets you choose a table result, say that you chose it.
- Never invent a die.
- Use the seed schedule in your setup notes.
- Put everything the players should see between a line `=== PUBLIC ===` and a
  line `=== END PUBLIC ===`. After the closing marker, put a `TO:` line naming
  who should answer (or `TO: none` when the session is closed). The checkpoint
  contains exactly the public body between the markers, with its final newline;
  neither marker nor routing line belongs in it. Anything outside the block goes
  to the orchestrator only. Keep private notes in the campaign files.
- The orchestrator relays and keeps records. It gives no rulings; the rules and
  your judgement decide.
- Before a roll, state the stakes. Make the roll with `--defer`, then show the
  dice and meaningful legal post-roll choices to the players who can act on them.
  Wait for those decisions before settling; never issue the roll again. If no
  eligible player has a meaningful post-roll choice, explain why and settle
  without discretionary spending in the same reply. Include abilities and
  payment choices in that check, not only Luck nudges.
- In combat, ask only the combatant or decision now due.
- Record each scene as a beat as it ends, and mark act breaks with `--act-end`.
- Save every public body with `tools/checkpoint.py`.
- Follow the table discipline and session evidence in the handbook, and the
  pacing card. After the second act, award any milestones still due, write the
  recap and close the session."

**Player.** "You play CHARACTER in a session of Hazardry, using only the packet you
were given. If setup explicitly gives a packet-file path, read that exact file
once as instructed. Otherwise, and after that read, do not use tools or read files.
- Each turn, say in character what your character does and how. Speak to the
  other characters as well as the Custodian, and play to your character's drive.
- Play cooperatively. Ask about unclear stakes or rules, and change or abandon an
  intent before committing to the roll. Once resolved, accept the result without
  seeking a reroll.
- When offered a Luck choice after a roll, decide how many tokens to spend, if
  any.
- Keep replies to two to five sentences."

## Setup (orchestrator)

1. Create the campaign under `playtests/campaigns/` with `campaign_init.py
   --base-dir playtests/campaigns`. The folder is git-ignored. Never use
   `campaigns/`.
2. Fix the roster and loadouts before play.
   - P1–P2 use Emberfall's Grak and Tarra, with their gear on the sheets
     (`examples/command_snippets.md` for a new party; the continuation procedure
     below for P2).
   - The other runs use seeded random characters. Each must have the
     capabilities its run should exercise: a sensitive in Rust, named spells in
     Candlelight, a plausible sorcerous option in Iron & Ruin, assigned crew
     roles in Free Traders. Record any adjustment.
   - Give each character a one-line drive, consistent with the sheet, and record
     it in the manifest.
3. Set the dice schedule:
   - Pick a master seed M for the run.
   - The Nth harness command that draws dice uses seed M×1000+N, with N counting
     up from 1.
   - A retry reuses its event ID and seed, including commands that produce a
     Deflection roll.
   - Seeding makes the mechanics reproducible from the command sequence. It does
     not make the narrative deterministic.
4. For runs without a published scenario, the Custodian writes its hidden
   scenario to `state/memory/hidden_scenario.md` before play.
   - The scenario gives the skin's distinctive procedures a chance to occur; it
     never forces them.
   - Never pick seeds to produce an outcome. A guaranteed outcome, such as a
     failed Unspeakable rite, belongs in a separately labelled probe.
5. Freeze a copy of the scenario, the roster and the optional modules, and start
   the manifest.

## Turn loop

1. The Custodian replies in the public-block format above. The orchestrator
   extracts the public body without rewriting it; private text and routing
   metadata are never sent to players.
2. The orchestrator gives the same frozen reply to every player who should
   answer.
   - Players answer independently. No player sees another's pending answer until
     all have answered.
   - Every player receives the public reply and the other players' completed
     answers verbatim, including when they are not due to answer. Delivery may be
     queued until that player's next turn, in chronological order. Each player
     must receive all completed public dialogue before making a new decision.
   - When the reply asks one player for a decision, only that player answers.
3. The orchestrator passes the answers to the Custodian, labelled by character.
4. The Custodian adjudicates through the harness, records what changed, saves the
   checkpoint and replies again. The orchestrator saves the reply's public block
   as its own file and checks it against the saved checkpoint before forwarding.
5. The run ends at the beat that closes the second act. The Custodian awards
   milestones, writes the recap and closes the session.

## Stop rules and interventions

- **Normal end:** the second act closes, usually after 10–12 beats.
- **Cap:** 16 beats or 150 Custodian replies. At the cap, keep the checkpoint and
  any pending state, and mark the run incomplete. Do not invent a second act or a
  session close.
- **Early ending:** a genuine ending before the cap, such as a party wipe, is
  recorded with its reason.
- **Stall:** if three replies pass without progress, the orchestrator may send one
  neutral prompt ("The scene needs a decision."). A deferred roll waiting on a
  Luck decision counts as progress.
- **Harness error:** the orchestrator may correct a malformed command, never a
  die or a state value.
- **Interventions:** any orchestrator message other than a relay counts as one,
  and goes in the manifest with its reason. Rules mistakes are not corrected
  during play; the auditor finds them afterwards.
- **Leaks:** if private material reaches the players, record it. The run then
  counts as a harness test only.

## Records

**Committed**, under `docs/playtests/pilot/RUN/`:

- **`manifest.md`:**
  - the run id, protocol revision and rules commit;
  - the skin, the frozen scenario reference, the roster and loadouts, and the
    modules;
  - the exact model ID and settings for every role;
  - the master seed;
  - whether access was enforced or only instructed;
  - the Custodian's policies on Luck tests, purges and shared hazards;
  - the start and end times, the interventions, and token and time costs for
    every role (marked estimated or unavailable where so).
- **`transcript.md`:** every exact player input and every public Custodian
  output, in order.
- **`summary.json`:** the output of `playtest_summary.py --campaign PATH --json`.
- **`audit.md`:** the auditor's verdicts, each marked correct, wrong (citing the
  rule), judgement call or not assessable. The audit covers:
  - every crisis and every unusual settlement path;
  - a declared sample of ordinary rulings; if there are fewer than ten
    consequential rulings, all of them;
  - event and message references, with citations to the rules;
  - a check that the saved checkpoints match the public text;
  - a check for leaks and tool use.
- **`report.md`:** the orchestrator's notes:
  - stalls and invented rules;
  - harness gaps and errors;
  - pacing against Almanac 9, as description, not a target;
  - coherence and fun;
  - procedures offered but not exercised;
  - what to change before the programme.

**Kept for the auditor** in the ignored run folder:
- the initial and final campaign state, the JSONL logs and the receipts;
- the frozen scenario and the exact packets delivered, with their hashes;
- each public reply as its own file, with the checkpoint comparisons;
- a command record;
- where the platform stores agent transcripts, a tool trace and token usage for
  every role.

## The continuation (P2)

Before opening session 2, reconcile the previously empty inventory fields with
P1's final fiction and receipts. Record retained, gained, traded and consumed
items and the evidence for each change; do not replenish the starting handout
gear by default. Keep P1's frozen final snapshot unchanged and put this setup
adjustment in P2's manifest.

A fresh Custodian receives only the documented bootstrap materials
(`skills/agent_bootstrap.md`). It rebuilds the prompt and loads the resume pack
and the checkpoint. The player agents carry on from P1 where the platform keeps
them; otherwise fresh players get character-filtered public packets. P2 tests
resuming, Pressure carried across sessions, and once-per-session powers
refreshing.

## After the pilot

Fable and Astra compare the eight reports and propose changes for Barry before the
40-run programme: to this protocol, to the briefs, and any harness fixes. No rule
changes follow from the pilot alone.
