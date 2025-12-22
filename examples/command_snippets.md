# Command Snippets (Example)

Build a starter prompt for Clanfire:

```bash
python tools/build_prompt.py --skin clanfire --mode agent --out /tmp/ss_prompt.md
```

Roll a standard check:

```bash
python tools/roll.py check --stat 12
```

Update a sheet (spend 1 Luck):

```bash
python tools/update_sheet.py --file state/characters/grak.yaml --inc pools.luck.current=-1
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
