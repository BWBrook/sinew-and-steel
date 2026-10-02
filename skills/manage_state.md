---
name: manage-state
description: Maintain campaign mechanics transactionally and keep private memory separate from public narration.
---

# Manage State

Campaign state lives under `campaigns/<slug>/state/`. Character sheets contain
Luck and Stamina; the session tracker contains structured Pressure, resource
limits, clocks, and pending actions. Whispers uses individual Insanity tracks.
Keep the whole state directory private.

```bash
uv run python tools/play.py --campaign scratch_demo --character grak luck --amount 1 --source "Short rest"
uv run python tools/play.py --campaign scratch_demo --character grak stamina --amount -1 --source "Falling debris"
uv run python tools/play.py --campaign scratch_demo pressure --gain 1 --category ambient --source "Blizzard"
uv run python tools/play.py --campaign scratch_demo clock --name rescue --amount 1 --max 4 --source "Signal raised"
uv run python tools/play.py --campaign scratch_demo scene --label "At the shelter"
uv run python tools/play.py --campaign scratch_demo --character grak resource --name beast_bond --recover --amount 1 --source "Bond rite at the fire"
uv run python tools/play.py --campaign scratch_demo --character grak condition --name injured --source "Spear wound"
```

Supply the actual fictional source. `--dry-run --json` previews a change and
`--event-id ID` makes an exact retry safe. Pressure gains are not generic clock
updates: the engine records thresholds, pending penalties, and crises. See
[Pressure and crises](../docs/ai_play_harness.md#pressure-and-crises). A resource
is named by its manifest id; see
[Contexts, costs, and conditions](../docs/ai_play_harness.md#contexts-costs-and-conditions)
for `resource` and `condition`.

Use `advance.py` for milestones, scores, and bought tags, while the session is open
and before `session-close`. `update_sheet.py` is
for metadata such as inventory and notes; it rejects mechanical fields, including
attributes, pools, creation, advancement, and trackers. `recap.py` updates private
memory only. Use `session_log.py` for public narration and `checkpoint.py` for the
exact last public response. JSONL telemetry is written by the engine; do not
hand-edit it to make a run appear complete.
