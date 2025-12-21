---
name: character-build
description: Build character sheets with point-buy validation or random generation.
---

# Character Build

## Goal
Create a legal character sheet for a chosen skin, either random or point-buy.

## Random generation
```bash
python tools/gen_character.py --skin <skin> --name "Name" --out state/characters/name.yaml
```

## Point-buy build (manual)
Provide stats explicitly (each stat 6–16) following the **double-debit** rule:
- Baseline is 10 in every stat.
- For every **+1 above 10**, subtract **-2 total** from other stats.

In other words: total decreases below 10 must be **at least 2×** total increases above 10.

```bash
python tools/char_builder.py --skin <skin> --name "Name" \
  --set MSC=12 --set REF=8 --set SYS=8 --set HAR=10 --set RES=10
```

Use campaign mode to write directly into campaigns/<slug>/state/characters/:

```bash
python tools/char_builder.py --campaign <slug> --name "Name" --set STAT1=12 --set STAT2=10 --set STAT3=8 --set STAT4=9 --set STAT5=11
```

## Notes
- The builder enforces the Sinew & Steel point-buy rule (range 6–16 + double-debit validation).
- Use `--strict` to require exact payment (no extra decreases beyond the minimum).
- Use `--delta STAT=+2` to adjust from baseline 10, then `--set` to override.
