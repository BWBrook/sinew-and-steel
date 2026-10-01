# Command Snippets (Example)

Build a starter prompt for Clanfire:

```bash
uv run python tools/build_prompt.py --skin clanfire --mode agent --out /tmp/ss_prompt.md
```

Initialize a campaign (recommended harness flow):

```bash
uv run python tools/campaign_init.py --title "<campaign title>" --skin clanfire --tone standard --random-character "Grak"
uv run python tools/build_prompt.py --campaign <slug>
uv run python tools/validate_campaign.py --campaign <slug>
```

Run the “Emberfall” starter scenario module (Clanfire):

```bash
uv run python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard
uv run python tools/build_prompt.py --campaign emberfall --mode agent --hidden rules/scenarios/clanfire_emberfall_hidden.md
```

Roll a standard check:

```bash
uv run python tools/roll.py check --stat 12
```

Record an adjudicated Luck cost:

```bash
uv run python tools/play.py --campaign <slug> --character <name> luck --amount -1 --source "Declared ability cost"
```

Resume fast (agent context):

```bash
uv run python tools/resume_pack.py --campaign <slug> --character <name>
uv run python tools/resume_pack.py --campaign <slug> --character <name> --public
```

Save and restore the last GM response:

```bash
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign <slug>
uv run python tools/checkpoint.py --campaign <slug> --show
```

Close the completed session, then start its successor (memory, prose log and telemetry):

```bash
uv run python tools/play.py --campaign <slug> session-close --label "Session complete"
uv run python tools/new_session.py --campaign <slug>
```
