# Changelog

## Unreleased
- TBD

## 0.3.0 - 2025-12-21
- Split prompts into chat vs agent templates and updated build_prompt `--mode`.
- Added schema_version fields to sheets/trackers/memory and roll tool version stamps.
- Hardened state mutation with strict path updates and `--allow-new` escape hatch.
- Fixed beat.py flag ordering (global flags accepted before/after subcommand).
- Standardized roll success semantics after nudges (raw vs final fields).
- Added doctor/ss utilities and example campaign scaffold under examples/.
- Clarified Stamina as separate from point-buy ledger; updated sample builds.
- Clamped tracker clock updates in recap/beat.

## 0.2.0 - 2025-12-21
- Restructured rules, skins, and prompts into a predictable layout.
- Added agent harness docs, skills, and CLI tools for dice, state, and prompt assembly.
- Added campaign scaffolding, memory/logging tools, and point-buy character builder.
- Added manifest and templates to standardize skins, sheets, and trackers.
- Added uv-based Python environment pinning for reproducible tooling.
