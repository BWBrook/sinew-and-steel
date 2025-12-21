# Handover Notes — Sinew & Steel Repo Review

These notes are for an independent reviewer (GPT‑5.2 Pro) who will read the repo and provide critique and recommendations.

## 1) What this repo is

**Sinew & Steel** is a lean, setting‑agnostic roll‑under d20 RPG engine with “skins” (genre overlays). The repo is being evolved into an **agent-first harness** designed for subscriber tools like **Codex CLI** (OpenAI) and **Claude Code** (Anthropic) to run sessions.

Key principle: **no API adapter code**. Instead, we supply:
- Markdown prompt templates and operational rules for an agent DM.
- A small toolbox of local scripts (Python) to handle dice/state bookkeeping.
- A file layout that supports multiple campaigns without git churn.

## 2) The design goal (what we’re optimizing for)

We want a “drop-in repo” that a new user can clone and immediately:
1. Choose a skin.
2. Create a campaign workspace (untracked) with its own state.
3. Generate or build a character sheet.
4. Produce a full prompt for a Codex/Claude agent.
5. Run a branching story **with mechanics in service of narrative**, not mechanics-first.

Success criteria:
- A new user can get from clone → first playable scene in minutes.
- An agent DM can run sessions while reliably updating sheets/trackers.
- Private GM memory stays private (file separation + workflow).
- Tooling is robust, not brittle, and resists user/agent mistakes.

## 3) Repo layout overview

### Core content
- `rules/core/` — core rules docs.
- `rules/quickstart.md` — rules on a page.
- `skins/` — skin add-ons (genre overlays).
- `prompts/` — prompt templates (starter + hidden scenario workflow).

### Harness and automation
- `AGENTS.md` — operational rules for AI agents.
- `skills/` — “skills” as reusable instruction files (Codex/Claude style).
- `tools/` — local CLI helpers.
- `manifest.yaml` — machine-readable index of rules/skins/prompts/templates + skin metadata.

### Runtime play state
- `campaigns/` — **git-ignored** per-campaign workspaces, each with its own state.
- `state/` — repo-level state scaffolding (also mostly ignored); campaign mode is preferred.

## 4) What exists today (major capabilities)

### Campaign scaffolding
- `tools/campaign_init.py` creates:
  - `campaigns/<slug>/campaign.yaml`
  - `campaigns/<slug>/state/characters/`
  - `campaigns/<slug>/state/trackers/session.yaml`
  - `campaigns/<slug>/state/memory/session_001.yaml`
  - `campaigns/<slug>/state/logs/`

### Prompt building
- `tools/build_prompt.py --campaign <slug>` builds `campaigns/<slug>/prompt.md`.

### Dice + bookkeeping
- `tools/roll.py` rolls checks/opposed checks (JSON output).
- `tools/update_sheet.py` updates YAML sheets (supports `--campaign` + `--character` shortcuts).
- `tools/trackers.py` updates scene counter and clocks (supports `--campaign`).

### Higher-level helpers
- `tools/recap.py` appends structured private memory and can update trackers.
- `tools/session_log.py` appends to public-ish logs.
- `tools/apply_roll.py` applies success/failure updates from roll JSON (also supports campaign shortcuts).
- `tools/summary.py` prints a one-screen campaign snapshot.
- `tools/beat.py` orchestrates a roll + optional nudge + state changes + log/recap in one command.

### Validation
- `tools/validate_repo.py` sanity-checks repo integrity.
- `tools/validate_sheet.py` validates a character sheet:
  - stats range 6–16
  - point-buy “double-debit” correctness
  - pool bounds
  - pressure track bounds
- `tools/validate_campaign.py` validates campaign scaffolding and state files.

### Character creation
There are two paths:
- `tools/gen_character.py` generates a **random** sheet using the **double-debit** method.
- `tools/char_builder.py` validates a **manual point-buy** build.

Important: We corrected the earlier “sum 50” misconception — validation is now based on the *written* rules: baseline 10, +1 above baseline costs -2 elsewhere.

## 5) What we want from your review

Please evaluate and suggest changes in these areas.

### (i) Repo design / UX for new users
- Is the layout intuitive?
- Are the “first steps” obvious?
- Is the split between core system vs harness clear?
- Should anything move between `rules/`, `skills/`, `AGENTS.md`, and `prompts/`?
- Is the campaign concept (slug + git-ignored workspace) well-explained and ergonomic?

### (ii) Tooling correctness + robustness
- Do tools behave consistently?
- Are default behaviors safe and predictable?
- Are there failure modes where an agent/human will drift state (wrong file, wrong campaign, wrong character)?
- Are validators sufficiently strict, or too strict?
- Are the tools missing obvious high-value commands?

Specific areas to scrutinize:
- Point-buy validation vs random generation alignment.
- Whether `beat.py` is a good abstraction or too complex.
- Whether `recap.py` and `session_log.py` are structured well.
- Whether JSON/YAML formats are stable and good for LLM use.

### (iii) Rules / skins prose (content quality)
This is not the first priority, but please assess:
- Are the core rules coherent and readable?
- Do skins feel consistent with the chassis?
- Do any skins contradict core mechanics in confusing ways?
- Are there recurring phrasing patterns that may confuse an LLM GM?

### (iv) Anything else (architecture and future direction)
We are aiming for:
- More reproducibility and “it just works” for fresh clones.
- Better guidance so agent DMs **don’t roll for everything**.
- Tools that reduce ceremony per beat.

Please also consider:
- Whether uv + venv setup (`pyproject.toml`, `uv.lock`) is adequate.
- Whether we should package tools as a CLI (entry points) vs keep them as scripts.
- Whether `manifest.yaml` is the right shape and should include more metadata (e.g., skill-to-tool mapping, default sheet template per skin).

## 6) Known pain points / history (context)

We’ve already encountered and fixed issues during live stress testing:
- Campaign mode bugs in `build_prompt.py` (quoting error) were fixed.
- `session_log.py` originally created a new log file unexpectedly; now it appends by default.
- Point-buy rules were initially validated as “sum 50”; now corrected to true double-debit.
- We added `--campaign` shortcuts across tools to reduce path friction.

A live stress-test campaign exists locally (not tracked) under `campaigns/alpha_mensae_9`.

## 7) How to run a quick local smoke test

Suggested commands:

```bash
uv venv
uv sync
python tools/validate_repo.py

python tools/campaign_init.py --name demo --skin jeffries_tube_blues --random-character "Demo Crew"
python tools/build_prompt.py --campaign demo
python tools/summary.py --campaign demo
python tools/validate_campaign.py --campaign demo
```

## 8) What “good feedback” looks like

If possible, please provide:
- A prioritized list of improvements (top 5).
- Any design changes you’d recommend before expanding features.
- One or two concrete “north star” workflows for a new user (step-by-step).
- Any risks: brittleness, complexity, unclear boundaries, or likely confusion points.

Thanks — the goal is to make this repo something a brand-new player can use with a CLI agent without reading a bunch of theory first.
