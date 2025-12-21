---
name: dice-resolution
description: Roll checks and opposed tests using tools/roll.py and record results.
---

# Dice Resolution

## Goal
Resolve roll-under checks and opposed tests with reproducible, parseable output.

## Commands
Single check:

```bash
python tools/roll.py check --stat 12
python tools/roll.py check --stat 12 --adv
python tools/roll.py check --stat 12 --dis
```

Apply roll to state (example):

```bash
python tools/apply_roll.py --campaign <slug> --character <name> --roll /tmp/roll.json --success-sheet-inc pools.stamina.current=-1
```

Opposed check:

```bash
python tools/roll.py opposed --attacker 12 --defender 10
python tools/roll.py opposed --attacker 12 --defender 10 --adv-attacker
```

## Notes
- The output is JSON; record key results in state notes.
- Use `--seed` when you need deterministic replay.
- Natural 1 and 20 are flagged in the JSON as `crit`.
