# Tools

Local CLI helpers intended for Codex/Claude Code agents (and humans).
Requires Python 3 and PyYAML (already present in most agent runtimes).

- build_prompt.py: assemble a full prompt from rules + skin + optional hidden notes.
- new_skin.py: create a skin from templates and optionally register it in the manifest.
- roll.py: d20 rolls for checks and opposed tests.
- trackers.py: update scene counters and clocks (pressure, threat, etc).
- update_sheet.py: update YAML sheets and trackers by path.
- validate_repo.py: sanity checks for manifest and file layout.

Examples:

```bash
python tools/build_prompt.py --list-skins
python tools/build_prompt.py --skin clanfire --out /tmp/ss_prompt.md
python tools/new_skin.py --slug skyfarer
python tools/roll.py check --stat 12 --adv
python tools/trackers.py --file state/trackers/session.yaml scene --inc 1
python tools/trackers.py --file state/trackers/session.yaml pressure --inc 1 --clamp
python tools/update_sheet.py --file state/characters/grak.yaml --inc pools.luck.current=-1
python tools/validate_repo.py
```
