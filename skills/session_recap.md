---
name: session-recap
description: Distill a session into private memory notes, open threads, and tracker updates.
---

# Session Recap

## Goal
Create a concise, private summary after each session beat or milestone, then update trackers and sheets.

## Recap format (YAML)
Use state/memory/seed_memory.yaml as the base.
Populate:
- summary: 3-6 sentences, focusing on outcomes and new facts.
- threads: unresolved hooks or decisions.
- npcs: new NPCs or status changes.
- secrets: GM-only reveals or hidden motives.

## Checklist
1. Write a summary entry in state/memory/ (tools/recap.py can do this).
2. Update pressure or threat clocks (tools/recap.py or tools/trackers.py).
3. Update character sheets for spent Luck, damage, or new items.
4. Note any milestone boons or build points awarded.

## Commands
```bash
python tools/trackers.py --file state/trackers/session.yaml pressure --inc 1 --clamp
python tools/update_sheet.py --file state/characters/<name>.yaml --inc pools.luck.current=-1
python tools/recap.py --campaign <slug> --summary "Beat recap" --pressure-inc 1 --scene-inc 1
```
