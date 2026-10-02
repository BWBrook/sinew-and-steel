---
name: session-recap
description: Record private outcomes and open threads, then mark genuinely completed sessions for playtest review.
---

# Session Recap

`recap.py` edits memory only. After a scene or session, record a concise summary
of outcomes and new facts, unresolved threads, NPC changes, and private secrets.
Do not duplicate already-applied mechanical costs in the recap.

```bash
uv run python tools/recap.py --campaign scratch_demo \
  --summary "The clan found shelter; the wolf still follows." \
  --thread "Find a safe route to the river"
```

Apply mechanical changes when they happen through `play.py`; use `advance.py`
for milestone awards and purchases while the session is open. Those operations
create the structured playtest events. Recaps do not replace that evidence.

At the real end of a session, save the exact public checkpoint, resolve pending
actions/crises, end any combat, award any milestones (`advance.py` refuses once the
session is closed), then run `play.py session-close --label "Session complete"`.
`playtest_summary.py --campaign scratch_demo --json` distinguishes completed sessions
from interrupted ones. Begin the next session with `play.py session --label ...`,
which creates matching memory and public log files; open threads, NPCs and
secrets carry forward into the new memory file. Keep private recap contents
out of player output; `resume_pack.py --public` omits memory and logs entirely.
