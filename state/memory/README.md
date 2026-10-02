# Memory (Seed Fixture)

A campaign keeps short summaries, secrets, and open threads in
`campaigns/<slug>/state/memory/`, one file per session (`session_NNN.yaml`);
`play.py session` creates the next. Write to the current one with `tools/recap.py`.
Hidden scenario notes go in `hidden_scenario.md` in the same folder, which every
prompt rebuild includes automatically.
