# Changelog

## Unreleased
- `gen_character.py --tag` (repeatable) reserves 2 build points per tag before the rest of the budget is spent on scores, and refuses tags the budget cannot cover.

## 0.4.0 - 2026-09-07
- Ruleset revision (7 September 2026, alpha): damage is now `1 + edge + 1 per full 5 points of margin - soak`, minimum 1; natural 1 ignores soak and adds +1. Replaces per-4 soak erosion and the separate +1 at margin 10, removing the hard zero against armour and the attribute-11 step.
- Opposed tests: both dice are read before anyone spends Luck. NPCs have no Luck pool unless a hook grants one.
- Advancement ceiling stated: attributes 16 and Stamina 9 hold for the life of the character; unspent build points carry over.
- Skins, Quickstart, README, the Emberfall teaching exchange, the demo prompt and log updated to the new wording; `tools/analysis/` re-encoded and re-verified.
- Tags are a core rule (Adventurer's Manual 2.6): a named niche for 2 build points, Advantage when the fiction squarely fits. Skin knacks and Expertise are tags; the four knack skins now state their free grants. Grak, Tom Calder and Sister Aveline re-priced to carry their tag inside budget. Sheets gain a `tags:` list; builder, validator and recalc count them.
- Almanac Toolkit gains "Why the defender wins ties", stating the opposed-test asymmetry as a design choice.
- Editorial pass over the whole book: removed repeated one-line maxims that restated the section, morals appended to the two vignettes, grandiose sign-off flourishes on every skin, and spaced hyphens doing em-dash work in prose. Rules text unchanged.
- Release pipeline: the screen and print PDFs now differ in substance. Screen downsamples images to 150 dpi (full book 36 MB to 2 MB); print keeps 300 dpi lossless (6 MB). Both carry real PDF metadata (title, author, subject, keywords) instead of the file stem.
- Removed the dead trim pipeline (`suggest_trim.py`, `apply_trim_suggestions.py`): no `trim=` attributes remain in the book. Removed the LaTeX PDF backend and its pandoc templates; WeasyPrint is the only renderer. `validate_repo.py` gained argparse so `--help` no longer runs a validation. Added a smoke test that runs `--help` on every CLI tool, and a `CLAUDE.md` that points Claude Code at `AGENTS.md`.
- Documentation audit: every quoted command now matches the tools' argparse. Fixed backslash-escaped quotes and skin-mismatched stat keys in `tools/README.md`, a missing tracker path in the recap skill, a broken image link in the PDF doc, and standardised every invocation on `uv run python tools/...`. Ancillary files (README, editor lint list, dice and character skills, starter prompts, example and seed sheets, the demo prompt) now carry the tags, lifetime-ceiling and opposed-test Luck-timing rules.

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
