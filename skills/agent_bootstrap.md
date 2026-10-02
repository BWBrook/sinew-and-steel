---
name: agent-bootstrap
description: Resume authoritative campaign state or initialize a new game with the current harness.
---

# Agent Bootstrap

Read `AGENTS.md` and [the Custodian handbook](agent_dm_handbook.md), then load state:

```bash
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/validate_campaign.py --campaign scratch_demo
uv run python tools/resume_pack.py --campaign scratch_demo
```

Any play action, checkpoint or advancement makes the saved prompt stale by design,
and `validate_campaign.py` treats a stale prompt as an error. Rebuild it first with
the same `--mode`, `--full` and `--hidden` options as before; the first line of
`prompt.md` records the mode, profile and sources of the last build, and notes saved
as `state/memory/hidden_scenario.md` are always included. `build_prompt.py --check
--json` reports staleness without writing.

The resume pack supplies sheets, tracker, latest private memory/log, and exact
checkpoint. `--character` filters it to one sheet, so omit it for a party. Check
whether a roll is pending; resume it with `play.py settle`, never a new roll.
Resolve a pending crisis before the next action.

For player output, use `resume_pack.py --public`. It exports selected character
and campaign fields plus the exact public checkpoint, with no raw clocks, logs,
private memory, arbitrary sheet fields, or paths. Read the private pack internally;
show the checkpoint and continue from that moment. A checkpoint alone can recover
the last wording, but does not replace checking mechanical state.

To start a new game:

```bash
uv run python tools/campaign_init.py --title "Scratch Demo" --skin clanfire \
  --tone standard --random-character Grak --seed 42
uv run python tools/build_prompt.py --campaign scratch_demo
```

Use `play.py` for mechanics and save the exact public response through
`checkpoint.py` after every Custodian turn. Old schemas require an explicit
migration preview and a known history; do not silently adopt a private campaign.
