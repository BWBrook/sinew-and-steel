# **Appendix — Playing Sinew & Steel with an AI Custodian**

This appendix is for groups who want an AI to run Sinew & Steel as Custodian (GM).
It covers two approaches:

- **Copy/paste mode** (no tools): fast and casual.
- **Repo harness mode** (recommended): reproducible campaigns, clean resumes, typo‑resistant state.

If you remember nothing else:

- Don’t roll by default.
- State stakes before rolls.
- Keep secrets private (and don’t “leak” trackers into the fiction).
- Record what changed (what was spent; what ticked; what new threat appeared).

---

## 1) The one rule that matters

![](../../assets/art/ss_when_to_roll.png){.wrap-right width=1.6in}

**Do not roll by default.** Roll only when the outcome is uncertain *and* it matters.

An AI will often try to “gamify” everything into checks. Don’t let it.
Use the conversation loop first: intent, method, stakes, then (maybe) a roll.

If failure would be boring, resolve it narratively.

---

## 2) Two ways to play

![](../../assets/art/ss_public_private_notes.png){.wrap-right width=1.6in}

### A) Copy/paste mode (no tools)
Use this if you just want to play in a chat window.

1. Choose one skin (e.g., Clanfire).
2. Paste in (from the PDFs or the Markdown files):
   - the quickstart rules (or the full core rules if you prefer),
   - the skin text,
   - (optional) a short scenario (e.g., Clanfire’s “Emberfall”).
3. Tell the AI (in one short directive):
   - “Be Custodian. Keep secrets private.”
   - “Offer 2–4 numbered options each beat.”
   - “State stakes before any roll (what changes on success vs failure).”
4. Roll dice however you like (physical d20 works great).

This mode is fast, but less reliable: state can drift, and typos happen.

### B) Repo harness mode (recommended)
Use this if you want reproducible campaigns, clean resumes, and typo‑resistant state.

You’ll use:
- `campaigns/<slug>/` for each game (gitignored)
- CLI tools in `tools/` to roll, update sheets, track Pressure and other clocks, and resume

**Secret handling (important):** If players can see the AI’s output, you cannot keep secrets in the same chat.
Either (a) run the AI in a private Custodian chat and paste only public narration/options into the player channel, or (b) keep secrets in your own notes and only ask the AI for player‑facing text.

---

## 3) Repo harness: “play tonight” workflow
_Note: Codex CLI or Claude Code can implement this for you, for a fully automated workflow._

### 3.1 Setup (first time only)
Recommended (reproducible installs):

```bash
uv venv
uv sync
python tools/validate_repo.py
```

Read `AGENTS.md` once. It defines the repo’s “public vs private” conventions (especially `state/` and `campaigns/`).

### 3.2 Create a campaign
```bash
python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard
```

Optional: generate a random character:
```bash
python tools/campaign_init.py --title "Emberfall" --skin clanfire --tone standard --random-character "Grak"
```

### 3.3 (Optional) Add a hidden scenario module
Fastest option (no copying): use the built-in module file directly:
`rules/scenarios/clanfire_emberfall_hidden.md`

If you want to customise the module per campaign, create:
`campaigns/<slug>/state/memory/hidden_scenario.md`

…then copy the contents of `rules/scenarios/clanfire_emberfall_hidden.md` into it and edit freely.

### 3.4 Build the full prompt
Using the built-in module directly:
```bash
python tools/build_prompt.py --campaign <slug> --mode agent \
  --hidden rules/scenarios/clanfire_emberfall_hidden.md
```

Or, if you created a per-campaign module file:
```bash
python tools/build_prompt.py --campaign <slug> --mode agent \
  --hidden campaigns/<slug>/state/memory/hidden_scenario.md
```

By default, `tools/build_prompt.py` strips inline artwork image tags for prompt cleanliness; add `--keep-art` if you want them embedded.

Open `campaigns/<slug>/prompt.md` in your agent tool and begin play.

---

## 4) During play (the minimal tool loop)

The core loop is:

- Roll only when uncertainty + stakes.
- Apply consequences immediately (sheets, Pressure, and other clocks).
- Record a short private recap and a public log entry.

Roll a check:
```bash
python tools/roll.py check --stat 12
```

Update a sheet (example: spend 1 Luck token):
```bash
python tools/update_sheet.py --campaign <slug> --character <name> --inc pools.luck.current=-1
```

Tick Pressure or clocks:
```bash
python tools/trackers.py --campaign <slug> pressure --inc 1 --clamp
```

Capture private memory (summary + threads):
```bash
python tools/recap.py --campaign <slug> --summary "Beat recap…" --scene-inc 1
```

Append public log text:
```bash
python tools/session_log.py --campaign <slug> --role GM --text "Public narration…"
```

---

## 5) Save and quit (ironman checkpoint)

![](../../assets/art/ss_checkpoint_overwrite.png){.wrap-right width=1.6in}

Sinew & Steel campaigns are designed to be “ironman”: no branching, no rewind.

To resume cleanly in a fresh agent context, save **only the last GM message** (overwrite the prior checkpoint).
Do this after any GM response you might want to resume from.

```bash
cat /tmp/last_gm.md | python tools/checkpoint.py --campaign <slug>
python tools/checkpoint.py --campaign <slug> --show
```

---

## 6) Resume fast (fresh context)
Use the resume pack to rebuild context quickly:

```bash
python tools/resume_pack.py --campaign <slug> --character <name>
python tools/resume_pack.py --campaign <slug> --character <name> --public
```

Use `--public` any time you are sharing a resume pack with players: it skips private memory/secrets and keeps only logs + checkpoint.

---

## 7) Troubleshooting (keep the AI useful)

- **The AI rolls too much:** remind it “one roll per meaningful uncertainty”, and require stakes before rolls (“If we fail, what changes?”). If failure would be boring, narrate success and move on.
- **The AI forgets state:** in repo mode, regenerate context using `python tools/resume_pack.py --campaign <slug> --character <name>` (or run `python tools/summary.py --campaign <slug>` mid-session). In copy/paste mode, keep a small “current state” block and re-paste it occasionally.
- **Secrets keep leaking:** use a private Custodian chat (or repo mode with hidden files), and only share player‑safe text. When in doubt, share `resume_pack --public`, not raw `state/memory/` content.
