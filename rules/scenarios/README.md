# Scenarios

![](../../assets/art/ss_logbook.png){.wrap-right width=1.25in}

This folder contains short, table-ready scenarios for Sinew & Steel.

- Scenarios are written to be **publish-safe** and **skin-forward** (they teach the chassis by play).
- Each scenario is written for the **Custodian** (GM). Treat it as “behind the screen” material unless a section is explicitly marked as player-facing.
- Each scenario assumes you already have:
  - the quickstart rules (or the full core rules),
  - the relevant skin,
  - and (optionally) the repo harness tools if you want reproducible campaigns and clean resumes.

## Files in this folder

- `clanfire_emberfall.md` — a “play tonight” starter scenario (Custodian-facing).
- `clanfire_emberfall_hidden.md` — a compact, prompt-ready **hidden module** for AI Custodians (private notes only).
- `clanfire_emberfall_player_handout.md` — a player-safe, shareable one-page brief (no secrets).

## Using a hidden module (AI Custodian)

If you’re using the agent harness, look for a matching `*_hidden.md` module and pass it to `tools/build_prompt.py`:

```bash
python tools/build_prompt.py --skin <skin> --mode agent \
  --hidden rules/scenarios/<scenario>_hidden.md \
  --out /tmp/prompt.md
```

If you’re playing in a normal chat (no repo/tools), you can still use the hidden module: paste it into the AI prompt as “private Custodian notes”, and only share player-facing narration/options.
