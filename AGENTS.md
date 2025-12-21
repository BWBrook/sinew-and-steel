# Agent Harness Instructions (Sinew & Steel)

This repo is structured for AI coding agents (Codex CLI, Claude Code, Jules) to run RPG sessions.
Use the files and tools below to keep play consistent, reproducible, and private.

## Sources of truth
- manifest.yaml: canonical index of rules, skins, prompts, and templates.
- rules/: core system docs.
- skins/: setting overlays.
- prompts/: prompt templates.
- tools/: local CLI helpers (no API adapters).
- skills/: step-by-step agent workflows.
- state/: private runtime data (character sheets, trackers, memory).

## Operating rules
- Keep private notes in state/. Do not reveal them to players unless explicitly requested.
- Use tools/roll.py for dice and tools/update_sheet.py for sheet changes.
- Record each roll result and consequence in state/memory/ or state/logs/.
- Separate public narration from private tracking.
- Prefer manifest.yaml for paths instead of hardcoding.

## Recommended session flow
1. Choose a skin from manifest.yaml.
2. Create a character sheet in state/characters/ (start from templates/character_sheet.yaml).
3. (Optional) Create hidden scenario notes in state/memory/.
4. Build a full prompt with tools/build_prompt.py.
5. Run play: narrate publicly, track privately, roll via tools/roll.py.
6. Update sheets/tracks immediately after each outcome.
7. Close with a short memory summary and unresolved threads.

## Private vs public
- Public: scene text, choices, roll outcomes (as shown to players).
- Private: clocks, secret motives, hidden scenario notes, GM-only consequences.

## Skills
Use the skills in skills/ for repeatable workflows:
- skills/build_prompt.md
- skills/dice_resolution.md
- skills/manage_state.md
- skills/run_session.md
