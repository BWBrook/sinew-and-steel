# Tools

Local CLI helpers intended for Codex/Claude Code agents (and humans).
Requires Python 3 and PyYAML (already present in most agent runtimes).

- build_prompt.py: assemble a full prompt from rules + skin + optional hidden notes.
- campaign_init.py: create a per-campaign state scaffold (untracked).
- char_builder.py: build a character sheet with point-buy validation.
- gen_character.py: generate a random character sheet for a skin (includes build points by default).
- recalc_sheet.py: recompute build_points_used on a sheet after manual edits.
- new_skin.py: create a skin from templates and optionally register it in the manifest.
- roll.py: d20 rolls for checks and opposed tests.
- beat.py: roll + (optional) nudge + state updates + log/recap in one command.
- apply_roll.py: apply roll results to sheets/trackers based on success/failure.
- doctor.py: run repo/campaign diagnostics in one command.
- recap.py: append a structured summary to memory and optionally advance clocks.
- session_log.py: append public narration or roll results to session logs.
- checkpoint.py: save exact last GM text for “save and quit” (separate from logs/memory).
- resume_pack.py: print a compact resume snapshot (campaign + character + memory + log + checkpoint).
- new_session.py: create paired session memory/log files together to avoid drift.
- summary.py: one-screen campaign snapshot (scene, clocks, sheet, last memory).
- trackers.py: update scene counters and clocks (pressure, threat, etc).
- update_sheet.py: update YAML sheets and trackers by path.
- validate_sheet.py: validate a character sheet against point-buy + manifest.
- validate_campaign.py: validate a campaign scaffold and its state.
- validate_repo.py: sanity checks for manifest and file layout.
- release_build.py: build release bundles (markdown + optional PDFs via pandoc) into release/dist/.
- md_pdf.py: build an ad-hoc PDF from arbitrary markdown file(s) for layout/art iteration.
- ss.py: thin dispatcher (`python tools/ss.py <command> ...`) for single-command workflows.

Note: state mutation tools are strict by default; use `--allow-new` only when you intend to create new keys.
Most mutators also accept `--dry-run` (no writes) and `--json` (machine-readable summary).
For tools with subcommands (roll/beat/trackers), global flags can appear before or after the subcommand.
Random generation reads optional per-skin `_gen` defaults from manifest.yaml (override with CLI flags).

Examples:

```bash
python tools/build_prompt.py --list-skins
python tools/build_prompt.py --skin clanfire --mode agent --out /tmp/ss_prompt.md
python tools/build_prompt.py --skin clanfire --mode chat --out /tmp/ss_prompt_chat.md
python tools/build_prompt.py --campaign ice_hunt --mode agent
python tools/campaign_init.py --title \"Ice Hunt\" --skin clanfire --tone standard --random-character \"Grak\"
python tools/char_builder.py --campaign ice_hunt --name \"Aveline\" --set HEW=6 --set FLT=8 --set LOR=10 --set MCY=13 --set PRV=10
python tools/gen_character.py --skin clanfire --tone standard --name \"Tarra\" --out /tmp/tarra.yaml
python tools/new_skin.py --slug skyfarer
python tools/roll.py check --stat 12 --adv --pretty
python tools/beat.py --campaign ice_hunt --character grak --log check --stat-key SYS --adv --nudge -1
python tools/recap.py --campaign ice_hunt --summary \"Beat 1: the blizzard\" --pressure-inc 1 --scene-inc 1
python tools/session_log.py --campaign ice_hunt --role GM --text \"The storm splits the ridge.\"
python tools/summary.py --campaign ice_hunt
python tools/new_session.py --campaign ice_hunt
python tools/trackers.py --campaign ice_hunt scene --inc 1
python tools/trackers.py --campaign ice_hunt pressure --inc 1 --clamp
python tools/update_sheet.py --campaign ice_hunt --character grak --inc pools.luck.current=-1
python tools/apply_roll.py --campaign ice_hunt --character grak --roll /tmp/roll.json --success-sheet-inc pools.stamina.current=-1
python tools/recalc_sheet.py --campaign ice_hunt --character grak
python tools/validate_sheet.py --campaign ice_hunt --character grak
python tools/validate_campaign.py --campaign ice_hunt
python tools/validate_repo.py
python tools/doctor.py --campaign ice_hunt
python tools/ss.py beat --campaign ice_hunt --character grak check --stat-key SYS
python tools/checkpoint.py --campaign ice_hunt --show
python tools/resume_pack.py --campaign ice_hunt --character grak
python tools/resume_pack.py --campaign ice_hunt --character grak --public
python tools/md_pdf.py rules/quickstart.md --out /tmp/quickstart.pdf --style bookish
python tools/md_pdf.py rules/quickstart.md skins/clanfire.md --out /tmp/layout_test.pdf --toc --style bookish
python tools/md_pdf.py --files \"rules/quickstart.md skins/clanfire.md\" --out /tmp/layout_test.pdf --toc --style bookish

# Save and quit (ironman): store exactly one checkpoint per campaign (overwritten each time).
# Prefer stdin or --text-file for multi-line messages.
cat /tmp/last_gm.md | python tools/checkpoint.py --campaign ice_hunt
python tools/checkpoint.py --campaign ice_hunt --show
```
