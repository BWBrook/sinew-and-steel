---
name: build-prompt
description: Assemble a compact Custodian prompt, load detailed sections, and verify source freshness.
---

# Build Prompt

```bash
uv run python tools/build_prompt.py --list-skins
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/build_prompt.py --campaign scratch_demo --check --json
uv run python tools/build_prompt.py --section manual:6
```

The default compact prompt includes the Quickstart, complete skin and addons,
current campaign state, and a detailed-rules index. `--full` includes both core
books. `--section manual:6` prints a numbered section on demand; `--section
almanac:4` retrieves the Pressure procedure. Supplying `--section` with a campaign
includes it in the assembled prompt, so use the section-only form for a read.

Campaign output goes to `campaigns/<slug>/prompt.md`. Without a campaign, use
`--skin SLUG --out FILE`, or omit `--out` for stdout. `--dry-run` writes nothing;
`--json` reports assembly metadata. `--check` verifies a saved campaign prompt or
`--out FILE`, including body, source hashes, and campaign file inventory.

Hidden scenario material belongs in `campaigns/<slug>/state/memory/hidden_scenario.md`,
which every rebuild includes automatically. `--hidden FILE` is for one-off prompts.
It is not remembered, and neither are `--mode`, `--full` or `--keep-art`, so pass
them again when rebuilding; the first line of `prompt.md` records the mode, profile
and sources of the last build. Any play action, checkpoint or advancement makes a
saved campaign prompt stale by design: `--check` reports it, `validate_campaign.py`
treats it as an error, and the remedy is to rebuild before validating or resuming.
All assembled campaign prompts are private. `--mode chat` selects the chat template,
not a public filter; a model that cannot read the repository also needs `--full`.
Artwork is stripped by default; `--keep-art` preserves it. Resolve paths through
`manifest.yaml`.
