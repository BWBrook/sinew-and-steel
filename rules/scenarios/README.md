# Scenarios

This folder contains short, table-ready scenarios for Sinew & Steel.

- Scenarios are written to be **publish-safe** and **skin-forward** (they teach the chassis by play).
- Each scenario should be runnable with:
  - `rules/quickstart.md` (player rules),
  - the relevant skin in `skins/`,
  - and (optionally) the AI harness tools (`tools/`) if you want repo-driven play.

If you’re using the agent harness, look for a matching `*_hidden.md` module you can pass to:

```bash
python tools/build_prompt.py --skin <skin> --hidden rules/scenarios/<scenario>_hidden.md --out /tmp/prompt.md
```

