# Candlelight Delvekit

`Candlelight Delvekit` is an optional sidecar for `skins/candlelight_dungeons.md`.
It adds a lean exploration procedure, a small dungeon-state schema, generated example sites, and a few tiny Python tools:

- `tools/delvekit_seed.py` for deterministic prototype generation
- `tools/delvekit_map.py` for hidden and player-map rendering
- `tools/delvekit_pitch.py` for Codex-facing title/blurb polish workflow
- `tools/delvekit_adventure.py` for Codex-facing full adventure polish workflow

It does **not** replace Candlelight Dungeons, and it does **not** change core Sinew & Steel.

## What Is Included

- `skins/candlelight_delvekit.md` — optional rules sidecar
- `rules/appendices/candlelight_delvekit_quickref.md` — short referee quick reference
- `examples/candlelight_delvekit/pale_warrens.md` — generated proof dungeon
- `examples/candlelight_delvekit/pale_warrens.yaml` — matching generated dungeon state
- `templates/candlelight_delvekit_dungeon.yaml` — minimal dungeon-state template
- `tools/delvekit_seed.py` — seeded prototype generator
- `tools/delvekit_map.py` — ASCII GM/player map renderer
- `tools/delvekit_pitch.py` — prompt prep and apply helper for final player-facing hook copy
- `tools/delvekit_adventure.py` — prompt prep and apply helper for full module markdown

If you only read one example, use `examples/candlelight_delvekit/pale_warrens.md`.
If you only run one tool, start with `tools/delvekit_seed.py`.

### Example Convention

- `*.yaml` example files are raw generated Delvekit state.
- `*.md` example files are the human-readable module view of that state.
- In general, keep the YAML inspectable and let the Markdown be the polished reading copy.

## Philosophy

Delvekit stays lean on purpose.

- Keep the base game intact.
- Add procedure only where dungeon play benefits from it.
- Prefer YAML, Markdown, and simple deterministic scripts.
- Do not build a tactical combat game by accident.

The generator is intentionally small and table-like. It should create useful variation, not replace Custodian judgment.

## Get Running Fast

If you are using Codex, start with a prompt, not a shell script.

### Simplest First-Time Prompt

If someone has never used Codex before, give them this:

```text
Read these files first:
- skins/candlelight_dungeons.md
- skins/candlelight_delvekit.md
- rules/appendices/candlelight_delvekit_quickref.md

Then generate a random Candlelight Delvekit dungeon for us.
Make it:
- tiny size
- hard difficulty

After that:
1. show me only the player-facing title and blurb
2. wait for my approval
3. if I like it, use the underlying dungeon to run the game for us
4. keep the GM information hidden unless I ask for it
5. enforce the Delvekit zero-stamina rule exactly:
   - soft = first two hits to 0 Stamina may survive with a hard cost
   - medium = first hit to 0 Stamina may survive with a hard cost
   - hard = 0 Stamina means death unless an ally prevents the blow immediately
6. do not invent mercy rescues, capture twists, prophecies, or prolonging escapes that bypass that rule
7. keep any visible progress or thinking text generic and spoiler-safe; never reveal secret doors, trap truths, hidden map information, faction plans, or future consequences there

Use Candlelight Dungeons as the base rules and Candlelight Delvekit as the dungeon procedure.
```

That is enough for a simple “make us a delve and start play” session.

Paste something like this into Codex:

```text
Read:
- docs/candlelight_delvekit.md
- skins/candlelight_dungeons.md
- skins/candlelight_delvekit.md
- rules/appendices/candlelight_delvekit_quickref.md

Generate a Candlelight Delvekit dungeon for me:
- size: tiny
- difficulty: hard
- random seed is fine

Then:
1. generate the raw YAML
2. generate a polished player-facing title and blurb
3. generate a polished GM-facing module in markdown
4. show me the blurb first, do not show the module or yaml to the player
5. if I approve it, run the delve from that module
6. enforce the Delvekit zero-stamina rule exactly:
   - soft = first two hits to 0 Stamina may survive with a hard cost
   - medium = first hit to 0 Stamina may survive with a hard cost
   - hard = 0 Stamina means death unless an ally prevents the blow immediately
7. do not invent mercy rescues, capture twists, prophecies, or prolonging escapes that bypass that rule
8. keep any visible progress or thinking text generic and spoiler-safe; never reveal secret doors, trap truths, hidden map information, faction plans, or future consequences there

Keep the YAML as source of truth and the markdown as the reading copy.
```

For a fresh session, include both `skins/candlelight_dungeons.md` and `skins/candlelight_delvekit.md`.
Delvekit is not a replacement for Candlelight Dungeons; it is the dungeon procedure layered on top.

That is the intended Codex-first workflow.

## Manual Workflow

If you want to run the steps yourself:

1. Generate a dungeon YAML.
2. Prepare a polished player hook.
3. Prepare a polished GM module.
4. Use the polished module for play.

Minimal path:

```bash
.venv/bin/python tools/delvekit_seed.py \
  --seed 42 \
  --size medium \
  --difficulty medium \
  --out /tmp/delve.yaml

.venv/bin/python tools/delvekit_pitch.py prepare \
  --file /tmp/delve.yaml \
  --out /tmp/delve_pitch.md

.venv/bin/python tools/delvekit_adventure.py prepare \
  --file /tmp/delve.yaml \
  --out /tmp/delve_adventure.md
```

Then in Codex:

- paste `/tmp/delve_pitch.md`
- ask for a final `Title:` and `Blurb:`
- apply that result back to the YAML with `tools/delvekit_pitch.py apply`
- paste `/tmp/delve_adventure.md`
- ask for Markdown only
- use that Markdown as the GM-facing module text for play

The YAML stays the source of truth. The polished Markdown is the reading copy.

## Minimal Data Model

Each dungeon is a single YAML file with:

- `dungeon`: id, name, style, subtheme, size, difficulty, start room, player hook, player blurb, character motivation
- `rooms`: room records with coordinates and tags
- `keys`, `factions`, `solo_monsters`, `bosses`, `weird_npcs`
- `player_map`: current reveal state

Each room supports:

- `id`, `name`, `x`, `y`
- `description`, `atmosphere`, `contents`
- `exits`
- `secret_exits`
- `locks`
- `trap_tags`
- `puzzle_tags`
- `faction_tags`
- `solo_monster_tags`
- `boss_tags`
- `treasure_tags`
- `role_tags`
- `discovered`

That is enough to support:

- a hidden GM map
- a progressively revealed player map
- hand-authored dungeons
- seeded future generation

## Generator Scope

`tools/delvekit_seed.py` supports:

- sizes: `tiny`, `medium`, `large`
- difficulties: `soft`, `medium`, `hard`
- deterministic output from `--seed`
- weighted, not mandatory, feature placement

Possible generated features:

- a Grimtooth-style lethal trap room
- a solo monster
- two competing factions
- a boss
- 0-2 puzzles
- keyed progression
- treasure rooms
- a weird NPC
- loops or secret routes

The generator deliberately avoids megadungeons. `large` is still a bounded site.

### Size Expectations

- `tiny` — one-shot or short-session site, usually one strong loop or backtrack
- `medium` — a substantial delve with enough moving parts for a session or two
- `large` — a broader but still bounded site, not a campaign megadungeon

### Difficulty Expectations

- `soft` — adventurous and forgiving, close to stock Candlelight Dungeons; most bad calls hurt before they kill
- `medium` — proper old-school danger, where attrition and bad routing matter and repeated mistakes stack fast
- `hard` — openly lethal; wasted turns, bad luck, and two bad decisions can be enough to end a delver

### Probabilistic Features

Delvekit uses weighted generation, not fixed checklists.

- A site can include factions, a solo monster, a boss, keys, puzzles, a lethal trap room, treasure rooms, a weird NPC, loops, or secret routes.
- The generator should not force every site to contain every feature.
- `tiny` sites still get a minimum feature floor so they do not come out empty.
- `soft`, `medium`, and `hard` mainly change danger pressure, not subsystem complexity.

Generated dungeons also carry two player-facing hook fields:

- `hook_type` and `hook_summary`: a compact statement of what kind of adventure the site is pitching
- `pitch_skeleton`: the structured, spoiler-aware brief for final title/blurb polish
- `title_draft` and `player_blurb_draft`: generator draft copy, useful as raw material but not the final sales pitch
- `player_blurb`: the final polished player-facing hook, after an AI polish pass
- `character_motivation`: one concrete reason a delver would choose to enter it

These are meant for table selection and campaign framing, not hidden GM notes.

## Pitch Polish

Delvekit generation should be treated as two steps:

1. Generate the dungeon and its `pitch_skeleton`.
2. Run a short AI polish pass to turn that skeleton into a readable title and back-cover hook.

The Python generator is responsible for structure, motif, and spoiler control.
The final public prose should come from [prompts/chat/candlelight_delvekit_pitch_polish.md](/Users/zach/Desktop/Files/github/other/sinew-and-steel/prompts/chat/candlelight_delvekit_pitch_polish.md), usually via [tools/delvekit_pitch.py](/Users/zach/Desktop/Files/github/other/sinew-and-steel/tools/delvekit_pitch.py).

The polish pass should:

- write clean English instead of template prose
- sound like the back cover of an old adventure module
- stay concrete and enticing without spoiling hidden content
- preserve the true job, tone, and site pressure

The `pitch_skeleton` is intentionally compact. It includes:

- `patron`: the named surface contact
- `public_place`: the public-facing site label
- `public_motifs`: visible thematic cues
- `hook_type`: the kind of job being offered
- `job`: what the delver thinks they are going down to do
- `setup`: the patron's claim or rumor
- `reward`: the promised payoff
- `pressures`: 2-4 spoiler-safe complications
- `title_cues`: candidate title phrases
- `spoiler_guard`: hard limits on what the blurb must not reveal

The goal is not to let Python write great copy. The goal is to give an LLM a robust skeleton to finish well.

The same pattern can be used for the full adventure text. Delvekit can emit a larger Codex-facing adventure payload containing:

- the current title and player blurb
- the pitch skeleton
- the hidden GM map
- the initial player map
- room data
- keys, factions, monsters, bosses, and weird NPCs

That larger payload is intended for [prompts/chat/candlelight_delvekit_adventure_polish.md](/Users/zach/Desktop/Files/github/other/sinew-and-steel/prompts/chat/candlelight_delvekit_adventure_polish.md), usually via [tools/delvekit_adventure.py](/Users/zach/Desktop/Files/github/other/sinew-and-steel/tools/delvekit_adventure.py).

Typical workflow:

```bash
.venv/bin/python tools/delvekit_seed.py \
  --seed 42 \
  --size medium \
  --difficulty medium \
  --out /tmp/delve.yaml \
  --pitch-prompt-out /tmp/delve_pitch.md \
  --adventure-prompt-out /tmp/delve_adventure.md

.venv/bin/python tools/delvekit_pitch.py prepare \
  --file /tmp/delve.yaml \
  --out /tmp/delve_pitch.md

# Paste /tmp/delve_pitch.md into Codex and ask it to answer with:
# Title: ...
# Blurb: ...

.venv/bin/python tools/delvekit_pitch.py apply \
  --file /tmp/delve.yaml \
  --text-file /tmp/polished_pitch.txt

.venv/bin/python tools/delvekit_adventure.py prepare \
  --file /tmp/delve.yaml \
  --out /tmp/delve_adventure.md

# Paste /tmp/delve_adventure.md into Codex and ask it to return Markdown only.

.venv/bin/python tools/delvekit_adventure.py apply \
  --out /tmp/delve_module.md \
  --markdown-file /tmp/polished_module.md
```

## Difficulty Knobs

The add-on uses explicit knobs instead of a second combat engine.

### Soft

- suggested tone: `heroic (16)`
- lighter resource pressure
- lower trap-room chance
- first two hits to `0 STM` may survive with a hard cost
- slower faction escalation

### Medium

- suggested tone: `standard (6)`
- meaningful attrition
- serious traps
- active factions
- first hit to `0 STM` may survive with a hard cost; the next time is death

### Hard

- suggested tone: `grim (0)`
- harsh resource pressure
- highest trap lethality
- aggressive factions
- `0 STM` means death on hard
- do not soften hard mode with capture or other prolonging escapes unless the table explicitly asked for that tone

The point is to change risk with a few explicit dials, not to introduce a second combat engine.

## Map Rendering

`tools/delvekit_map.py` renders:

- full hidden GM maps
- player maps from discovered state
- optional frontier placeholders for adjacent unknown rooms

Maps use box-drawing room boxes, not `#` and `.` fill maps.

Example:

```bash
.venv/bin/python tools/delvekit_map.py \
  --file examples/candlelight_delvekit/pale_warrens.yaml \
  --mode gm
```

Player-map example:

```bash
.venv/bin/python tools/delvekit_map.py \
  --file examples/candlelight_delvekit/pale_warrens.yaml \
  --mode player \
  --frontier \
  --reveal-rooms 2,4 \
  --position 4
```

## Generate a Dungeon

Write YAML only:

```bash
.venv/bin/python tools/delvekit_seed.py \
  --seed 42 \
  --size tiny \
  --difficulty hard \
  --out /tmp/delvekit_42.yaml
```

Write YAML plus a markdown dossier and maps:

```bash
.venv/bin/python tools/delvekit_seed.py \
  --seed 42 \
  --size medium \
  --difficulty medium \
  --title "Lantern Vault" \
  --out /tmp/lantern_vault.yaml \
  --markdown-out /tmp/lantern_vault.md \
  --gm-map-out /tmp/lantern_vault_gm.txt \
  --player-map-out /tmp/lantern_vault_player.txt
```

Quick review loop:

```bash
.venv/bin/python tools/delvekit_seed.py \
  --seed 42 \
  --size medium \
  --difficulty medium \
  --out /tmp/delve.yaml

.venv/bin/python tools/delvekit_map.py --file /tmp/delve.yaml --mode gm
.venv/bin/python tools/delvekit_map.py --file /tmp/delve.yaml --mode player --frontier
```

## Test the Example

The fastest review path is:

1. Read `skins/candlelight_delvekit.md`
2. Read `examples/candlelight_delvekit/pale_warrens.md`
3. Render the YAML example as a GM map
4. Render a few player-map reveal states
5. Generate a few seeded dungeons and inspect the YAML and maps

Suggested commands:

```bash
.venv/bin/python tools/delvekit_map.py \
  --file examples/candlelight_delvekit/pale_warrens.yaml \
  --mode gm

.venv/bin/python tools/delvekit_map.py \
  --file examples/candlelight_delvekit/pale_warrens.yaml \
  --mode player \
  --frontier

.venv/bin/python tools/delvekit_seed.py \
  --seed 7 \
  --size tiny \
  --difficulty soft

.venv/bin/python tools/delvekit_seed.py \
  --seed 29 \
  --size medium \
  --difficulty medium

.venv/bin/python tools/delvekit_seed.py \
  --seed 81 \
  --size large \
  --difficulty hard
```

## What Is Still Rough

- The generator is intentionally prototype-scale, not a finished content engine.
- Room prose is serviceable and varied, but still table-driven.
- Map rendering favors readability over perfect inline annotation.
- The generator does not simulate faction patrol state over time; that still belongs to the Custodian at the table.
- The final title/blurb voice depends on a polish pass; the generator's draft copy is only scaffolding.

That is acceptable for this PR. The goal is a mergeable first Delvekit, not a forever-tool.
