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

## Updating sheets and trackers
Use the updater for consistent changes to character sheets, but keep **pressure** in trackers (campaign-wide clock).

```bash
python tools/update_sheet.py --campaign <slug> --character <name> --inc pools.luck.current=-1
```

For trackers and scene counters:

```bash
python tools/trackers.py --campaign <slug> scene --inc 1
python tools/trackers.py --campaign <slug> pressure --inc 1 --clamp
```

## Notes
- Treat state/ as private. Do not reveal it to players unless you intend spoilers.
- Summarize every scene or milestone in memory notes.
- Keep pressure tracks and clocks in trackers for fast retrieval.
- `update_sheet.py` is strict by default; use `--allow-new` only when you intend to add new keys.
