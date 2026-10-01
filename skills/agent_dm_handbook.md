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

## Mechanics and records

Use `play.py` for campaign checks, opposition, attacks, Pressure, pools, clocks,
conditions, resources, and session boundaries. `--defer` persists dice and upfront
costs; show the dice, then `settle` without rerolling. Use an explicit event ID for
safe retries. A dry-run previews an operation and creates no pending roll.

Declare semantic contexts for both sides. Pressure modifiers are snapshotted at
start, accumulate, and consume one-test penalties even when Advantage cancels
them. Supply the toll choice when required, and keep base ability costs separate
from automatic tolls. A pending crisis requires a table result, target,
adjudicated consequence, and any lasting effects before reset. Record effects'
expiry explicitly and supply their applicable modifiers on later tests.

Each able combatant acts once per round; defence uses no action. Establish side
initiative once for the fight. Twilight positions keep both their benefit and
drawback throughout the round. Supply edge, soak, and the actual legal defence;
use `opposed` instead of `attack` for a contest whose consequence is not damage.

Use `advance.py` for milestones and purchases. Creation snapshots and spending
are fixed; advancement has its own replayable entries. `recalc_sheet.py` verifies
that history rather than repricing the current scores. New campaign characters
must be added through the builders so personal Pressure and resource rosters stay
in sync. Never infer missing legacy history merely because a current sheet looks
legal.

## Public and private

Keep public narration in the conversation and public Markdown log. Store private
motives, hidden consequences, and recaps under campaign memory. Save the exact
public Custodian response with `checkpoint.py` after every turn. Resume from
current state and this checkpoint; it is not a rewind point.

A private resume includes raw sheets, tracker, memory, and log. Public mode uses
a field allowlist and excludes all raw private state and logs; its checkpoint text
must already be public. Full campaign prompts are private, including chat-mode
prompts. The compact prompt is the default; load numbered sections on demand and
check/rebuild its source fingerprint after changes.

## Session evidence

Record scene-scale beats separately from rolls. Mark perilous beats honestly,
award milestones at the book's cadence, and log recovery when it occurs. Close
only completed sessions with `play.py session-close`; start the next with `session`.
The playtest summary distinguishes complete and partial sessions and supports
review of Luck depletion and red-line duration. These logs inform a Custodian's
judgment; they do not turn a small playtest into precise balance evidence.

For an unexpected state error, stop the dependent action, inspect the receipt and
`validate_campaign.py` output, and repair the actual inconsistency. Do not reroll,
reinitialize a played campaign, or bypass a protected mechanical field through a
generic YAML updater.
