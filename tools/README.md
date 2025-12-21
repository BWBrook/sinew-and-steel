# Tools

Local CLI helpers intended for Codex/Claude Code agents (and humans).
Requires Python 3 and PyYAML (already present in most agent runtimes).

- build_prompt.py: assemble a full prompt from rules + skin + optional hidden notes.
- campaign_init.py: create a per-campaign state scaffold (untracked).
- char_builder.py: build a character sheet with point-buy validation.
- gen_character.py: generate a random character sheet for a skin.
- new_skin.py: create a skin from templates and optionally register it in the manifest.
- roll.py: d20 rolls for checks and opposed tests.
- apply_roll.py: apply roll results to sheets/trackers based on success/failure.
- recap.py: append a structured summary to memory and optionally advance clocks.
- session_log.py: append public narration or roll results to session logs.
- trackers.py: update scene counters and clocks (pressure, threat, etc).
- update_sheet.py: update YAML sheets and trackers by path.
- validate_repo.py: sanity checks for manifest and file layout.

Examples:

```bash
python tools/build_prompt.py --list-skins
python tools/build_prompt.py --skin clanfire --out /tmp/ss_prompt.md
python tools/build_prompt.py --campaign icehunt
python tools/campaign_init.py --name icehunt --skin clanfire --random-character \"Grak\"
python tools/char_builder.py --campaign icehunt --name \"Aveline\" --set HEW=6 --set FLT=8 --set LOR=10 --set MCY=13 --set PRV=10
python tools/gen_character.py --skin clanfire --name \"Tarra\" --out /tmp/tarra.yaml
python tools/new_skin.py --slug skyfarer
python tools/roll.py check --stat 12 --adv
python tools/recap.py --campaign icehunt --summary \"Beat 1: the blizzard\" --pressure-inc 1 --scene-inc 1
python tools/session_log.py --campaign icehunt --role GM --text \"The storm splits the ridge.\"
python tools/trackers.py --file state/trackers/session.yaml scene --inc 1
python tools/trackers.py --file state/trackers/session.yaml pressure --inc 1 --clamp
python tools/update_sheet.py --file state/characters/grak.yaml --inc pools.luck.current=-1
python tools/apply_roll.py --roll /tmp/roll.json --sheet state/characters/grak.yaml --success-sheet-inc pools.stamina.current=-1
python tools/validate_repo.py
```
