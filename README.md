# **Sinew & Steel**

*A lean, setting-agnostic role-playing engine for the table, and for any reasoning AI in the Custodian's chair.*

---

## Why another ruleset?

Because most RPG rulebooks ask you to memorise a phone-book of subsystems before you can bleed on the page.
Sinew & Steel works the other way round:

* **One d20. Five stats. Luck tokens. Stamina. Pressure.**
* **Friction where it matters:** burning Luck, pushing damage through armour with margin, riding the Pressure fuse.
* **Skin-agnostic.** Swap the coat of paint and you're in Bronze-Age Atlantis, a Martian dust storm, or the heat-death horizon.
* **AI-ready.** The rules are easy for a language model to keep in short-term memory, so the Custodian (the game master) can focus on story beats instead of chart-flipping. This repository also gives an AI agent the tools to keep dice, state and secrets honest.

> *A lean chassis for messy stories. Expansion skins for the sparks.*

**Status:** version 0.4.0. The rules, ten skins and AI harness are being finalised; AI-run playtests come next, then the final book layout. Everything here is free and openly licensed (see [License](#license)).

---

## Core concept (60 seconds)

| Pillar | One-line summary |
|---|---|
| **Roll-under d20** | Roll at or under your score to succeed. A natural 1 always succeeds (it ignores soak and adds +1 damage); a natural 20 always fails. |
| **Scores** | Attributes baseline 10 (6–16) and Stamina baseline 5 (3–9), ceilings for life. Standard play starts with **6 build points** (grim 0, pulp 12, heroic 16): +1 above baseline costs 2 points; +1 below baseline costs 1 point; lowering scores pays back at most 8 points in all; a **tag** (Advantage in one named niche) costs 2. |
| **Luck = tokens** | Spend to nudge dice after seeing them (either die, in an opposed test). Your score sets the pool's size; a Luck test rolls under the tokens you have left. |
| **Stamina** | Baseline 5; buy it up or down with build points. Hits deal 1 + weapon edge + 1 per full 5 points of margin, minus soak (minimum 1). 0 = collapse. |
| **Pressure track** | A 0–5 fuse, usually shared by the party. Its name and effects change by skin (Doom, Shadow, Sin, Heat, Fatigue, Stress, Strain, Dread, Insanity, Anomaly…). |
| **Armour** | Soak 1–3 subtracts from damage; a winning hit always deals at least 1. |

That's the chassis. Skins add the setting and its procedures.

---

## Skins

| Skin | Pitch |
|---|---|
| Clanfire | Neanderthal Ice-Age survival. Totem spirits, Beast bonds, Shadow track. The book's exemplar skin. |
| Iron & Ruin | Pulp sword-and-sorcery. Doom, Heroic Acts, bargain-magic. |
| Time Odyssey | Brass-and-crystal chrononautics. Ingenuity pool, Anomaly crises, epoch graphing. |
| Briar & Benedictine | Medieval sleuthing. Divine providence, Sin and penance, murder mystery. |
| Rust & Domes | Noir-tinged Red Planet frontier. Heat track, psionics, red-dust grime. |
| Candlelight Dungeons | Old-school dungeon crawl. Fatigue clock, spell backlash, torchlit terror, plus an optional Delvekit for stricter procedural exploration. |
| Service Duct Blues | Lower-decks starship drama. Resourcefulness pool, Stress track, system saves. |
| Whispers in the Fog | Weird 1920s horror. Personal Insanity tracks, fragile hope, occult terror. |
| Free Traders of the Drift Marches | Starfreight drama. Ship Shares, Strain track, speculative cargo gambles. |
| Twilight of the Northlands | Wanderer fantasy elegy. Hope and Dread, subtle rites, travel Fatigue. |

Skins are optional: the core rules play perfectly well on their own. Swap a few words and build your own skin in an afternoon (`templates/skin_template.md`).

---

## Three ways to play

### At the table

1. Read `rules/quickstart.md` (two pages), then the Adventurer's Manual and Custodian's Almanac in `rules/core/` as you need them.
2. Pick a skin from `skins/`. Clanfire with the Emberfall starter scenario (`rules/scenarios/clanfire_emberfall.md`) is the gentlest first game.
3. Hand the rules to the players; keep the skin and scenario notes behind your screen.
4. Roll dice, burn Luck, tell messy stories.

To print the book, see `docs/pdf_building.md`.

### With an AI in chat

Any capable chat model can be your Custodian; the book's AI chapters (`rules/book/ai_as_custodian.md` and `rules/appendices/ai_play.md`) explain how to get the best from one. Build a filled-in prompt and paste it in:

```bash
uv run python tools/build_prompt.py --skin clanfire --mode chat --out /tmp/chat_prompt.md
```

Chat prompts carry both complete core books, because a chat model cannot read this repository. (`--profile compact` builds a shorter prompt with only the Quickstart and the skin; it tells the model to ask for missing rules rather than invent them.) The template in `prompts/chat/starter_prompt.md` holds `{{...}}` placeholders, so do not paste it raw.

For a secret scenario, the **Hidden Scenario Prompt** in `prompts/chat/` asks the model to write its notes in Chinese (see `prompts/chat/how_to_use_chinese_room.md`). That only guards against accidental spoilers: anyone with the chat can read or translate the notes.

### With an AI agent in this repository

Here a Codex CLI or Claude Code agent runs the game, and the tools keep the dice, campaign state and secrets honest.

1. **Install dependencies** (see [Setup](#setup)).
2. **List skins:** `uv run python tools/build_prompt.py --list-skins`
3. **Create a campaign and character:**
   ```bash
   uv run python tools/campaign_init.py --title "Scratch Demo" --skin clanfire --tone standard --random-character "Grak"
   ```
   The slug, `scratch_demo` here, comes from the title; use your own title for a real campaign.
4. **Build the agent prompt:**
   ```bash
   uv run python tools/build_prompt.py --campaign scratch_demo --mode agent
   ```
   This strips PDF-only artwork tags to keep the prompt clean; `--keep-art` keeps them.
5. **Play** from `campaigns/scratch_demo/prompt.md`. The agent resolves rolls and records state with `tools/play.py`.

The worked workflow is `docs/ai_play_harness.md`; `skills/agent_dm_handbook.md` is the agent's own guide, and `AGENTS.md` its operating rules.

**Resuming in a fresh context.** Any play action, checkpoint or advancement makes the saved prompt stale by design, so rebuild it first (with the same `--mode`, `--full` and `--hidden` options as before), then load the resume pack:

```bash
uv run python tools/build_prompt.py --campaign <slug>
uv run python tools/resume_pack.py --campaign <slug>
```

`--character <character_slug>` filters the pack to one sheet; omit it for a party. Add `--public` for the player view: a fixed selection of character fields and the exact public checkpoint, with private clocks, logs, paths and memory omitted. `skills/agent_bootstrap.md` is the shortest "get playing" path.

Example player directive for a fresh agent:
```
You're resuming a Sinew & Steel campaign. Read only AGENTS.md and skills/agent_dm_handbook.md.
Then run: uv run python tools/build_prompt.py --campaign <campaign_slug>
and: uv run python tools/resume_pack.py --campaign <campaign_slug>
Use that output for your internal context only (do not show memory/secrets/log to me).
If you have any questions, ask now. If not, print ONLY the checkpoint text and continue play from there.
```

### Candlelight fast path

For the torchlit dungeon-crawl lane:

- Read `skins/candlelight_dungeons.md` for the base skin.
- Add `skins/candlelight_delvekit.md` and `rules/appendices/candlelight_delvekit_quickref.md` for stricter exploration turns, keyed progression, hidden and player maps, and seeded site generation.
- `uv run python tools/build_prompt.py --skin candlelight_dungeons --mode agent --out /tmp/candlelight_prompt.md` builds an agent prompt; Candlelight prompts include the Delvekit automatically.
- `uv run python tools/delvekit_seed.py --seed 42 --size tiny --difficulty hard --out /tmp/delve.yaml` generates a bounded dungeon prototype.
- `docs/candlelight_delvekit.md` has the full workflow, and `examples/candlelight_delvekit/` has ready-to-read examples.

---

## Setup

The tools need Python 3.10 or later and PyYAML. For reproducible installs, use `uv`:

```bash
uv venv
uv sync
```

Without `uv`:

```bash
python -m venv .venv
. .venv/bin/activate
pip install pyyaml
```

Check the repository with `uv run python tools/validate_repo.py`, and run the tests with `uv run python -m unittest discover -s tests -q`.

---

## What's in the repository

* **`rules/`** — the book: Quickstart, core rules, starter scenario and AI chapters.
* **`skins/`** — the ten setting overlays.
* **`manifest.yaml`** — a machine-readable index of rules, skins, and prompts.
* **`AGENTS.md`** — operational rules for an AI agent running games.
* **`skills/`** — short, reusable instructions for common agent tasks (prompt building, dice, state, recaps).
* **`tools/`** — command-line helpers for prompts, rolls, campaign state and sessions (`tools/README.md` lists them).
* **`docs/ai_play_harness.md`** — the practical workflow for AI Custodian campaigns.
* **`examples/campaign_demo/`** — a worked example campaign (prompt, logs, memory, tracker).
* **`state/`** — seed fixtures that show the sheet, tracker, and memory formats.
* **`campaigns/`** — your untracked campaign workspaces; live state, logs, and checkpoints are in `campaigns/<slug>/state/`.
* **`docs/`** — the PDF build guide, the Delvekit guide, engine analyses and review records.

The tools you will use most in play:

* `tools/campaign_init.py` scaffolds a campaign; `tools/gen_character.py` and `tools/char_builder.py` add characters.
* `tools/play.py` resolves checks, opposed tests and attacks, and records Pressure, resources, scenes and sessions with atomic receipts. `--defer`, then `settle`, lets a player choose a Luck nudge after seeing the dice without a reroll.
* `tools/advance.py` awards milestones and records purchases against the creation snapshot.
* `tools/recap.py` and `tools/session_log.py` capture private memory and the public log; `tools/checkpoint.py` saves the exact last Custodian reply for a clean resume.
* `tools/resume_pack.py` (or `--public`) loads a campaign into a fresh context.
* `tools/playtest_summary.py` summarises Luck, Pressure, crises and roll choices from completed sessions.
* `tools/ss.py` is a single entry point (`uv run python tools/ss.py play ...`), and `tools/doctor.py` validates the repository and a campaign in one command.

---

## Contributing

Issues, forks, pull requests, new skins, typo fixes — all welcome. Keep additions:

* **Lean.** One new rule should replace three lines of "crunch".
* **Setting-agnostic** in core; setting-specific rules live in `skins/`.
* **Plain Markdown** first; we'll prettify later.

---

## License

* Sinew & Steel core rules © 2025 Barry Brook
* **Text & tables:** Creative Commons **CC-BY 4.0**
* **Helper code snippets:** MIT

See `NOTICE` and `LICENSES/` for details and scope.

Credit the project, hack it, sell adventures, translate it into Akkadian — just link back here.

---

> "Steel is honest; spells are treacherous. Dice are the coin we pay for either."
> — *Design notes, margin scrawl*

Happy carving.
