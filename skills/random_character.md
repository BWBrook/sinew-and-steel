---
name: random-character
description: Generate a random character sheet that obeys Sinew & Steel build rules.
---

# Random Character

## Goal
Create a legal random sheet (stats 6–16) with skin-specific labels, generated using the double-debit method.

## Command
```bash
python tools/gen_character.py --skin <skin> --name "Name" --out state/characters/name.yaml
```

## Notes
- The generator uses manifest.yaml for attribute labels and luck naming.
- Use --seed for reproducible generation.
