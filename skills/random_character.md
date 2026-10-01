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
- Per-skin generator defaults live under manifest `skins.<slug>._gen` (override with `--primary`, `--min-steps`, `--max-steps`). Each double-debit step lowers 2 points, so at most 4 steps fit the 8-point refund cap; the generator refuses more.
- Use --seed for reproducible generation.
- Use `--tone grim|standard|pulp|heroic` (or `--build-points N`) to control starting power.
- Add tags with `--tag "Name"` (repeatable). Each reserves 2 build points before scores are bought; the sheet lists them under `tags:`.
