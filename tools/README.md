# Tools

Local CLI helpers intended for Codex/Claude Code agents (and humans).
Requires Python 3 and PyYAML (already present in most agent runtimes).

- build_prompt.py: assemble a full prompt from rules + skin + optional hidden notes.
- campaign_init.py: create a per-campaign state scaffold (untracked).
- char_builder.py: build a character sheet with point-buy validation.
- gen_character.py: generate a random character sheet for a skin (spends the build-point budget on scores; it never buys tags, so add those with char_builder.py --tag or by hand and rerun recalc_sheet.py).
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
- release_build.py: build release bundles (Markdown + optional PDFs via pandoc + WeasyPrint) into release/dist/.
- md_pdf.py: build an ad-hoc PDF from arbitrary markdown file(s) for layout/art iteration.
- layout_lab.py: render the fixtures in examples/layout_lab/ to PDFs (and optional PNGs) for wrap and pagination checks.
- delvekit_seed.py: generate a deterministic Candlelight Delvekit dungeon prototype as YAML and optional markdown/maps.
- delvekit_map.py: render hidden GM maps and progressively revealed player maps from Delvekit YAML.
- delvekit_pitch.py: prepare a Codex-facing pitch-polish prompt bundle and apply polished title/blurb text back into Delvekit YAML.
- delvekit_adventure.py: prepare a Codex-facing adventure-polish bundle and write the finished module markdown.
- ss.py: thin dispatcher (`uv run python tools/ss.py <command> ...`) for single-command workflows.

For PDF building (including wrapped inline images), see `docs/pdf_building.md`.

Note: state mutation tools are strict by default; use `--allow-new` only when you intend to create new keys.
Most mutators also accept `--dry-run` (no writes) and `--json` (machine-readable summary).
For tools with subcommands (roll/beat/trackers), global flags can appear before or after the subcommand.
Random generation reads optional per-skin `_gen` defaults from manifest.yaml (override with CLI flags).

Manifest-defined addons:
- `build_prompt.py` embeds any addon files listed under a skin in `manifest.yaml`.
- Today that means `uv run python tools/build_prompt.py --skin candlelight_dungeons ...` includes `skins/candlelight_delvekit.md` automatically.

Examples:

```bash
uv run python tools/build_prompt.py --list-skins
uv run python tools/build_prompt.py --skin clanfire --mode agent --out /tmp/ss_prompt.md
# Note: build_prompt strips artwork image tags by default (for LLM prompt cleanliness).
# Use --keep-art if you explicitly want the `![](...){...}` artwork markers included.
uv run python tools/build_prompt.py --skin clanfire --mode chat --out /tmp/ss_prompt_chat.md
uv run python tools/build_prompt.py --skin candlelight_dungeons --mode agent --out /tmp/candlelight_prompt.md
uv run python tools/build_prompt.py --campaign ice_hunt --mode agent
uv run python tools/campaign_init.py --title "Ice Hunt" --skin clanfire --tone standard --random-character "Grak"
uv run python tools/char_builder.py --campaign ice_hunt --name "Grak" --set MGT=12 --set SPR=8 --set INS=8 --set STM=7 --tag "Megafauna tracker"
uv run python tools/gen_character.py --skin clanfire --tone standard --name "Tarra" --out /tmp/tarra.yaml
uv run python tools/new_skin.py --slug skyfarer   # writes skins/skyfarer.md and edits manifest.yaml
uv run python tools/roll.py check --stat 12 --adv --pretty
uv run python tools/beat.py --campaign ice_hunt --character grak --log check --stat-key MGT --adv --nudge -1
uv run python tools/recap.py --campaign ice_hunt --summary "Beat 1: the blizzard" --pressure-inc 1 --scene-inc 1
uv run python tools/session_log.py --campaign ice_hunt --role GM --text "The storm splits the ridge."
uv run python tools/summary.py --campaign ice_hunt
uv run python tools/new_session.py --campaign ice_hunt
uv run python tools/trackers.py --campaign ice_hunt scene --inc 1
uv run python tools/trackers.py --campaign ice_hunt pressure --inc 1 --clamp
uv run python tools/update_sheet.py --campaign ice_hunt --character grak --inc pools.luck.current=-1
uv run python tools/apply_roll.py --campaign ice_hunt --character grak --roll /tmp/roll.json --success-sheet-inc pools.stamina.current=-1
uv run python tools/recalc_sheet.py --campaign ice_hunt --character grak
uv run python tools/validate_sheet.py --campaign ice_hunt --character grak
uv run python tools/validate_campaign.py --campaign ice_hunt
uv run python tools/validate_repo.py
uv run python tools/doctor.py --campaign ice_hunt
uv run python tools/ss.py beat --campaign ice_hunt --character grak check --stat-key MGT
uv run python tools/checkpoint.py --campaign ice_hunt --show
uv run python tools/resume_pack.py --campaign ice_hunt --character grak
uv run python tools/resume_pack.py --campaign ice_hunt --character grak --public
uv run python tools/delvekit_seed.py --seed 42 --size tiny --difficulty hard --out /tmp/delve.yaml
uv run python tools/delvekit_map.py --file /tmp/delve.yaml --mode gm
uv run python tools/delvekit_seed.py --seed 42 --size medium --difficulty medium --out /tmp/delve.yaml --pitch-prompt-out /tmp/delve_pitch.md
uv run python tools/delvekit_seed.py --seed 42 --size medium --difficulty medium --out /tmp/delve.yaml --adventure-prompt-out /tmp/delve_adventure.md
uv run python tools/delvekit_pitch.py prepare --file /tmp/delve.yaml --out /tmp/delve_pitch.md --json-out /tmp/delve_pitch.json
uv run python tools/delvekit_pitch.py apply --file /tmp/delve.yaml --text-file /tmp/polished_pitch.txt --echo
uv run python tools/delvekit_adventure.py prepare --file /tmp/delve.yaml --out /tmp/delve_adventure.md --json-out /tmp/delve_adventure.json
uv run python tools/delvekit_adventure.py apply --out /tmp/delve_module.md --markdown-file /tmp/polished_module.md
uv run python tools/delvekit_map.py --file examples/candlelight_delvekit/pale_warrens.yaml --mode player --frontier --reveal-rooms 3,4 --position 4
uv run --extra pdf python tools/md_pdf.py rules/quickstart.md --out /tmp/quickstart.pdf --style bookish
uv run --extra pdf python tools/md_pdf.py rules/quickstart.md skins/clanfire.md --out /tmp/layout_test.pdf --toc --style bookish
uv run --extra pdf python tools/md_pdf.py --files "rules/quickstart.md skins/clanfire.md" --out /tmp/layout_test.pdf --toc --style bookish

# Save and quit (ironman): store exactly one checkpoint per campaign (overwritten each time).
# Prefer stdin or --text-file for multi-line messages.
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign ice_hunt
uv run python tools/checkpoint.py --campaign ice_hunt --show
```
