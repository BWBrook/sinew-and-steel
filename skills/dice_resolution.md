---
name: dice-resolution
description: Resolve campaign tests with declared stakes, saved dice, and informed Luck spending.
---

# Dice Resolution

Roll only for meaningful uncertainty. Choose the method, fitting attribute, and
stakes before the die. Supply applicable contexts and modifiers explicitly.

```bash
uv run python tools/play.py --campaign scratch_demo --character grak --seed 42 \
  --event-id crossing-roll check --attribute FLT --method "Cross the ice bridge" \
  --stakes "Cross safely; failure loses time and adds Shadow" --failure-pressure 1 --defer
uv run python tools/play.py --campaign scratch_demo --event-id crossing-settle settle
```

Read the persisted dice before settling. Add `--nudge -1 --payer grak` only if
that is the player's chosen legal spend. For opposition, use `opposed` or
`attack` with `--opponent ACTOR --defender-attribute KEY`; both dice are saved
before the Luck decision. `--nudge-target defender` can adjust the other die,
paid by a participant. `settle` never rerolls. `attack` also applies damage.
For multiple participants or dice, repeat `--adjust PAYER=SIDE:DELTA`, for example
`--adjust grak=attacker:-2 --adjust tarra=defender:-1`. Each payer covers the sum
of their absolute adjustments; opposite adjustments do not cancel the spending.

In combat, an `attack` or an `opposed` test a combatant starts uses that
combatant's action for the round. A plain `check` is a free reaction; add
`--combat-action` when the check is their action, so it gets the same turn checks
and uses the turn.

With Twilight's optional Injury module, an attack can commit damage and return
`pending` with `phase: deflection`. Read that saved die, then call `settle` again
with the chosen `--deflection-nudge` (or no nudge). Do not rerun the attack;
Deflection has its own post-roll Luck decision. Defence and Deflection rolls
never pay Pressure tolls; only the character attempting a test pays one.

The engine uses current Luck for a Luck test, after mandatory upfront costs,
and fixes that target during nudging. Natural 1 and 20 are locked; nudged endpoints
are not natural. Advantage/Disadvantage sources cancel and do not stack. Nudge
flags are accepted only on `settle`; an immediate roll command accepts its result
without nudging. A returned `settlement_error` leaves the original dice pending
for a valid settlement, never a reroll. When a skin's magic tier forbids nudges
(Iron & Ruin's Wrack and Wyrd, Candlelight's Arcanum, Mournful Shores' Incantation and
Unspeakable, Twilight's Invocation and Reckoning), declare the roll with
`--no-nudge`; `settle` then refuses any nudge to the caster's die and any nudge
the caster pays for, though a resister may nudge their own die. Declare a cost due
only on success (Candlelight's Greater Spell) with `--success-luck-cost N`: it is
set aside, paid on success and kept on failure. `settle --fund beast_bond` (Clanfire)
or `--fund companionship` (Twilight) pays the `--nudge` from that pool instead of
Luck. A test a pending crisis demands uses `check --crisis-test`, and a Luck test
the Custodian calls for uses `check --luck-test`; neither pays a toll.

Use `--context` and `--defender-context` for relevant semantic conditions: fear,
dread, ritual, clergy, repairs, melee, and so on as defined by the skin/manifest.
The engine snapshots Pressure modifiers and charges its active toll; choose
`--toll luck|pressure` when required. Declare base ability costs separately and
never charge the automatic toll twice. Use `--adv-source`/`--dis-source` for
fictional modifiers the Custodian must judge.

A seeded `--dry-run --json` is a preview, not a saved roll. Reuse a committed
operation's `--event-id` only to retry that same request. `roll.py` remains a
stateless calculator for isolated dice checks; it does not update campaign state.
See [the complete roll/combat examples](../docs/ai_play_harness.md).
