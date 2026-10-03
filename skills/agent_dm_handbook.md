---
name: agent-dm-handbook
description: Custodian operating discipline for the campaign engine, source rules, and private state.
---

# Agent DM Handbook

Read the selected skin before play. `manifest.yaml` indexes the canonical books,
skins, and mechanical metadata. Use [the harness workflow](../docs/ai_play_harness.md)
for commands and [agent bootstrap](agent_bootstrap.md) for a quick resume.

## Table discipline

- Roll only when the outcome is uncertain and failure has an interesting cost.
  Ordinary competence and settled fictional outcomes need no roll.
- Ask what the character does and how. Choose the attribute that fits; a new
  description does not make an unsuitable favourite attribute apply.
- State stakes before rolling. If two failure consequences fit, name both before
  the roll and use the book's selection procedure; do not invent a new price after
  seeing the result.
- Keep choices concrete, including plausible narrative options. Let the player
  think aloud; only fictional stalling costs time.
- Judge tags, equipment, contextual modifiers, and exceptional harm from the
  fiction. The CLI records the judgment; it does not read a description as rules.
- Apply Pressure when the fiction triggers it, including time passing under
  an active threat, noisy heroics, desperate bargains and taboo acts (Almanac 4),
  as well as when players accept it as a price. Use the skin's rules and the
  declared shared-hazard policy; do not charge for real-world deliberation or
  merely to reach a pacing figure.
- When the fiction suits a character's distinctive capability (a power, bond,
  rite, spell or signature gear), include it among the options you name. Never
  require it.
- Offer Luck when a legal spend could change the declared outcome or a
  meaningful degree of success. If no eligible player has a meaningful legal
  post-roll choice, show the dice, explain why, and settle without discretionary
  spending in the same reply. Check other abilities and payment choices too:
  an ineffective nudge does not remove Jack-of-Trades or a Spell's choice of
  Fortune versus Fatigue.

## Mechanics and records

Use `play.py` for campaign checks, opposition, attacks, Pressure, pools, clocks,
conditions, resources, and session boundaries. `--defer` persists dice and upfront
costs; show the dice, then `settle` without rerolling. Use an explicit event ID for
safe retries. A dry-run previews an operation and creates no pending roll.

Declare semantic contexts for both sides. Pressure modifiers are snapshotted at
start, accumulate, and consume one-test penalties even when Advantage cancels
them. Supply the toll choice when required, and keep base ability costs separate
from automatic tolls. A pending crisis requires a table result, target,
adjudicated consequence, and any lasting effects before reset. A failed Arcanum or
Unspeakable rite forces a crisis below 5 (`pressure --crisis --forced`); a test the
crisis itself demands rolls with `check --crisis-test` before the reset. Record effects'
expiry explicitly and supply their applicable modifiers on later tests.

Each able combatant acts once per round; defence uses no action. An `attack`, an
`opposed` test the combatant starts, or a `check` declared with `--combat-action`
uses that action; a plain `check` is a free reaction. Record a turn without a roll
with `play.py pass`. The earlier side in initiative order acts or passes before the
later side. Establish
side initiative once for the fight. Twilight positions keep both their benefit and
drawback throughout the round. Supply edge, soak, and the actual legal defence;
use `opposed` instead of `attack` for a contest whose consequence is not damage.

Use `advance.py` for milestones and purchases, while the session is open and before
`session-close`; it refuses once the session is closed. Creation snapshots and
spending are fixed; advancement has its own replayable entries. `recalc_sheet.py`
verifies that history rather than repricing the current scores. New campaign
characters must be added through the builders so personal Pressure and resource
rosters stay in sync, before the first logged action or between `session-close` and
the next `session`. Never infer missing legacy history merely because a current
sheet looks legal.

## Public and private

Keep public narration in the conversation and public Markdown log. Store private
motives, hidden consequences, and recaps under campaign memory. Save the exact
public Custodian response with `checkpoint.py` after every turn. Resume from
current state and this checkpoint; it is not a rewind point.

A private resume includes raw sheets, tracker, memory, and log. Public mode uses
a field allowlist and excludes all raw private state and logs; its checkpoint text
must already be public. Full campaign prompts are private, including chat-mode
prompts. The compact prompt is the default; load numbered sections on demand. Any
play action, checkpoint or advancement makes the saved prompt stale by design, so
rebuild it, with the same `--mode`, `--full` and `--hidden` options, before
validating or resuming.

## Session evidence

Record each scene as a beat, separately from rolls. A fight is one beat, however
many rounds it runs. Mark a beat perilous when failure in the scene could cost
Stamina, a life or the goal; assess its actual fictional stakes, not whether dice
were used. A genuine hazard resolved through preparation or a boon can qualify;
safe chores, rests and danger staged for milestone credit do not. Mark act breaks
(`--act-end`) where the story turns or pauses. Award a milestone when the third or
fourth perilous beat since the last one ends; do not save it for the session's
close. Log recovery when it occurs. Record promises made in the fiction (rewards,
debts, favours) as recap threads until they are settled. Close only completed
sessions with `play.py session-close`; start the next with `session`. Without
sittings, a session is two acts, about ten beats; Almanac 9 gives the pacing
numbers. The playtest summary distinguishes complete and partial sessions and
supports review of Luck depletion and red-line duration. These logs inform a
Custodian's judgment; they do not turn a small playtest into precise balance
evidence.

For an unexpected state error, stop the dependent action, inspect the receipt and
`validate_campaign.py` output, and repair the actual inconsistency; a stale-prompt
error only needs a rebuild. Do not reroll, reinitialize a played campaign, or
bypass a protected mechanical field through a generic YAML updater.
