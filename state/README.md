# State (Local Runtime Data)

This folder is for private, runtime state used by AI agents running a session.
Keep it local; do not share these files with players unless you intend spoilers.

Suggested layout:
- state/characters/ : YAML character sheets
- state/trackers/   : pressure, clocks, scene counters
- state/memory/     : private notes and summaries
- state/logs/       : session transcripts (private)

Seed files:
- state/characters/seed_character.yaml
- state/trackers/seed_tracker.yaml
- state/memory/seed_memory.yaml

Use tools/update_sheet.py and tools/trackers.py for consistent edits.
