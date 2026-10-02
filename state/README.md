# State (Seed Fixtures)

This folder holds seed files that show the formats; it holds no live campaign
data. Each campaign keeps its own private state under `campaigns/<slug>/state/`.
Keep that state local; do not share it with players unless you intend spoilers.

Layout of a campaign's state directory:
- characters/  : YAML character sheets
- trackers/    : Pressure, resources, clocks, scene counters
- memory/      : private notes and summaries, one file per session
- logs/        : public session log and the engine's structured events
- checkpoints/ : the exact last public response

Seed files:
- state/characters/seed_character.yaml
- state/trackers/seed_tracker.yaml
- state/memory/seed_memory.yaml

Use `tools/play.py` for mechanical changes and `tools/advance.py` for milestones
and spending. `tools/update_sheet.py` edits descriptive fields only. Campaign
creation supplies the selected skin's Pressure and resource structures; the
seed files illustrate the formats and do not supply a complete party roster.
