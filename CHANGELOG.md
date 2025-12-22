# Changelog

## Unreleased
- TBD

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
