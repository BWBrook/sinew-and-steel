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
Provide scores explicitly (attributes 6–16; `STA` 3–9) following the **build points** economy.

Baselines:
- Attributes baseline at **10**.
- Stamina baseline at **5** (treat as `STA`).

Costs:
- **+1 above baseline costs 2 build points.**
- **+1 below baseline costs 1 build point** (so **2 build points** can restore **+2** below baseline).

Default starting budget is **6 build points** (“standard”), but you can run:
- `--tone grim` (0), `--tone standard` (6), `--tone pulp` (12), `--tone heroic` (16)
- or `--build-points N` for an explicit budget.

```bash
python tools/char_builder.py --skin <skin> --name "Name" \
  --set MSC=12 --set REF=8 --set SYS=8 --set HAR=10 --set RES=10
```

Example that trades Stamina down to pay for a spike:

```bash
python tools/char_builder.py --skin <skin> --name "Name" \
  --set MSC=10 --set REF=10 --set SYS=14 --set HAR=10 --set RES=7 --set STA=3
```

Example using a heroic budget to raise the floor while still specializing:

```bash
python tools/char_builder.py --skin <skin> --tone heroic --name "Name" \
  --set MSC=13 --set REF=10 --set SYS=10 --set HAR=10 --set RES=10 --set STA=6
```

Use campaign mode to write directly into campaigns/<slug>/state/characters/:

```bash
python tools/char_builder.py --campaign <slug> --name "Name" --set STAT1=12 --set STAT2=10 --set STAT3=8 --set STAT4=9 --set STAT5=11
```

## Notes
- The builder enforces the Sinew & Steel creation rules:
  - Ranges: attributes 6–16, `STA` 3–9.
  - Build points budget (default 6, or campaign.yaml `build_points_budget` in campaign mode).
- Stamina participates in the same economy, but uses a baseline of **5**.
- Use `--strict` to disallow extra decreases (voluntary weakness below baseline).
- Use `--delta STAT=+2` to adjust from baseline (10 for attributes; 5 for `STA`), then `--set` to override.
