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
