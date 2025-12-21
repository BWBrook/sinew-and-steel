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
Provide stats explicitly (sum must be 50, each stat 6–16):

```bash
python tools/char_builder.py --skin <skin> --name "Name" \
  --set STAT1=12 --set STAT2=10 --set STAT3=8 --set STAT4=9 --set STAT5=11
```

Use campaign mode to write directly into campaigns/<slug>/state/characters/:

```bash
python tools/char_builder.py --campaign <slug> --name "Name" --set STAT1=12 --set STAT2=10 --set STAT3=8 --set STAT4=9 --set STAT5=11
```

## Notes
- The builder enforces the Sinew & Steel point-buy rule (sum 50, range 6–16).
- Use --delta STAT=+2 to adjust from baseline 10, then --set to override.
