---
name: build-prompt
description: Assemble a compact Custodian prompt, load detailed sections, and verify source freshness.
---

# Build Prompt

```bash
uv run python tools/build_prompt.py --list-skins
uv run python tools/build_prompt.py --campaign ice_hunt
uv run python tools/build_prompt.py --campaign ice_hunt --check --json
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

Use `--hidden FILE` for explicit scenario material. Campaign-local
`state/memory/hidden_scenario.md` is included automatically. All assembled campaign
prompts are private. `--mode chat` selects the chat template, not a public filter.
Artwork is stripped by default; `--keep-art` preserves it. Resolve paths through
`manifest.yaml` and rebuild when a freshness check reports changes.
