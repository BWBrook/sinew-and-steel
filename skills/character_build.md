---
name: character-build
description: Create legal sheets and record milestone advancement without repricing creation.
---

# Character Build

Start with five attributes at 10 and Stamina (`STM`) at 5. Attributes remain
6–16 and Stamina 3–9 for the character's life. Lowering scores funds raises, with
an 8-point refund cap across attributes and Stamina together. A +1 costs 1 point
while below baseline and 2 at or above it.

Budgets are `--tone grim` (0), `standard` (6), `pulp` (12), or `heroic` (16), or
`--build-points N`. Campaign mode reads the campaign's budget.

```bash
uv run python tools/char_builder.py --campaign ice_hunt --name Grak \
  --set MGT=12 --set SPR=8 --set INS=8 --set STM=7 --tag "Megafauna tracker" --dry-run --json
```

The example spends exactly 6 points. Remove `--dry-run` to add the character.
`--set KEY=N` assigns scores; `--delta KEY=N` adjusts the baseline before those
assignments. `--strict` disallows voluntary extra weaknesses. Use `--skin` and
`--out FILE` for a standalone sheet.

## Bought tags and grants

Bought tags cost 2 points each and use `--tag NAME`. Spare lowering refunds never
buy tags, so the grim budget cannot buy one. A skin's free tags use
`--free-tag knack=NAME` or `--free-tag expertise=NAME` and are recorded separately.
Candlelight and Free Traders grant one of each; Whispers and Twilight grant one
Knack. Further tags cost 2. Agree their scope from the skin and fiction.
Rust & Domes' M-field sensitive is a bought 2-point tag, with no extra attribute or
invented score prerequisite.

## Advancement

```bash
uv run python tools/advance.py --campaign ice_hunt --character grak \
  --event-id ridge-milestone award --id ridge --boon "A sheltered camp"
uv run python tools/advance.py --campaign ice_hunt --character grak raise --stat MGT
uv run python tools/advance.py --campaign ice_hunt --character grak show --json
```

Each milestone awards 2 points and refills Luck. `raise --stat KEY --steps N`
records each +1 and its actual price; `tag --name NAME` buys a tag. Add
`--dry-run --json` to preview any purchase. Unspent points carry over. Increasing
a pool maximum leaves current tokens/health unchanged.

Schema-2 sheets preserve `creation.snapshot` and `creation.build_points_used`.
`advancement.entries` records awards and purchases; validation replays them and
checks the current sheet. A capped creation refund can leave the current creation
price unchanged after a raise: the advancement point is still spent.

Use `validate_sheet.py` to check the result. `recalc_sheet.py` refreshes derived
pool metadata while preserving the snapshot and every purchase; it does not
repair a hand-edited score by erasing its spending history. Legacy adoption
requires `--adopt-creation`, asserting that the character has never advanced and
all existing tags were bought. Ambiguous histories need manual reconstruction.
