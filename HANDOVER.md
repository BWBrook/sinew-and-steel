# Sinew & Steel: successor handover

Updated 7 September 2026. Start here, then read `AGENTS.md` and the files needed
for Barry's next request. This is a working snapshot; the live files and Barry's
current direction take precedence.

## Purpose and immediate position

Barry is developing a bespoke tabletop RPG with two complementary products:
a guided book for DriveThruRPG, and a Python harness for agents to run faithful,
reproducible sessions. The flagship is the guided book. A smaller starter pack
(core rules, Quickstart, probably two skins) follows once the book is ready.

The book has had extensive, author-approved prose revision. The tooling has
also completed a substantial simplification pass. Our publication work is now
at the visual review stage: the full book was rebuilt and handed to Barry for
inspection. Resume from his feedback. Further mechanics changes, a fresh
editorial sweep, and another architecture audit need a specific reason.

## Live state at handover

- The last tooling baseline is `2a153b2` ("Simplify harness and release tooling").
  Barry then requested a bundled commit and push of this handover and the
  mechanics analysis. Use `git log -1` for the closeout commit. A fresh remote
  check found only `main`; the sole checkout is the main project directory.
- `tools/analysis/` was untracked when the handover was written and is included
  in that closeout bundle. Its README describes probability/combat/Luck/build
  analysis. Its claims have not been verified in this handover and are not
  approved rule changes; inspect it if Barry resumes that separate work.
- `release/dist/build_report.yaml` records a successful full-book WeasyPrint
  build at that commit on 4 August 2026. The existing screen PDF was checked
  again for this note: 115 A4 pages. No new PDF build was run. Closeout checks
  passed: six harness tests, repository validation, and syntax parsing of the
  seven analysis scripts. The analysis calculations were not rerun.
- `assets/*`, `release/*`, and campaign workspaces are ignored by Git. Artwork
  is present locally, including `assets/covers/ss_cover_book_a4.png`; a fresh
  clone alone will not reproduce the illustrated book. Preserve local assets
  and private campaign data. Keep durable planning notes outside `release/`.

## Settled book decisions

The canonical assembly is `bundle_definitions()` in
`tools/_release_content.py`; `manifest.yaml` indexes the rules and skins.
The reading order is:

| Part | Chapters, in order |
| --- | --- |
| Introduction | 1. Preface; 2. Quickstart |
| Core Rules | 3. The Adventurer; 4. Adventurers Manual; 5. The Custodian; 6. Custodian's Almanac; 7. Customisation; 8. Clanfire (exemplar skin) |
| Starter Scenario | 9. Clanfire: Emberfall; 10. Clanfire Player Handout; 11. Clanfire Custodian Notes |
| Expansion Skins | 12. Iron and Ruin; 13. Time Odyssey; 14. Briar and Benedictine; 15. Rust and Domes; 16. Candlelight Dungeons; 17. Service Duct Blues; 18. Whispers in the Fog; 19. Free Traders of the Drift Marches; 20. Twilight of the Northlands |
| AI for Solo Play | 21. AI as Custodian; 22. AI Play Notes |

The back-cover blurb is unnumbered end matter. Book hierarchy is title, part,
chapter, then internal headings at levels 4/5. Assembly manages chapter headings
and page breaks; standalone Markdown heading levels are not the whole story.

`rules/book/ai_as_custodian.md` is the stance chapter.
`rules/appendices/ai_play.md` is the human-facing appendix; the detailed agent
workflow lives in `docs/ai_play_harness.md`. The prompt-ready Emberfall hidden
notes stay out of the book. Its authored Custodian Notes chapter complements
the scenario rather than repeating it. Zach Aandahl's dungeon sidecar is
documented in `docs/candlelight_delvekit.md` and introduced in the Candlelight skin.

## Layout workflow and remaining work

Use **WeasyPrint**, which supports the intended image wrapping. This project
moved from WSL to macOS; platform font handling was repaired. A4 is settled.
The current design has hierarchical TOC entries with page numbers, restrained
page rules, and lower-centre page numbers omitted on the cover and back page.

The modular visual pass reached Preface and Quickstart, including less bolding,
slightly looser line spacing, and tighter paragraph spacing. Quickstart must
occupy **exactly two pages**. In the last inspected full build it occupies
pages 6-7; The Adventurer starts on page 8. The cover, TOC, Preface, Quickstart,
chapter transition and back page were sampled, not every page of the book.

Continue section by section with Barry, normally starting with The Adventurer
unless his PDF feedback points elsewhere. Make local source fixes where they
belong and shared style fixes where they affect the whole book. Standalone
renders help diagnosis, but release assembly adds headings, wrappers and CSS;
confirm pagination-sensitive work in the full build. Passing a standalone
Quickstart render has previously concealed a full-book spill.

After the chapter pass: inspect the assembled book for remaining layout issues;
complete front/back matter, credits/legal, character sheet and asset checks;
then define the starter pack and finish DriveThru metadata and packaging.
Screen/print filenames alone do not establish distributor readiness. Check
current official submission requirements when that work becomes active.
Earlier referenced DriveThru plan/listing drafts are absent locally; do not
assume a completed release checklist exists.

## Ruleset revision, 7 September 2026

Barry reopened the mechanics work with explicit permission to iterate (alpha
testing; the engine should work at every tier, not only when tuned). Changes
landed in the rules text, all skins, Quickstart, README, the Emberfall teaching
exchange, the demo prompt and log, and `tools/analysis/`: see `CHANGELOG.md`
(Unreleased). The damage rule is now one formula with a minimum of 1; Luck
timing in opposed tests and a lifetime score ceiling are stated. Left open on
purpose: attacker disadvantage in symmetric opposed tests (both-fail and ties
go to the defender) and the tone dial gating breadth rather than peak. The
full book was rebuilt after the change: 115 pages, Quickstart on pages 6-7.
Rebuild after any further rules change and re-check that constraint.

## Useful commands and code map

Run from the repository root. `docs/pdf_building.md` explains the workflows.

```sh
uv sync --extra pdf
uv run --extra pdf python tools/release_build.py --bundle full_book --pdf --backend weasyprint --style bookish
```

Outputs: `release/dist/SinewAndSteel_FullBook_v0.3.1_screen.pdf` and
`release/dist/SinewAndSteel_FullBook_v0.3.1_print.pdf`.

For an individual section:

```sh
uv run --extra pdf python tools/md_pdf.py rules/book/the_adventurer.md --backend weasyprint --style bookish --paper a4 --out release/test/the_adventurer.pdf
```

Shared styles live in `templates/html/bookish.css`; runtime overrides also
live in the renderers. `tools/release_build.py` coordinates release builds,
`_release_content.py` assembles the book, `_pdf_render.py` renders release PDFs,
and `_pdf_common.py` shares platform/font/image handling with `md_pdf.py`.
Check both paths before assuming a standalone style change reaches the book.

The harness simplification removed obsolete state/compatibility paths,
centralised character construction and opposed dice outcomes, and split
Delvekit generation, prose and output responsibilities. Retain the lean design;
authored rules and skins were protected throughout that engineering work.
For relevant code changes, existing checks are:

```sh
uv run python -m unittest discover -s tests -q
uv run python tools/validate_repo.py
uv run python tools/validate_campaign.py --campaign emberfall
```

Campaign validation takes a slug, not a filesystem path. At the last code
handoff all six harness tests, repository validation and the two example
campaign validations passed. Re-run checks according to the next change.

## Collaboration and skills

Barry supplies the authored voice and design judgment, reviews concrete results,
and often edits alongside the agent. Preserve his worktree changes. Use direct
prose, restrained emphasis, and few em dashes. Avoid habitual "not X, but Y"
rhetoric and gratuitous polishing of already approved text.

Use these personal skills when their task applies (paths relative to `~/.codex/skills/`):

- `twilight-laboratory/SKILL.md`: coherent stages, autonomous routine decisions,
  substantive human review points, and the 80/20 stopping cadence. Apply its
  collaboration principles proportionally to this creative project.
- `kill-your-darlings/SKILL.md`: keep tooling lean; remove complexity only after
  checking current consumers and recoverability. Further refactoring needs a
  concrete benefit.
- `audit-ai-writing/SKILL.md`: for requested prose edits; preserve meaning and
  Barry's voice while removing generic AI rhetoric.
- `pdf/SKILL.md`: inspect actual rendered pages for layout work; successful
  compilation alone does not verify appearance.
- `.system/imagegen/SKILL.md`: for requested illustration or cover changes.

Deliver one coherent requested tranche, perform a focused review/repair pass,
then return a useful result. Avoid repeated audits and marginal polish loops.
Commit, push or publish only under applicable user authorization; earlier
completed commit requests are not standing permission. This handover itself
authorizes no new rules changes or publication actions.
