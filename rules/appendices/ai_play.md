# **Appendix — Playing Sinew & Steel with an AI Custodian**

This appendix is for groups who want an AI to run Sinew & Steel as Custodian (GM).
It covers two approaches: **copy/paste mode** and **repo harness mode**.

---

## 1) The one rule that matters
**Do not roll by default.** Roll only when the outcome is uncertain *and* it matters.

An AI will often try to “gamify” everything into checks. Don’t let it.
Use the conversation loop first: intent, method, stakes, then (maybe) a roll.

---

## 2) Two ways to play

### A) Copy/paste mode (no repo, no tools)
Use this if you just want to play in a chat window.

1. Choose one skin from `skins/`.
2. Paste in:
   - the quickstart rules (or the full core rules if you prefer),
   - the skin text,
   - (optional) a scenario like `rules/scenarios/clanfire_emberfall.md`.
3. Tell the AI: “Be Custodian. Keep secrets private. Offer 2–4 options.”
4. Roll dice however you like (physical d20 works great).

This mode is fast, but less reliable: state can drift, and typos happen.

### B) Repo harness mode (recommended)
Use this if you want reproducible campaigns, clean resumes, and typo‑resistant state.

You’ll use:
- `campaigns/<slug>/` for each game (gitignored)
- CLI tools in `tools/` to roll, update sheets, track clocks, and resume

---

## 3) Repo harness: “play tonight” workflow 
_Note: Codex CLI or Claude Code can implement this for you, for a fully automated workflow_

### 3.1 Setup (first time only)
Recommended (reproducible installs):

```bash
uv venv
uv sync
python tools/validate_repo.py
```

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

If you want to customize the module per campaign, create:
`campaigns/<slug>/state/memory/hidden_scenario.md`

…then copy the contents of `rules/scenarios/clanfire_emberfall_hidden.md` into it and edit freely.

### 3.4 Build the full prompt
```bash
python tools/build_prompt.py --campaign <slug> --mode agent \
  --hidden rules/scenarios/clanfire_emberfall_hidden.md
```

Open `campaigns/<slug>/prompt.md` in your agent tool and begin play.

---

## 4) During play (the minimal tool loop)

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
Sinew & Steel campaigns are designed to be “ironman”: no branching, no rewind.

To resume cleanly in a fresh agent context, save **only the last GM message** (overwrite the prior checkpoint):

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
