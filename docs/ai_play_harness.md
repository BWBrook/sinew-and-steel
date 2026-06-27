# **AI Play Harness Workflow**

This document is the practical companion to the book appendix **AI Play Notes**.
The book explains what the harness is for. This file explains how to use it.

Use this when you want an AI Custodian to run Sinew & Steel with reproducible state, clean resumes, private notes, and fewer context-drift problems than a plain chat window.

## What the harness gives you

The repo harness keeps play grounded in files the agent can read and update:

- `campaigns/<slug>/` for each local game,
- character sheets and trackers under campaign state,
- public logs and private memory,
- checkpointed last Custodian messages,
- prompt builders that assemble rules, skins, and hidden notes.

It does not replace judgment. It gives the AI fewer excuses to forget what happened.

## Two ways to play

### Copy/paste mode

Use this if you just want to play in a chat window.

1. Choose one skin, such as Clanfire.
2. Paste the Quickstart or full rules.
3. Paste the skin text.
4. Optionally paste a short scenario, such as Clanfire: Emberfall.
5. Tell the AI:
   - "Be Custodian. Keep secrets private."
   - "Offer 2-4 numbered options each beat."
   - "State stakes before any roll."
   - "Do not roll unless uncertainty matters."
6. Roll dice however you like.

This mode is fast, but state can drift and secrets are fragile.

### Repo harness mode

Use this if you want reproducible campaigns, clean resumes, and typo-resistant state.

You will use:

- `campaigns/<slug>/` for each game,
- CLI tools in `tools/` to roll, update sheets, track Pressure and other clocks, and resume,
- `AGENTS.md` for public/private operating conventions.

If players can see the AI's output, you cannot keep secrets in the same channel. Use a private Custodian chat or keep hidden notes in files and share only player-facing narration.

## First-time setup

Install dependencies and validate the repo:

```bash
uv sync
uv run python tools/validate_repo.py
```

Read `AGENTS.md` once. It defines the repo's public/private split, especially `state/` and `campaigns/`.

## Create a campaign

Start a campaign:

```bash
uv run python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard
```

Optionally generate a random character during setup:

```bash
uv run python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard --random-character "Grak"
```

## Add hidden scenario notes

Fastest option: use a built-in hidden module directly.

```bash
uv run python tools/build_prompt.py --campaign <slug> --mode agent \
  --hidden rules/scenarios/clanfire_emberfall_hidden.md
```

For campaign-specific edits, create:

```text
campaigns/<slug>/state/memory/hidden_scenario.md
```

Then copy the hidden module into that file, edit freely, and build the prompt from the campaign-local version:

```bash
uv run python tools/build_prompt.py --campaign <slug> --mode agent \
  --hidden campaigns/<slug>/state/memory/hidden_scenario.md
```

By default, `tools/build_prompt.py` strips inline artwork image tags for prompt cleanliness. Add `--keep-art` if you want them embedded.

Open `campaigns/<slug>/prompt.md` in your agent tool and begin play.

## During play

The minimal loop is:

1. Ask for intent and method.
2. State stakes if a roll might matter.
3. Roll only when uncertainty matters.
4. Apply consequences immediately.
5. Record what changed.
6. Checkpoint the last Custodian message.

Roll a check:

```bash
uv run python tools/roll.py check --stat 12
```

Update a sheet, such as spending 1 Luck token:

```bash
uv run python tools/update_sheet.py --campaign <slug> --character <name> --inc pools.luck.current=-1
```

Tick Pressure or another clock:

```bash
uv run python tools/trackers.py --campaign <slug> pressure --inc 1 --clamp
```

Capture private memory:

```bash
uv run python tools/recap.py --campaign <slug> --summary "Beat recap..." --scene-inc 1
```

Append public log text:

```bash
uv run python tools/session_log.py --campaign <slug> --role GM --text "Public narration..."
```

## Save and quit

Sinew & Steel campaigns are designed to be ironman: no branching, no rewind.

To resume cleanly in a fresh agent context, save only the last Custodian message. Do this after any Custodian response you might want to resume from.

```bash
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign <slug>
uv run python tools/checkpoint.py --campaign <slug> --show
```

## Resume in a fresh context

Use the resume pack to rebuild context:

```bash
uv run python tools/resume_pack.py --campaign <slug> --character <name>
uv run python tools/resume_pack.py --campaign <slug> --character <name> --public
```

Use `--public` any time you are sharing a resume pack with players. It skips private memory/secrets and keeps only logs plus checkpoint.

## Keep the AI useful

- **The AI rolls too much:** remind it "one roll per meaningful uncertainty" and require stakes before rolls. If failure would be boring, narrate success and move on.
- **The AI forgets state:** regenerate context with `tools/resume_pack.py`, or keep a small current-state block in copy/paste mode.
- **Secrets leak:** use a private Custodian channel or repo-hidden files. Share only player-safe narration and options.
- **Consequences get soft:** point back to the current sheet, trackers, pressure clocks, and last checkpoint. The files are there so the world can remember.

The harness is successful when it becomes boring: the agent has the right rules, the right state, and a clear next beat, so the session can feel like play instead of prompt maintenance.
