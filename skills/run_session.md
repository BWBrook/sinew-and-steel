---
name: run-session
description: Run a campaign through the shared engine and preserve public narration, private state, and session evidence.
---

# Run Session

1. Rebuild the saved prompt, then validate and resume the campaign with
   [agent bootstrap](agent_bootstrap.md). Any play action, checkpoint or advancement
   makes the saved prompt stale by design, and validation treats a stale prompt as
   an error; rebuild with the same `--mode`, `--full` and `--hidden` options.
2. Ask for intent and method. State success and failure stakes before a necessary
   roll; otherwise resolve the fiction without dice.
3. Use `play.py check|opposed|attack --defer`, show the dice, and `settle` the chosen
   Luck spend. Supply contexts, source modifiers, and declared costs honestly.
4. Apply adjudicated consequences with engine commands. Resolve pending crises
   through their skin table; do not reset them with a generic clock edit.
5. Record a narrative beat with `play.py beat --label ...` and mark it `--perilous`
   when appropriate. A die roll is not itself a beat.
6. Keep private summaries in `recap.py`, public narration in `session_log.py`, and
   save the exact public response after each Custodian turn:

```bash
cat /tmp/last_gm.md | uv run python tools/checkpoint.py --campaign scratch_demo
```

In combat, an `attack` or an `opposed` test a combatant starts uses that
combatant's action for the round; after a plain `check`, record the turn with
`play.py pass`. The earlier side in initiative order acts or passes before the
later side.

Start scenes with `play.py scene --label ...`; use `boundary --kind camp|port
--reason ...` only when the fiction allows the corresponding resource reset.
Recovery uses explicit Luck/Stamina/Pressure commands. Award milestones and
spend build points with `advance.py` while the session is open, before
`session-close` (it refuses once the session is closed), preserving creation
history.

At a completed session boundary, settle pending actions/crises, end any combat,
award any milestones, record private recap and unresolved threads, then:

```bash
uv run python tools/play.py --campaign scratch_demo session-close --label "Session complete"
uv run python tools/playtest_summary.py --campaign scratch_demo --json
uv run python tools/play.py --campaign scratch_demo session --label "Next session"
```

If play merely pauses, leave the session incomplete and resume its checkpoint.
Do not manufacture an end marker for metrics. `new_session.py` is a wrapper for
`play.py session` that accepts `--campaign` and `--label`; it requires the previous
session to be closed.
