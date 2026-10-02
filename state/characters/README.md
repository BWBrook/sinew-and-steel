# Characters (Seed Fixture)

`seed_character.yaml` shows the sheet format. A campaign's sheets live in
`campaigns/<slug>/state/characters/`; create them with
`campaign_init.py --random-character`, `char_builder.py --campaign`, or
`gen_character.py --campaign`, which also register the character's Pressure and
resources. `templates/character_sheet.yaml` is for standalone `--file` sheets only.
