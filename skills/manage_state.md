---
name: manage-state
description: Maintain private notes, trackers, and character sheets in state/.
---

# Manage State

## Goal
Keep durable, private session data for the agent: sheets, trackers, memory, and logs.

## Recommended layout
- state/characters/ : YAML character sheets
- state/trackers/   : pressure clocks, scene counters
- state/memory/     : private notes and summaries
- state/logs/       : full session logs (private)

## Updating sheets
Use the updater for consistent changes:

```bash
python tools/update_sheet.py --file state/characters/<name>.yaml --inc pools.luck.current=-1
python tools/update_sheet.py --file state/characters/<name>.yaml --set tracks.pressure.current=2
```

## Notes
- Treat state/ as private. Do not reveal it to players unless you intend spoilers.
- Summarize every scene or milestone in memory notes.
- Keep pressure tracks and clocks in trackers for fast retrieval.
