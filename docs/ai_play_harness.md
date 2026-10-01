# AI Play Harness Workflow

Use the harness to keep a campaign's rules, dice, character history, Pressure,
and private notes consistent across sessions. `play.py` handles mechanical state;
the Custodian still judges intent, plausible methods, stakes, and consequences.
Roll only when the outcome is uncertain and failure would matter.

## Setup and characters

```bash
uv sync
uv run python tools/validate_repo.py
uv run python tools/campaign_init.py --slug emberfall --title Emberfall --skin clanfire --tone standard
uv run python tools/char_builder.py --campaign emberfall --name Grak \
  --set MGT=12 --set SPR=8 --set INS=8 --set STM=7 --tag "Megafauna tracker"
uv run python tools/validate_campaign.py --campaign emberfall
```

Alternatively, pass `--random-character Grak --seed 42` when initializing the
campaign. Add `--dry-run --json` to preview generation without creating files.
Character builders add the sheet and its Pressure/resource bookkeeping together;
they refuse to overwrite an existing campaign character.

Campaign data lives under `campaigns/<slug>/state/`: sheets in `characters/`,
mechanical state in `trackers/session.yaml`, private recaps in `memory/`, public
narration and structured events in `logs/`, and the exact last public response in
`checkpoints/last.md`. Operation receipts support safe retries. Keep this state
private; public exports deliberately include only selected fields.

Creation starts with five attributes at 10 and Stamina at 5. Reductions fund
raises, with at most 8 refunded points in total. Tags cost 2 build points each;
spare reductions cannot buy them, including on the grim budget. Skin grants are
explicit, for example `--free-tag "knack=Occult Scholar"` in Whispers. Candlelight and Free Traders also grant an Expertise. M-field sensitive
in Rust & Domes is a bought tag, not another attribute.

## Prompts and source checks

```bash
uv run python tools/build_prompt.py --campaign emberfall
uv run python tools/build_prompt.py --campaign emberfall --check --json
uv run python tools/build_prompt.py --section manual:6
uv run python tools/build_prompt.py --campaign emberfall --full
```

The default compact prompt contains the Quickstart, complete selected skin and
addons, current state, and a detailed-rule lookup index. `--full` embeds both core
books. `--section manual:6` prints combat rules without rebuilding a campaign
prompt; repeat `--section` to retrieve more sections. `--check` checks the saved
prompt's body, sources, and campaign file inventory without writing. Rebuild a
stale prompt before resuming. Artwork is stripped unless `--keep-art` is supplied.

Campaign-local `state/memory/hidden_scenario.md` is included automatically. Use
`--hidden rules/scenarios/clanfire_emberfall_hidden.md` for a supplied module or
another explicit file. Assembled prompts contain private material: do not send
one to the players. `--mode chat` changes the template for copy/paste play; it does
not turn a private campaign prompt into a public export.

## Checks and informed Luck spending

State the method and both possible outcomes before rolling. Choose the attribute
that fits the method, and supply applicable contexts and Advantage sources.

```bash
uv run python tools/play.py --campaign emberfall --character grak --seed 42 \
  --event-id river-roll check --attribute FLT --method "Cross on the fallen tree" \
  --stakes "Reach the far bank; failure loses time and adds Shadow" \
  --failure-pressure 1 --defer
uv run python tools/play.py --campaign emberfall --event-id river-settle settle
```

`--defer` saves the raw dice and upfront costs. Show the dice to the player, then
use `settle` once they choose; it never rerolls the saved action. To spend Luck,
add, for example, `--nudge -1 --payer grak`; an opposed test can instead use
`--nudge-target defender`. The payer must participate. A natural 1 or 20 is locked,
and a nudged endpoint is not natural. Both opposed dice are visible before this
decision. Nudge flags belong to `settle`. Without `--defer`, the command accepts
the result without a Luck nudge. If settlement cannot pay a required cost, the
receipt retains the pending dice and upfront costs with `settlement_error`;
inspect that reason and settle the saved action rather than rolling again.

For several adjustments, repeat `--adjust PAYER=SIDE:DELTA`, for example
`settle --adjust mara=attacker:-2 --adjust holo=defender:-1`. Either participant
may adjust either rolled die, paying from their own pool. Each adjustment costs
its absolute amount even if another adjustment offsets it. The whole settlement
must be legal and affordable. `--companionship` funds only the one-point
`--nudge` convenience option; `--adjust` spends ordinary Luck.

Use a stable `--event-id` for each write. Repeating the same command with the same
ID returns its saved receipt; using that ID for a changed command fails. An
operation without an explicit ID receives a new one. A seed reproduces dice; it
does not make a second command a safe retry. `--dry-run --json` previews without
saving an action, so it cannot be followed by `settle` until the action is committed.

### Contexts, costs, and conditions

The engine does not infer circumstances from prose. Supply every relevant
`--context`; `risky` is added automatically. Common skin-specific contexts are:

| Fiction | Context |
|---|---|
| Clanfire rite / Iron & Ruin ritual | `rite` / `ritual` |
| Dealing with clergy / open defiance | `clergy` / `open_defiance` |
| Black-market dealing | `black_market` |
| Time-sensitive Service Duct repairs | `time_sensitive_repair` |
| Whispers fear or coercion | `fear` / `coercion` |
| Twilight dread test | `dread` |
| Combat approach and defence | `melee`, `missile`, `screened`, as applicable |

For opposition, give the defender's contexts with `--defender-context`. The
engine snapshots applicable Pressure effects at action start, consumes a pending
one-test penalty even if Advantage cancels it, and charges the active toll.
Where a toll offers a choice, supply `--toll luck` or `--toll pressure` (and
`--defender-toll` when needed). Base ability costs use `--luck-cost` and
`--pressure-cost`; do not add the automatic toll again. A Luck target uses current
tokens after mandatory upfront costs and remains fixed during nudging.

Use `--adv-source "reason"` and `--dis-source "reason"` for adjudicated modifiers,
including those a skin leaves to the Custodian. Tags, equipment, exhaustion, and
lasting crisis effects still require the applicable fictional judgment. Known
limited abilities can be charged with `--use-resource NAME`; this records use,
not an inferred benefit from its prose. Declare the relevant Advantage source.

## Opponents and combat

Register an NPC, then establish side order once. Omit `--order` to roll initiative;
use it only when the fiction already establishes who acts first.

```bash
uv run python tools/play.py --campaign emberfall npc --id wolf --stat MGT=10 --stat FLT=10 --stamina 4
uv run python tools/play.py --campaign emberfall combat-start --side clan=grak --side pack=npc:wolf --order clan,pack
uv run python tools/play.py --campaign emberfall --character grak --seed 42 \
  --event-id wolf-strike attack --attribute MGT --opponent npc:wolf --defender-attribute FLT \
  --context melee --defender-context melee --edge 1 --soak 0 \
  --method "Keep the wolf back with the spear" --stakes "Wound it if the attack wins" --defer
uv run python tools/play.py --campaign emberfall --event-id wolf-settle settle
```

`attack` applies winning damage to the target; `opposed` resolves a contest without
damage. Edge belongs to the attacking weapon and soak to the defender. Use
`--actor npc:wolf` for the NPC's turn. Each able combatant gets one action;
defending consumes none. `pass --actor grak --reason "Drag Tarra into cover"`
records a turn used for another activity. After all able combatants act, `round`
starts the next round and retains initiative. End with `combat-end --reason ...`.
The Custodian judges whether a defence is possible; `--undefended` records that
ruling for an attack.

Twilight positions are declared for every combatant before the round begins,
using `positions --position grak=vanguard ...` and subsequent
`round --position ...` declarations. Benefits and drawbacks stay together for
the round. Supply melee/missile/screened contexts correctly. Its optional Injury
module uses `--injury` (and optionally `--gritty`); Companionship nudges use
`settle --nudge -1 --companionship`. Read the skin before enabling these options.

An Injury-triggering attack may return another pending action with
`phase: deflection` after its damage is committed. Read that stored Deflection
die, then run `settle` again, optionally with `--deflection-nudge -1` and
`--companionship` if chosen and legal. This is a second informed Luck decision;
do not rerun the attack or choose its Deflection nudge before seeing the die.
When a forthcoming Deflection requires a different mandatory toll, supply
`--deflection-toll luck|pressure` while settling the attack.

## Pressure and crises

Pressure is structured tracker state, never a character pool. Most skins share
a party track; Whispers has an Insanity track for each investigator. Select the
affected investigator with `--character` for personal changes. For shared gains,
use `--character` when one action identifies the tipper; omit it for a group hazard.

```bash
uv run python tools/play.py --campaign emberfall pressure --gain 1 --category ambient --source "Storm closes the pass"
uv run python tools/play.py --campaign emberfall pressure --purge 1 --source "Safe shelter"
```

Effects accumulate at their thresholds. One-test penalties fire once per crisis
cycle; recovery discards unused penalties above the new level without re-arming
them. At 5 a crisis stays pending. Read the skin's table, establish its target and
consequence, and apply any mechanical harm/cost with the appropriate command.
Then record the adjudicated table result and lasting effects to reset the track:

```bash
uv run python tools/play.py --campaign emberfall pressure --crisis --target grak \
  --table-result 2 --source "Describe the actual adjudicated consequence" \
  --effect "Describe its lasting effect=until the stated recovery condition"
```

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
uv run python tools/play.py --campaign emberfall --character grak luck --amount 1 --source "Short rest"
uv run python tools/play.py --campaign emberfall --character grak stamina --amount 1 --source "Short rest"
uv run python tools/play.py --campaign emberfall beat --perilous --label "Survived the crossing"
uv run python tools/advance.py --campaign emberfall --character grak --event-id ridge-award \
  award --id ridge --boon "A sheltered camp"
uv run python tools/advance.py --campaign emberfall --character grak raise --stat MGT
uv run python tools/advance.py --campaign emberfall --character grak show --json
```

A beat is a scene-scale development, not an individual die roll. The Custodian
awards milestones at the book's cadence; each grants 2 points, a narrative boon,
and full Luck. `advance.py` records the award and each purchase separately from
the immutable creation snapshot. A +1 costs 1 below baseline or 2 at/above it;
`tag --name "Steady hands"` costs 2. Unspent points carry over. Attribute 16 and
Stamina 9 remain lifetime ceilings. Raising a maximum does not heal or refill a
current pool. `recalc_sheet.py` verifies this history; it never erases advancement
by repricing the current scores.

`scene --label ...` resets scene uses. `boundary --kind camp|port --reason ...`
resets relevant skin uses when the fiction allows it. These boundaries do not
substitute for explicit Luck, Stamina, or Pressure recovery.

```bash
uv run python tools/recap.py --campaign emberfall --summary "The clan found shelter; the wolf still follows."
uv run python tools/session_log.py --campaign emberfall --role GM --text "Public narration only."
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign emberfall
uv run python tools/play.py --campaign emberfall session-close --label "End of the first session"
uv run python tools/playtest_summary.py --campaign emberfall --json
uv run python tools/play.py --campaign emberfall session --label "The next morning"
```

Save the exact public Custodian response after every turn. Private summaries
belong in memory. `session-close` marks a completed session for the telemetry
summary; `session` begins the next one and creates matching memory/log files.
Add characters before the first action, or between `session-close` and `session`.
The roster stays fixed within each logged session so party-size comparisons remain
valid. Adding a character increases a shared pool's capacity without restoring
tokens spent in play.
The summary separates completed and incomplete sessions so a truncated run does
not masquerade as a full session's midpoint or Pressure window. Luck movements,
Pressure sources, roll methods, and crisis targets are recorded by the engine.
The first session after legacy migration is marked as partial history even when
closed; the following session can contribute to the completed-session evidence.
They support playtest review; they do not decide whether a rule should change.
Without beat events, midpoint and beat-rate results are unavailable. Open red-line
windows remain censored, even at session end. The summary's default threshold of
more than 3 affected rolls is a provisional reading of “a few”; change it with
`--red-line-rolls N` and keep that choice visible when comparing runs.

## Resume and legacy state

```bash
uv run python tools/resume_pack.py --campaign emberfall
uv run python tools/resume_pack.py --campaign emberfall --public --json
```

The private pack includes the authoritative sheets, tracker, latest memory/log,
and exact checkpoint. Public mode allows selected campaign/character fields,
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
