# Campaigns (Local Only)

This folder is for per-campaign runtime data and is not tracked by git.
Each campaign can have its own state, memory, and logs without affecting the repo.

Suggested layout per campaign:
- campaigns/<slug>/campaign.yaml
- campaigns/<slug>/state/characters/
- campaigns/<slug>/state/trackers/
- campaigns/<slug>/state/memory/
- campaigns/<slug>/state/logs/
- campaigns/<slug>/state/checkpoints/ (exact last GM text for save/quit, overwritten each time)

Use tools/campaign_init.py to create a campaign scaffold. Prefer a slug like `ice_hunt`, or pass `--title` to auto-slugify.
