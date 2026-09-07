# Changelog

## Unreleased
- Ruleset revision (7 September 2026, alpha): damage is now `1 + edge + 1 per full 5 points of margin - soak`, minimum 1; natural 1 ignores soak and adds +1. Replaces per-4 soak erosion and the separate +1 at margin 10, removing the hard zero against armour and the attribute-11 step.
- Opposed tests: both dice are read before anyone spends Luck. NPCs have no Luck pool unless a hook grants one.
- Advancement ceiling stated: attributes 16 and Stamina 9 hold for the life of the character; unspent build points carry over.
- Skins, Quickstart, README, the Emberfall teaching exchange, the demo prompt and log updated to the new wording; `tools/analysis/` re-encoded and re-verified.

## 0.3.1 - 2025-12-22
- Stamina now participates in the point-buy ledger (baseline 5), with build-point budgets integrated across rules, builders, validators, and sample builds.
- Added per-skin random generation defaults in manifest (`_gen`) and builder tracking fields in sheets.
- New tooling: `new_session.py`, `recalc_sheet.py`, resume pack `--public`, plus dry-run/JSON support across remaining mutators.
- Improved roll/beat ergonomics (nudges, spend-side controls, global flags after subcommands) and safer tracker/sheet clamping.
- Documentation refresh: bootstrap/resume flow, checkpoint discipline, and new tool examples.

## 0.3.0 - 2025-12-21
- Split prompts into chat vs agent templates and updated build_prompt `--mode`.
- Added schema_version fields to sheets/trackers/memory and roll tool version stamps.
- Hardened state mutation with strict path updates and `--allow-new` escape hatch.
- Standardized roll success semantics after nudges (raw vs final fields).
- Added doctor/ss utilities and example campaign scaffold under examples/.
- Clamped tracker clock updates in recap/beat.

## 0.2.0 - 2025-12-21
- Restructured rules, skins, and prompts into a predictable layout.
- Added agent harness docs, skills, and CLI tools for dice, state, and prompt assembly.
- Added campaign scaffolding, memory/logging tools, and point-buy character builder.
- Added manifest and templates to standardize skins, sheets, and trackers.
- Added uv-based Python environment pinning for reproducible tooling.
