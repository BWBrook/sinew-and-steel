# **Sinew & Steel**

*A razor-lean, setting-agnostic role-playing engine—designed to sing at the table and purr in the context of any reasoning AI.*

---

## Why another ruleset?

Because most RPG rulebooks ask you to memorise a phone-book of subsystems before you can bleed on the page.  
Sinew & Steel works the other way round:

* **One d20. Five stats. Luck tokens. Stamina. Pressure.**  
* **Friction where it matters:**  Burning Luck, shaving armour with margin, riding peril tracks.  
* **Skin-agnostic.**  Swap the coat of paint and you’re in Bronze-Age Atlantis, a Martian dust storm, or the heat-death horizon.  
* **AI-ready.**  The rules are easy for a language model to keep in short-term memory, so the “GM” can focus on story beats instead of chart-flipping.

> *A lean chassis for messy stories. Everything else is skin and sparks.*

---

## Core concept (60 seconds)

| Pillar | One-line summary |
|---|---|
| **Roll-under d20** | ≤ attribute = succeed.  Natural 1 legendary, 20 catastrophic. |
| **Scores** | Attributes baseline 10 (6–16) and Stamina baseline 5 (3–9). Standard play starts with **6 build points** (grim 0, pulp 12, heroic 16): +1 above baseline costs 2 points; +1 below baseline costs 1 point. |
| **Luck = tokens** | Spend to nudge dice; pool size *is* the score. |
| **Stamina** | Baseline at 5; nudge with build points.  Hits deal 1 + weapon edge.  0 = collapse. |
| **Pressure track** | 0-5 fuse.  Colour changes by skin (Doom, Shadow, Sin, Heat, Fatigue, Stress, Strain, Dread, Insanity, Anomaly…). |
| **Dynamic armour** | Soak 1-3; attacker margin erodes soak 1 per 4 points. |

That’s the chassis. Everything else is flavour‐text.

---

## Example skins

|Scenario | Pitch |
|---|---|
|Clanfire | Neanderthal Ice-Age survival. Totem spirits, Beast bonds, Shadow track. |
|Iron & Ruin | Pulp sword-and-sorcery. Doom, Heroic acts, bargain-magic. |
|Time Odyssey | Brass-and-crystal chrononautics. Ingenuity pool, Anomaly crises, epoch graphing. |
|Briar & Benedictine | Medieval sleuthing. Divine providence, Sin and penance, murder mystery. |
|Rust & Domes | Noir-tinged Red Planet frontier. Heat track, psionics, red-dust grime. |
|Candlelight Dungeons | Old-school dungeon crawl. Fatigue clock, spell backlash, torchlit terror. |
|Service Duct Blues | Lower-decks starship drama. Resourcefulness pool, Stress track, system saves. |
|Whispers in the Fog | Weird 1920s horror. Insanity track, fragile hope, occult terror. |
|Free Traders of the Drift Marches | Starfreight drama. Ship Shares, Strain track, speculative cargo gambles. |
|Twilight of the Northlands | Wanderer fantasy elegy. Hope and Dread, subtle rites, travel Fatigue. |

Swap a few words and build your own skin in an afternoon.

---

## Quick start (campaign + agent)

Start here if you want a Codex CLI or Claude Code agent to run the game from this repo.

1. **Install deps (recommended):**
   ```bash
   uv venv
   uv sync
   ```
2. **List skins:** `python tools/build_prompt.py --list-skins`
3. **Create a campaign + character:**
   ```bash
   python tools/campaign_init.py --title "Ice Hunt" --skin clanfire --tone standard --random-character "Grak"
   ```
4. **Build the agent prompt:**
   ```bash
   python tools/build_prompt.py --campaign ice_hunt --mode agent
   ```
5. **Start play** using `campaigns/ice_hunt/prompt.md`, then track state with tools.

Canonical guide: `skills/agent_dm_handbook.md`

Starter scenario (Clanfire, “play tonight”):
- `rules/scenarios/clanfire_emberfall.md`
- `rules/scenarios/clanfire_emberfall_hidden.md` (prompt-ready module)

### Resume fast (fresh context)

If you’re resuming a campaign in a new agent context, use the resume pack:

```bash
python tools/resume_pack.py --campaign <slug> --character <name>
```
Add `--public` to redact private memory/secrets when you need player-safe output.

Or read: `skills/agent_bootstrap.md` for the shortest possible “get playing” path.

Example player directive (fresh Codex resume):
```
You’re resuming a Sinew & Steel campaign. Read only AGENTS.md and skills/agent_dm_handbook.md.
Then run: python tools/resume_pack.py --campaign <campaign_slug> --character <character_slug>
Use that output for your internal context only (do not show memory/secrets/log to me).
If you have any questions, ask now. If not, print ONLY the checkpoint text and continue play from there.
```


---

## Quick start (table / chat play)

1. **Read `rules/quickstart.md`.**  
2. Pick or clone a skin from `/skins/`.  
3. Hand the rules page to players; keep the skin doc behind your screen.  
4. (Optional) paste the **Starter Prompt** in `/prompts/chat/` into ChatGPT or another LLM and hit enter.
5. (Optional) use the **Hidden Scenario Prompt** in `/prompts/chat/` to generate a secret scenario/module! 
6. Roll dice, burn Luck, tell messy stories.

---

## Local setup (recommended)

The CLI tools are Python-based. For reproducible installs, use `uv`:

```bash
uv venv
uv sync
```

Alternative (no uv):

```bash
python -m venv .venv
. .venv/bin/activate
pip install pyyaml
```

---

## For AI game-masters

The repo’s `/prompts/chat/` folder contains:

* A **starter prompt template** that loads the engine + chosen skin in one go.  
* A **hidden scenario prompt** for secret GM notes.

No plugins needed for reasoning engines with tool use — `random.randint(1,20)` and short, punchy prose carry the night.

Appendix (AI play): `rules/appendices/ai_play.md`

---

## Agent harness (Codex / Claude Code / Jules-friendly)

This repo includes an agent-focused harness to run sessions without API adapters:

* **`AGENTS.md`** — operational rules for an AI agent running games.
* **`skills/`** — small, reusable instruction files for common tasks (prompt build, editor notes, dice, state updates).
* **`tools/`** — CLI helpers for assembling prompts, rolling dice, and updating YAML sheets.
* **`manifest.yaml`** — a machine-readable index of rules, skins, and prompts.
* **`state/`** — private notes, trackers, and character sheets (local runtime data).
* **`campaigns/`** — untracked per-campaign workspaces with their own state and logs.
* **`skills/agent_dm_handbook.md`** — end-to-end guide for running sessions with the tools.
* **`examples/campaign_demo/`** — a real example campaign scaffold (prompt, logs, memory, tracker).

Key utilities for play:
* `tools/campaign_init.py` to scaffold a campaign workspace.
* `tools/gen_character.py` to generate legal random characters.
* `tools/recap.py` and `tools/session_log.py` to capture private memory and public logs.
* `tools/apply_roll.py` to update sheets and trackers based on roll results.
* `tools/new_session.py` to advance memory/log files in lockstep.
* `tools/recalc_sheet.py` to recompute `creation.build_points_used` after manual edits.
* `tools/resume_pack.py` (or `--public`) for fast context resumes.
* `tools/checkpoint.py` for ironman save-and-quit checkpoints.
* `tools/doctor.py` to validate repo + campaign in one command.
* `tools/ss.py` for a single entry point (`python tools/ss.py beat ...`).

---

## Contributing

Issues, forks, pull requests, new skins, typo fixes — all welcome. Keep additions:

* **Lean.**  One new rule should replace three lines of “crunch”.  
* **Setting-agnostic** in core; setting-specific rules live in `skins/`.  
* **Plain Markdown** first; we’ll prettify later.

---

## License

* Sinew & Steel core rules © 2025 Barry Brook
* **Text & tables:** Creative Commons **CC-BY 4.0**  
* **Helper code snippets:** MIT

See `NOTICE` and `LICENSES/` for details and scope.

Credit the project, hack it, sell adventures, translate it into Akkadian — just link back here.

---

> “Steel is honest; spells are treacherous. Dice are the coin we pay for either.”  
> — *Design notes, margin scrawl*

Happy carving.
