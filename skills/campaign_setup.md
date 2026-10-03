---
name: campaign-setup
description: Create a private campaign with skin-specific Pressure and resource state.
---

# Campaign Setup

Choose a skin from `manifest.yaml`, then preview the entire scaffold:

```bash
uv run python tools/campaign_init.py --slug scratch_demo --title "Scratch Demo" --skin clanfire \
  --tone standard --random-character Grak --seed 42 --dry-run --json
```

Remove `--dry-run` to create the reviewed campaign. Repeat `--random-character`
for a party, or omit it and add characters later with `char_builder.py` or
`gen_character.py --campaign scratch_demo`. Add characters before the first
logged action, or after `play.py session-close` and before the next `session`,
never mid-session. Both builders register the character's
Pressure and limited-use resources and refuse to overwrite an existing sheet. In
the same window, `play.py --character NAME retire --reason ...` takes a dead or
departed character out of play and keeps their sheet under `state/characters/retired/`.
Use `--tag NAME` for bought tags and `--free-tag GRANT=NAME` for a skin's free grant.

```bash
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/validate_campaign.py --campaign scratch_demo
```

Campaigns are untracked under `campaigns/`. Sheets hold Luck and Stamina;
`state/trackers/session.yaml` holds Pressure, resources, and other clocks.
Whispers receives one Insanity track per investigator; other current skins use a
party track. `--force` on initialization only fills missing files, preserving
existing state. It is not a migration or reset command.

For old campaigns, use the explicit preview and history decisions in
[the migration workflow](../docs/ai_play_harness.md#resume-and-legacy-state).
