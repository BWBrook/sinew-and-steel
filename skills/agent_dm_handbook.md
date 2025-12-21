---
name: agent-dm-handbook
description: End-to-end guide for running a Sinew & Steel game with the repo and tools.
---

# Agent DM Handbook

This guide explains how to run a full Sinew & Steel session using the repo, tools, and state files.
It is written for Codex/Claude-Code style agents and keeps private GM data separate from public play.

## Philosophy
- Keep rules, skin, and prompt assembly deterministic and auditable.
- Store private notes and trackers locally (never show them unless asked).
- Use the CLI tools for rolls and state updates to avoid mistakes.

## Repo map (agent view)
- rules/: core system (adventurers_manual + custodians_almanac)
- skins/: setting overlays
- prompts/: prompt templates
- skills/: repeatable workflows (including this guide)
- tools/: CLI helpers
- state/: private runtime data (repo-level)
- campaigns/: per-campaign workspaces (untracked)

## Recommended workflow (campaign mode)

### 1) Initialize a campaign
```bash
python tools/campaign_init.py --name <slug> --skin <skin> --random-character "Name"
```
This creates:
- campaigns/<slug>/campaign.yaml
- campaigns/<slug>/state/{characters,trackers,memory,logs}/

### 2) Build the full prompt
```bash
python tools/build_prompt.py --campaign <slug>
```
This writes campaigns/<slug>/prompt.md using the campaign skin.

### 3) Start play
- Use prompt.md to seed the model.
- Keep public narration in the conversation.
- Keep private notes in campaigns/<slug>/state/memory/.

### 4) Resolve actions
- Roll dice with tools/roll.py.
- Apply outcomes using tools/update_sheet.py, tools/trackers.py, or tools/apply_roll.py.

Examples:
```bash
python tools/roll.py check --stat 12 --adv > /tmp/roll.json
python tools/apply_roll.py --roll /tmp/roll.json \
  --sheet campaigns/<slug>/state/characters/hero.yaml \
  --success-sheet-inc pools.stamina.current=-1
```

### 5) Capture memory and logs
- Memory: use tools/recap.py after each beat or scene.
- Logs: use tools/session_log.py to append public narration or roll results.

Examples:
```bash
python tools/recap.py --campaign <slug> \
  --summary "Beat 1: the bridge collapses" --pressure-inc 1 --scene-inc 1

python tools/session_log.py --campaign <slug> --role GM \
  --text "The bridge sways, ropes snapping in the storm."
```

## Public vs private
- Public: scene narration, options, roll results shown to the player.
- Private: GM notes, hidden motives, clocks, consequences.

## Skin toggles
- The manifest stores per-skin attributes, luck naming, and pressure track names.
- Campaign initialization uses the skin to label trackers and sheets automatically.

## When to update state
- After every roll: update sheet and tracker immediately.
- After every beat: add a memory recap.
- At session end: summarize unresolved threads.

## Troubleshooting
- Run `python tools/validate_repo.py` if tools or paths break.
- Use `tools/build_prompt.py --list-skins` to verify skin slugs.
- If a campaign is missing, re-run campaign_init.

## Optional: repo-level state
If you are not using campaigns/, you can store data in state/ at repo root.
The tools work the same way; just point them to state/ paths.
