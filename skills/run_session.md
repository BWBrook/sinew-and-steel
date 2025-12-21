---
name: run-session
description: Run a live Sinew & Steel session while updating state and trackers.
---

# Run Session

## Goal
Run a branching RPG session with clear separation between public narration and private GM notes.

## Setup
1. Pick a skin from manifest.yaml.
2. Create a character sheet in state/characters/ from templates/character_sheet.yaml.
3. (Optional) Generate a hidden scenario and save notes in state/memory/.
4. Build a full prompt using tools/build_prompt.py.

## During play
- Write public narration and choices only to the player.
- Record private notes and tracker changes in state/.
- Roll dice with tools/roll.py and update sheets with tools/update_sheet.py.
- Advance pressure tracks and clocks when fiction demands (tools/trackers.py).

## End of session
- Write a short memory summary in state/memory/.
- Capture unresolved threads in state/trackers/ or state/memory/.
