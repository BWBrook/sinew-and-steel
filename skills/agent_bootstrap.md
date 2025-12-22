---
name: agent-bootstrap
description: Fast start or resume workflow for Codex/Claude Code using this repo.
---

# Agent Bootstrap

## Goal
Get a Codex/Claude Code agent to a playable state quickly, either by resuming a campaign or starting a new one.

## Resume a campaign (fastest)
Minimal read list:
- `AGENTS.md`
- `skills/agent_dm_handbook.md`

Then load campaign state:
- `campaigns/<slug>/campaign.yaml`
- `campaigns/<slug>/state/characters/*.yaml`
- `campaigns/<slug>/state/trackers/session.yaml`
- latest `campaigns/<slug>/state/memory/session_*.yaml`
- latest `campaigns/<slug>/state/logs/session_*.md`
- `campaigns/<slug>/state/checkpoints/last.md`

### One-shot resume pack
```bash
python tools/resume_pack.py --campaign <slug> --character <name>
```
This prints a compact snapshot (campaign + character + tracker + latest memory/log + checkpoint).
Add `--public` to redact private memory/secrets when you need a player-safe resume.

### Absolute minimum (checkpoint only)
If you can run only one tool, restore the last GM response directly:

```bash
python tools/checkpoint.py --campaign <slug> --show
```
This skips memory/logs entirely and is the fastest resume fallback.

### Example player directive (fresh Codex resume)
Use placeholders for the campaign and character:

```
You’re resuming a Sinew & Steel campaign. Read only AGENTS.md and skills/agent_dm_handbook.md.
Then run: python tools/resume_pack.py --campaign <campaign_slug> --character <character_slug>
Use that output for your internal context only (do not show memory/secrets/log to me).
If you have any questions, ask now. If not, print ONLY the checkpoint text and continue play from there.
```

## Start a new campaign (fastest)
```bash
python tools/build_prompt.py --list-skins
python tools/campaign_init.py --title "My Campaign" --skin <skin> --tone standard --random-character "Name"
python tools/build_prompt.py --campaign <slug> --mode agent
```
Then open `campaigns/<slug>/prompt.md` in your agent and begin Scene 1.

## Notes
- Keep rolls rare: uncertainty + stakes only.
- After each GM response, write a checkpoint with `tools/checkpoint.py`.
