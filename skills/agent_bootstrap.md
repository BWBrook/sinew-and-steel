---
name: agent-bootstrap
description: Resume authoritative campaign state or initialize a new game with the current harness.
---

# Agent Bootstrap

Read `AGENTS.md` and [the Custodian handbook](agent_dm_handbook.md), then load state:

```bash
uv run python tools/validate_campaign.py --campaign ice_hunt
uv run python tools/resume_pack.py --campaign ice_hunt --character grak
uv run python tools/build_prompt.py --campaign ice_hunt --check --json
```

The resume pack supplies sheets, tracker, latest private memory/log, and exact
checkpoint. Check whether a roll is pending; resume it with `play.py settle`,
never a new roll. Resolve a pending crisis before the next action. A stale prompt
should be rebuilt from current sources.

For player output, use `resume_pack.py --public`. It exports selected character
and campaign fields plus the exact public checkpoint, with no raw clocks, logs,
private memory, arbitrary sheet fields, or paths. Read the private pack internally;
show the checkpoint and continue from that moment. A checkpoint alone can recover
the last wording, but does not replace checking mechanical state.

To start a new game:

```bash
uv run python tools/campaign_init.py --title "Ice Hunt" --skin clanfire \
  --tone standard --random-character Grak --seed 42
uv run python tools/build_prompt.py --campaign ice_hunt
```

Use `play.py` for mechanics and save the exact public response through
`checkpoint.py` after every Custodian turn. Old schemas require an explicit
migration preview and a known history; do not silently adopt a private campaign.
