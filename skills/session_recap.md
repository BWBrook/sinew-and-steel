---
name: session-recap
description: Record private outcomes and open threads, then mark genuinely completed sessions for playtest review.
---

# Session Recap

`recap.py` edits memory only. After a scene or session, record a concise summary
of outcomes and new facts, unresolved threads, NPC changes, and private secrets.
Do not duplicate already-applied mechanical costs in the recap.

```bash
uv run python tools/recap.py --campaign ice_hunt \
  --summary "The clan found shelter; the wolf still follows." \
  --thread "Find a safe route to the river"
```

Apply mechanical changes when they happen through `play.py`; use `advance.py`
for milestone awards and purchases. Those operations create the structured
playtest events. Recaps do not replace that evidence.

At the real end of a session, save the exact public checkpoint, resolve pending
actions/crises, then run `play.py session-close --label "Session complete"`.
`playtest_summary.py --campaign ice_hunt --json` distinguishes completed sessions
from interrupted ones. Begin the next session with `play.py session --label ...`,
which creates matching memory and public log files. Keep private recap contents
out of player output; `resume_pack.py --public` omits memory and logs entirely.
