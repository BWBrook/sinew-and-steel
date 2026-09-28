# Changelog

## Unreleased
- Prose pass with the author, section by section in reading order (in progress). Preface and Quickstart: fewer reveal colons and emphasis italics, stock phrases and restating summary lines removed, terms matched to the Manual. The Preface now explains Custodian and S&S at first use and gives the public repository address. The Quickstart names all ten skins, shows a worked damage result, and still prints on exactly two facing pages (pp. 6-7). The Adventurer: "X is Y" headings turned into instructions, and the closing vignette now agrees with the rule that the Custodian states failure costs before a roll. Adventurer's Manual: section 5 no longer duplicates 1.4 (5.1 is the step-by-step test, 5.2 defines attacker and defender), key terms are defined, Luck and combat are regrouped in playing order, and Grak's full build is a worked example. The text now states outright that trade-offs pay only for raises, so a tag always costs build points (a grim-budget character buys no tags at creation). The Manual's rules, section numbers, tables and images are unchanged. The Custodian: headings turned into instructions, the Custodian says what is at stake before anyone rolls, and the vignette ends on the scene instead of a moral. Custodian's Almanac: the quick guide is regrouped (Pressure rules in one place, Luck-test frequency folded in), Toolkit Part II is re-lettered A-H, and "Fatal tag" is now "Fatal harm" so that "tag" means only the core rule. Corrections: the Cave Bear counter-swipes on an attacker's natural 20, not a natural 1; the old-school AC and 2d6 conversions now give usable numbers; the attacker's share of equal-score exchanges is 25-46% (Table 9.2), not a flat third; at the grim budget, a tag beyond a skin's free grant is earned at a milestone. NPC design gains the engine atlas's plate note and tier-difficulty odds. Customisation: Luck is counted once among the five attributes, the Pressure invariant matches the Manual, edge and soak are no longer called tags, and a new invariant keeps the creation ledger fixed (a skin sets only the budget and free grants).
- Independent engine review: exact creation, resolution, Luck and Pressure calculations; 1.48 million coupled combat simulations; all ten skins; matched Delvekit generation. Methods, figures, limitations and decisions are in `docs/independent_engine/README.md`. Keep the damage engine, Twilight stances and creation ledger; the observed specialist advantage is conditional on the adventure's demands.
- Rules and skins clarify attempt/recovery cadence, attribute/tag scope, initiative, current-Luck targets, cost reservation, Pressure sequencing, trade stakes, scans, travel roles, assemblies and Knack costs. Book layout is deferred.
- Harness fixes enforce natural outcomes, cancelling Advantage/Disadvantage, bounded nudges and correct sheet ownership/current Luck. Soft tiny Delvekit variety fill no longer forces traps or roaming monsters. Added 18 regression tests; 27 tests pass in total.
- Engine atlas: `tools/analysis/atlas.py` sweeps every interaction in the engine (success, margin, opposed tests, damage, time to drop, survival, parties, Luck economy, creation economy, advancement, Pressure fuse, skin procedures) into `docs/engine_atlas/` figures and tables, with commentary and a ranked findings list in `docs/engine_atlas.md`. New optional dependency group `analysis` (matplotlib).
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
