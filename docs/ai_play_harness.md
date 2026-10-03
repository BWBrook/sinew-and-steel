# AI Play Harness Workflow

Use the harness to keep a campaign's rules, dice, character history, Pressure,
and private notes consistent across sessions. `play.py` handles mechanical state;
the Custodian still judges intent, plausible methods, stakes, and consequences.
Roll only when the outcome is uncertain and failure would matter. The examples
use a throwaway campaign slug, `scratch_demo`; never run them against a real
campaign.

## Setup and characters

```bash
uv sync
uv run python tools/validate_repo.py
uv run python tools/campaign_init.py --slug scratch_demo --title "Scratch Demo" --skin clanfire --tone standard
uv run python tools/char_builder.py --campaign scratch_demo --name Grak \
  --set MGT=12 --set SPR=8 --set INS=8 --set STM=7 --tag "Megafauna tracker"
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/validate_campaign.py --campaign scratch_demo
```

Alternatively, pass `--random-character Grak --seed 42` when initializing the
campaign. Add `--dry-run --json` to preview generation without creating files.
Character builders add the sheet and its Pressure/resource bookkeeping together;
they refuse to overwrite an existing campaign character. Add characters before
the first logged action, or after `session-close` and before the next `session`;
the engine refuses a mid-session addition. Build the prompt before validating,
because a saved prompt older than the latest state change is stale by design.

Campaign data lives under `campaigns/<slug>/state/`: sheets in `characters/`,
mechanical state in `trackers/session.yaml`, private recaps in `memory/`, public
narration and structured events in `logs/`, and the exact last public response in
`checkpoints/last.md`. Operation receipts support safe retries. Keep this state
private; public exports deliberately include only selected fields.

Creation starts with five attributes at 10 and Stamina at 5. Reductions fund
raises, with at most 8 refunded points in total. Tags cost 2 build points each;
spare reductions cannot buy them, including on the grim budget. Skin grants are
explicit, for example `--free-tag "knack=Occult Scholar"` in Mournful Shores. Candlelight and Free Traders also grant an Expertise. M-field sensitive
in Rust & Domes is a bought tag, not another attribute.

## Prompts and source checks

```bash
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/build_prompt.py --campaign scratch_demo --check --json
uv run python tools/build_prompt.py --section manual:6
uv run python tools/build_prompt.py --campaign scratch_demo --full
```

The default compact prompt contains the Quickstart, complete selected skin and
addons, current state, and a detailed-rule lookup index. `--full` embeds both core
books. `--section manual:6` prints combat rules without rebuilding a campaign
prompt; repeat `--section` to retrieve more sections. `--check` checks the saved
prompt's body, sources, and campaign file inventory without writing. Artwork is
stripped unless `--keep-art` is supplied.

Any play action, checkpoint, or advancement makes the saved prompt stale by design,
and `validate_campaign.py` reports a stale prompt as an error. Rebuild it before
validating or resuming. `--mode`, `--full`, `--keep-art`, and `--hidden` are not
remembered, so pass them again on every rebuild; the header comment on the first
line of `prompt.md` records the mode, profile, and sources of the last build.

Hidden scenario material belongs in `campaigns/<slug>/state/memory/hidden_scenario.md`,
which every rebuild includes automatically. Use
`--hidden rules/scenarios/clanfire_emberfall_hidden.md` only for a one-off prompt
from a supplied module or another explicit file. Assembled prompts contain private
material: do not send one to the players. `--mode chat` changes the template for
copy/paste play and defaults to both full books, because a chat model cannot read
this repository (`--profile compact` opts out); it does not turn a private campaign
prompt into a public export.

## Checks and informed Luck spending

State the method and both possible outcomes before rolling. Choose the attribute
that fits the method, and supply applicable contexts and Advantage sources.

```bash
uv run python tools/play.py --campaign scratch_demo --character grak --seed 42 \
  --event-id river-roll check --attribute FLT --method "Cross on the fallen tree" \
  --stakes "Reach the far bank; failure loses time and adds Shadow" \
  --failure-pressure 1 --defer
uv run python tools/play.py --campaign scratch_demo --event-id river-settle settle
```

`--character` takes the sheet's file stem (`grak` for Grak).
`--defer` saves the raw dice and upfront costs. Show the dice to the player, then
use `settle` once they choose; it never rerolls the saved action. To spend Luck,
add, for example, `--nudge -1 --payer grak`; an opposed test can instead use
`--nudge-target defender`. The payer must participate. A natural 1 or 20 is locked,
and a nudged endpoint is not natural. Both opposed dice are visible before this
decision. Nudge flags belong to `settle`. Without `--defer`, the command accepts
the result without a Luck nudge. If settlement cannot pay a required cost, the
receipt retains the pending dice and upfront costs with `settlement_error`;
inspect that reason and settle the saved action rather than rolling again.

Some skins forbid nudging their top magic tiers: Iron & Ruin's Wrack and Wyrd,
Candlelight's Arcanum, Mournful Shores' Incantation and Unspeakable, and Twilight's
Invocation and Reckoning. Declare `--no-nudge` on that roll. `settle` then refuses
any nudge or adjustment to the caster's die, and any nudge the caster pays for on
either die; a resisting character may still nudge their own die.

A cost the method charges only on success, such as Candlelight's Greater Spell
coin, is declared with `--success-luck-cost N`. Those tokens are set aside at the
roll: `settle` will not spend them on a nudge, pays them once if the roll succeeds,
and leaves them in the pool if it fails.

For several adjustments, repeat `--adjust PAYER=SIDE:DELTA`, for example
`settle --adjust mara=attacker:-2 --adjust holo=defender:-1`. Either participant
may adjust either rolled die, paying from their own pool. Each adjustment costs
its absolute amount even if another adjustment offsets it. The whole settlement
must be legal and affordable. `--fund NAME` pays the `--nudge` convenience option
from a pool the skin reserves for nudges instead of Luck: `companionship` (one
point, once per scene, in Twilight) or `beast_bond` (one bead per point, from the
acting character's bonded beast, in Clanfire). `--adjust` always spends ordinary
Luck. When a beast's beads reach 0, the Custodian decides what the beast does.

Use a stable `--event-id` for each write. Repeating the same command with the same
ID returns its saved receipt; using that ID for a changed command fails. IDs are
case-insensitive, and an ID belongs to the session that first used it: reusing it
in a later session fails, so choose a fresh one. An operation without an explicit
ID receives a new one. A seed reproduces dice; it
does not make a second command a safe retry. `--dry-run --json` previews without
saving an action, so it cannot be followed by `settle` until the action is committed.

Every write is journaled. If a command is interrupted part-way, the next writing
command restores the campaign first. Until then `build_prompt.py`, `resume_pack.py`,
`summary.py`, `playtest_summary.py` and `validate_campaign.py` refuse to read it;
run `play.py --campaign <slug> status` to restore it.

### Contexts, costs, and conditions

The engine does not infer circumstances from prose. Supply every relevant
`--context`; `risky` is added automatically. Common skin-specific contexts are:

| Fiction | Context |
|---|---|
| Clanfire rite / Iron & Ruin ritual | `rite` / `ritual` |
| Dealing with clergy / open defiance | `clergy` / `open_defiance` |
| Black-market dealing | `black_market` |
| Time-sensitive Service Duct repairs | `time_sensitive_repair` |
| Mournful Shores fear or coercion | `fear` / `coercion` |
| Twilight dread test | `dread` |
| Combat approach and defence | `melee`, `missile`, `screened`, as applicable |

For opposition, give the defender's contexts with `--defender-context`. The
engine snapshots applicable Pressure effects at action start, consumes a pending
one-test penalty even if Advantage cancels it, and charges the active toll.
Where a toll offers a choice, supply `--toll luck` or `--toll pressure`. Only
the character attempting the test pays; a defence or Deflection roll never pays a
toll, although step penalties still apply to it. Base ability costs use `--luck-cost` and
`--pressure-cost`; do not add the automatic toll again. A Luck target uses current
tokens after mandatory upfront costs and remains fixed during nudging.

Use `--adv-source "reason"` and `--dis-source "reason"` for adjudicated modifiers,
including those a skin leaves to the Custodian. Tags, equipment, exhaustion, and
lasting crisis effects still require the applicable fictional judgment. Known
limited abilities can be charged with `--use-resource NAME`; this records use,
not an inferred benefit from its prose. Declare the relevant Advantage source.
Name a resource by its manifest id (for example `totem_mark`, `beast_bond`, or
`companionship`), not its display name; `play.py status` lists a campaign's ids
under `resources`.

Outside a roll, `play.py resource` records the use of a limited ability, or
restores pool tokens with `--recover` when the fiction allows it. `play.py
condition` sets or clears a named condition on a sheet.

```bash
uv run python tools/play.py --campaign scratch_demo --character grak resource --name totem_mark --source "Calls on the totem"
uv run python tools/play.py --campaign scratch_demo --character grak resource --name beast_bond --recover --amount 1 --source "Bond rite at the fire"
uv run python tools/play.py --campaign scratch_demo --character grak condition --name injured --source "Spear wound"
uv run python tools/play.py --campaign scratch_demo --character grak condition --name injured --clear --source "Healing rest"
```

## Opponents and combat

Register an NPC, then establish side order once. Omit `--order` to roll initiative;
use it only when the fiction already establishes who acts first.

```bash
uv run python tools/play.py --campaign scratch_demo npc --id wolf --stat MGT=10 --stat FLT=10 --stamina 4
uv run python tools/play.py --campaign scratch_demo combat-start --side clan=grak --side pack=npc:wolf --order clan,pack
uv run python tools/play.py --campaign scratch_demo --character grak --seed 42 \
  --event-id wolf-strike attack --attribute MGT --opponent npc:wolf --defender-attribute FLT \
  --context melee --defender-context melee --edge 1 --soak 0 \
  --method "Keep the wolf back with the spear" --stakes "Wound it if the attack wins" --defer
uv run python tools/play.py --campaign scratch_demo --event-id wolf-settle settle
```

`attack` applies winning damage to the target; `opposed` resolves a contest without
damage. Edge belongs to the attacking weapon and soak to the defender. Add
`--actor npc:wolf` after the subcommand for the NPC's turn. Each able combatant
gets one action per round, and defending consumes none. An `attack`, or an
`opposed` test the combatant starts (intimidate, disarm, shove), uses that action.
A plain `check` is a free reaction; when a check *is* the combatant's action (a
spell on themselves, working a device), add `--combat-action`, which applies the
same turn checks and uses the action. Record a turn spent on anything without a
roll with `pass --actor grak --reason "Drag Tarra into cover"`. The earlier side in
initiative order must act or pass before the later side; the engine refuses an
action from a combatant who has already acted or is at 0 Stamina. After all able combatants act, `round`
starts the next round and retains initiative. End with `combat-end --reason ...`.
The Custodian judges whether a defence is possible; `--undefended` records that
ruling for an attack.

Twilight positions are declared for every combatant before the round begins,
using `positions --position grak=vanguard ...` and subsequent
`round --position ...` declarations. Benefits and drawbacks stay together for
the round. Supply melee/missile/screened contexts correctly. Its optional Injury
module uses `--injury` (and optionally `--gritty`); Companionship nudges use
`settle --nudge -1 --fund companionship`. Read the skin before enabling these options.

An Injury-triggering attack may return another pending action with
`phase: deflection` after its damage is committed. Read that stored Deflection
die, then run `settle` again, optionally with `--deflection-nudge -1` and
`--fund companionship` if chosen and legal. This is a second informed Luck decision;
do not rerun the attack or choose its Deflection nudge before seeing the die.
Deflection pays no toll.

## Pressure and crises

Pressure is structured tracker state, never a character pool. Most skins share
a party track; Mournful Shores has an Insanity track for each investigator. Select the
affected investigator with `--character` for personal changes. For shared gains,
use `--character` when one action identifies the tipper; omit it for a group hazard.

```bash
uv run python tools/play.py --campaign scratch_demo pressure --gain 1 --category ambient --source "Storm closes the pass"
uv run python tools/play.py --campaign scratch_demo pressure --purge 1 --source "Safe shelter"
```

Effects accumulate at their thresholds. One-test penalties fire once per crisis
cycle; recovery discards unused penalties above the new level without re-arming
them. At 5 a crisis stays pending. Read the skin's table, establish its target and
consequence, and apply any mechanical harm/cost with the appropriate command.
Then record the adjudicated table result and lasting effects to reset the track:

```bash
uv run python tools/play.py --campaign scratch_demo pressure --crisis --target grak \
  --table-result 2 --source "Describe the actual adjudicated consequence" \
  --effect "Describe its lasting effect=until the stated recovery condition"
```

A failed Arcanum (Candlelight) or Unspeakable rite (Mournful Shores) causes a crisis even
below 5. Record it with `pressure --crisis --forced --character CASTER ...`; it falls
on the caster and resets the track. If the rite also took the track to 5, it is
still one crisis. Service Duct Blues' nanite alarm asks for a SYS test during the
crisis: roll it with `check --crisis-test` while the crisis is pending (it pays no
toll or cost; step penalties apply), then record the crisis with the outcome. A Luck
test the Custodian calls for ("Test your Luck!") is not a chosen attempt either:
roll it with `check --attribute <luck key> --luck-test`. A Luck-attribute test a
character chooses, such as Time Odyssey's lateral leap, pays tolls as usual.

The command is a recording form, not a substitute for the selected skin's table.
If the table calls for multiple outcomes, repeat `--table-result` after resolving
them. If no single character tipped a shared track, the Custodian chooses the
character the fiction points to. Crisis consequences may outlast the reset;
duration text is stored, not interpreted as an automatic expiry rule. Apply an
active consequence with `--dis-source` when it fits, and end its returned effect
ID with `effect-end --id ID --reason "Recovery condition met"`. Do not replace a
crisis with a generic clock reset.

## Recovery, advancement, and session records

Record adjudicated recovery and damage through the engine:

```bash
uv run python tools/play.py --campaign scratch_demo --character grak luck --amount 1 --source "Short rest"
uv run python tools/play.py --campaign scratch_demo --character grak stamina --amount 1 --source "Short rest"
uv run python tools/play.py --campaign scratch_demo beat --perilous --label "Survived the crossing"
uv run python tools/advance.py --campaign scratch_demo --character grak --event-id ridge-award \
  award --id ridge --boon "A sheltered camp"
uv run python tools/advance.py --campaign scratch_demo --character grak raise --stat MGT
uv run python tools/advance.py --campaign scratch_demo --character grak show --json
```

A beat is a scene, not an individual die roll: one situation with one open
question, ending when the question is answered, dropped or changed. Record each
with `beat --label "what changed"` as the scene ends, adding `--perilous` when
failure could cost Stamina, a life or the goal, and `--act-end` when it ends an
act (a turn or a pause, usually after four to six beats). Ending a beat begins the
next scene and resets once-per-scene limits. Without sittings, a session is two
acts, about ten beats: the beat that ends the second act returns a reminder to
award any milestone and close the session. Almanac 9 gives the pacing numbers.

The Custodian awards milestones at the book's cadence; each grants 2 points, a narrative boon,
and full Luck. In Clanfire it also refills a bonded beast's beads if the beast is
still with the character; the award receipt reminds you, and `resource --name
beast_bond --recover --amount 3` records it. Award milestones and record purchases
while the session is open,
before `session-close`; `advance.py` refuses while a session is closed or an
action is pending. `advance.py` records the award and each purchase separately from
the immutable creation snapshot. A +1 costs 1 below baseline or 2 at/above it;
`tag --name "Steady hands"` costs 2. Unspent points carry over. Attribute 16 and
Stamina 9 remain lifetime ceilings. Raising Stamina does not heal. Raising the Luck
attribute adds its new token too, so a milestone spent on Luck still ends with a
full pool. `recalc_sheet.py` verifies this history; it never erases advancement
by repricing the current scores.

`boundary --kind camp|port --reason ...` resets relevant skin uses when the
fiction allows it. These boundaries do not
substitute for explicit Luck, Stamina, or Pressure recovery.

```bash
uv run python tools/recap.py --campaign scratch_demo --summary "The clan found shelter; the wolf still follows."
uv run python tools/session_log.py --campaign scratch_demo --role GM --text "Public narration only."
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign scratch_demo
uv run python tools/play.py --campaign scratch_demo session-close --label "End of the first session"
uv run python tools/playtest_summary.py --campaign scratch_demo --json
uv run python tools/play.py --campaign scratch_demo session --label "The next morning"
```

Save the exact public Custodian response after every turn. Private summaries
belong in memory. `session-close` marks a completed session for the telemetry
summary (end any combat and settle pending actions and crises first); `session`
begins the next one and creates matching memory/log files. The new memory file
carries forward open threads, NPCs and secrets, and starts a fresh summary.
Add characters before the first logged action, or after `session-close` and before
the next `session`, never mid-session. A character who dies or leaves stays on the
roster until the session closes; then `play.py --character NAME retire --reason ...`
moves the sheet to `state/characters/retired/` and shrinks the shared pools. The
next session records the smaller party.
The roster stays fixed within each logged session so party-size comparisons remain
valid. Adding a character increases a shared pool's capacity without restoring
tokens spent in play.
The summary separates completed and incomplete sessions so a truncated run does
not masquerade as a full session's midpoint or Pressure window. Luck movements,
Pressure sources, roll methods, and crisis targets are recorded by the engine.
The first session after legacy migration is marked as partial history even when
closed; the following session can contribute to the completed-session evidence.
They support playtest review; they do not decide whether a rule should change.
The summary reports each act, and a session's midpoint is the end of its first
act, so without an act break the midpoint results are unavailable; without beats,
so are beat rates. Red-line windows report the beats they span as well as their
affected rolls, and open windows remain censored, even at session end. The summary's default threshold of
more than 3 affected rolls is a provisional reading of “a few”; change it with
`--red-line-rolls N` and keep that choice visible when comparing runs.

## Resume and legacy state

```bash
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/resume_pack.py --campaign scratch_demo
uv run python tools/resume_pack.py --campaign scratch_demo --public --json
```

Rebuild the saved prompt first, with the same options as before (see Prompts and
source checks). `--character <character_slug>` filters a pack to one sheet, so omit
it for a party. The private pack includes the authoritative sheets, tracker, latest
memory/log, and exact checkpoint. Public mode allows selected campaign/character fields,
scene number, and checkpoint text only. It omits logs, private memory, hidden
clocks, arbitrary sheet fields, and paths. The checkpoint must already contain
only the public response; the tool cannot detect a secret inside that prose.

Legacy campaigns require an explicit history decision. Preview a known fresh,
unadvanced campaign with:

```bash
uv run python tools/migrate_campaign.py --campaign OLD_CAMPAIGN --fresh-pressure --fresh-resources --adopt-creation --json
```

Only add `--apply` after reviewing that preview. `--fresh-pressure` asserts a
known fresh/crisis-reset zero with no pending effects; otherwise provide reviewed
schema-2 Pressure data with `--pressure-state FILE`. Separately,
`--fresh-resources` asserts initial pool balances and unused ability limits; use
`--resources-state FILE` for reviewed resource state otherwise. `--adopt-creation` asserts
that legacy characters have never advanced and their existing tags were bought.
Ambiguous advancement, free-grant provenance, nonzero character Pressure, or
missing fired-threshold history needs manual reconstruction. The migration tool
backs up originals; no private campaign is migrated automatically.
