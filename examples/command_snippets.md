# Command Snippets (Example)

Build a starter prompt for Clanfire:

```bash
python tools/build_prompt.py --skin clanfire --mode agent --out /tmp/ss_prompt.md
```

Initialize a campaign (recommended harness flow):

```bash
python tools/campaign_init.py --title "<campaign title>" --skin clanfire --tone standard --random-character "Grak"
python tools/build_prompt.py --campaign <slug>
python tools/validate_campaign.py --campaign <slug>
```

Run the “Emberfall” starter scenario module (Clanfire):

```bash
python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard
python tools/build_prompt.py --campaign emberfall --mode agent --hidden rules/scenarios/clanfire_emberfall_hidden.md
```

Roll a standard check:

```bash
python tools/roll.py check --stat 12
```

Update a sheet (spend 1 Luck):

```bash
python tools/update_sheet.py --campaign <slug> --character <name> --inc pools.luck.current=-1
```

Resume fast (agent context):

```bash
python tools/resume_pack.py --campaign <slug> --character <name>
python tools/resume_pack.py --campaign <slug> --character <name> --public
```

Save and restore the last GM response:

```bash
cat /tmp/last_gm.md | python tools/checkpoint.py --campaign <slug>
python tools/checkpoint.py --campaign <slug> --show
```

Start a new paired session (memory + log):

```bash
python tools/new_session.py --campaign <slug>
```
