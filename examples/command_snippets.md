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

Run the “Emberfall” starter scenario module (Clanfire) in a throwaway campaign. The module's default PCs are Grak and Tarra, so build them at the standard budget, save the module as the campaign's hidden scenario (every rebuild includes it automatically), then build and validate the prompt:

```bash
uv run python tools/campaign_init.py --title "Scratch Demo" --skin clanfire --tone standard
uv run python tools/char_builder.py --campaign scratch_demo --name Grak \
  --set MGT=12 --set SPR=8 --set INS=8 --set STM=7 --tag "Megafauna tracker"
uv run python tools/char_builder.py --campaign scratch_demo --name Tarra \
  --set MGT=6 --set FLT=8 --set CUN=12 --set SPR=14 --set INS=11 --set STM=3
uv run python tools/update_sheet.py --campaign scratch_demo --character grak \
  --append 'inventory.big_items=["Stone spear (+1, thrown or thrust)", "Hand-axe (+1)", "Hide cloak (soak 1)"]' \
  --append 'inventory.small_items=["Ochre pouch (ritual mark)", "Sinew cord"]'
uv run python tools/update_sheet.py --campaign scratch_demo --character tarra \
  --append 'inventory.big_items=["Fire-bow drill"]' \
  --append 'inventory.small_items=["Carved bone flute (Advantage when calming beasts)", "Herb bundle", "Scrap of strange cloth from southern strangers"]'
cp rules/scenarios/clanfire_emberfall_hidden.md campaigns/scratch_demo/state/memory/hidden_scenario.md
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/validate_campaign.py --campaign scratch_demo
```

Roll a standard check:

```bash
uv run python tools/roll.py check --stat 12
```

Record an adjudicated Luck cost (`--character` takes the sheet's file stem, such as `grak`):

```bash
uv run python tools/play.py --campaign <slug> --character <character_slug> luck --amount -1 --source "Declared ability cost"
```

Resume fast (agent context). Any play action, checkpoint or advancement makes the saved prompt stale by design, so rebuild it first with the same options. `--character <character_slug>` filters the pack to one sheet; omit it for a party:

```bash
uv run python tools/build_prompt.py --campaign <slug>
uv run python tools/resume_pack.py --campaign <slug>
uv run python tools/resume_pack.py --campaign <slug> --public
```

Save and restore the last GM response:

```bash
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign <slug>
uv run python tools/checkpoint.py --campaign <slug> --show
```

Award any milestones with `advance.py` first; it refuses once the session is closed. Then close the completed session and start its successor (memory, prose log and telemetry):

```bash
uv run python tools/play.py --campaign <slug> session-close --label "Session complete"
uv run python tools/new_session.py --campaign <slug>
```
