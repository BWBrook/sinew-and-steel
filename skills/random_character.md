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
python tools/gen_character.py --skin <skin> --name "Name" --out state/characters/name.yaml
```

## Notes
- The generator uses manifest.yaml for attribute labels and luck naming.
- Per-skin generator defaults live under manifest `skins.<slug>._gen` (override with `--primary`, `--min-steps`, `--max-steps`).
- Use --seed for reproducible generation.
- Use `--tone grim|standard|pulp|heroic` (or `--build-points N`) to control starting power.
