---
name: random-character
description: Generate a random character sheet that obeys Sinew & Steel build rules.
---

# Random Character

## Goal
Create a legal random sheet with skin-specific labels, generated using:
- a double-debit “specialization” pass, then
- spending a build points budget (default 6) to improve scores.

## Command
```bash
uv run python tools/gen_character.py --skin <skin> --name "Name" --out state/characters/name.yaml
```

## Notes
- The generator uses manifest.yaml for attribute labels and luck naming.
- Per-skin generator defaults live under manifest `skins.<slug>._gen` (override with `--primary`, `--min-steps`, `--max-steps`).
- Use --seed for reproducible generation.
- Use `--tone grim|standard|pulp|heroic` (or `--build-points N`) to control starting power.
- Generated sheets carry no tags. Add one by hand under `tags:` (2 build points each) and rerun `uv run python tools/recalc_sheet.py`, or build with `char_builder.py --tag`.
