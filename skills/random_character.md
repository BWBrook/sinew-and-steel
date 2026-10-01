---
name: random-character
description: Generate reproducible characters with the shared creation ledger and explicit tag grants.
---

# Random Character

```bash
uv run python tools/gen_character.py --campaign ice_hunt --name Tarra \
  --seed 42 --tone standard --tag "Ember-singer" --dry-run --json
```

Remove `--dry-run` to add the sheet and its campaign bookkeeping. For an exported
sheet, use `--skin clanfire --out /tmp/tarra.yaml` instead of campaign mode.

The generator reads attribute names, Luck naming, and `_gen` defaults from the
manifest. It makes trade-offs, then spends the available budget. Each trade-off
step refunds 2 points; at most 4 steps fit the shared 8-point cap. Override defaults
with `--primary`, `--steps`, or `--min-steps`/`--max-steps`; `--steps 0` starts from
the baseline before spending.

Bought `--tag` choices reserve 2 points each. A free skin grant uses repeatable
`--free-tag GRANT=NAME` and remains separate in the immutable creation snapshot.
Choose grants from the skin's rules; the generator does not invent their scope.
See [character build](character_build.md) for budgets, caps, and advancement.
