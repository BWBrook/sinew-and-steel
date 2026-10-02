# External review brief

Commissioned by Barry W. Brook, the author, on 2 October 2026.

## Your task

Review the whole Sinew & Steel project at
<https://github.com/BWBrook/sinew-and-steel> (main branch) and tell us what we
have missed. We want an overall view first, then specific, evidenced findings.
State the commit you reviewed.

The book and its tooling were drafted and cross-reviewed by two AI agents
working under the author's direction: Astra (an OpenAI Codex agent) and Fable
(a Claude agent). Their agreement is not independent confirmation. You are the
independent check, so be direct. If you find fewer real problems than the format
below allows, report fewer. Do not pad.

## What the game is

Sinew & Steel is a lean, setting-agnostic tabletop role-playing game:

- a roll-under d20 with five attributes;
- Luck tokens that nudge dice after the roll;
- Stamina for health;
- a 0–5 Pressure fuse whose name and effects change by setting.

Ten skins (setting overlays) recast it, from Neanderthal Europe to the trade
routes between the stars. It will be a free release on DriveThruRPG with no
revenue goal.

It is AI-first. The intended audience is players who want an AI to run the game
or to help a human run it. That can happen in two ways:

- in **chat play**, through a prompt pasted into any capable model;
- in **harness play**, through an agent working in this repository, whose
  command-line tools keep dice, state and secrets honest.

A human table with paper and dice is supported too.

The design is fiction-first:

- It resists min-maxing at character creation and saves extreme characters
  for advancement.
- Trade-offs are meant to bite in the story rather than in the numbers.
- The Custodian (the game master) tunes pacing and can overrule anything.

**Terms.**
- **Custodian:** the game master.
- **Skin:** a setting overlay.
- **Beat:** a scene-scale development; a perilous beat is a dangerous scene.
- **Milestone:** an advancement award.
- **Tag:** a named niche that grants Advantage when the fiction fits.
- **Edge:** a weapon's damage bonus. **Soak:** armour's damage reduction.
- **Nudge:** spending Luck tokens to shift a die, one point per token.

## Where the project stands

These stages are complete:

- a book-wide prose pass with the author;
- a cross-examination of that pass;
- decisions on the game's core numbers;
- alignment of the text to those decisions;
- an overhaul and review of the AI harness.

Next come simulated (AI-run) playtests across skins and party sizes. After them
the rules and writing are frozen as GOLD, and only then is the book laid out.
The author's own human playtests will be few, so they count as indicative only.

Your review comes before the playtests. A concern that needs statistical
evidence, such as whether a number is too harsh, belongs in your playtest
recommendations, not in a rule change.

## Settled decisions

Challenge these only by showing a contradiction, a defect, or a rule that cannot
be applied as written. Disagreeing with the choice is not enough. If you still
believe one is wrong, say what evidence would show it.

**Core resolution**
- Damage is 1 + edge + 1 per full 5 points of margin − soak, minimum 1.
- A natural 1 always succeeds, ignores soak and adds 1 damage. A natural 20
  always fails. Neither can be nudged.
- Opposed ties and double failures go to the defender.

**Character creation and advancement**
- Creation is point-buy around baselines of 10 for attributes and 5 for
  Stamina. The lifetime ceilings are 16 and 9.
- Four budgets: grim, standard, pulp and heroic.
- Tags cost 2 build points.
- Lowering scores refunds at most 8 points in total.
- A milestone comes every 3–4 perilous beats. It brings 2 build points, a
  narrative boon and a full Luck pool.

**Pressure**
- One track is shared by the party. Whispers in the Fog is the exception: each
  investigator has a personal Insanity track.
- Step effects add up.
- A one-test penalty works like this:
  - it fires once on reaching or passing its step;
  - it is discarded if the track falls back below that step;
  - it re-arms only after a crisis.
- Tolls apply only to tests a character chooses to attempt, never to defence.
- When a crisis falls on one character, it falls on whoever tipped the track,
  unless the fiction points elsewhere. It is recorded before the track resets.

**Combat and magic**
- Unless the fiction settles who acts first, each side rolls initiative once
  per fight, then orders its own members each round.
- Twilight of the Northlands' combat positions are held for the whole round.
- Top-tier magic cannot be nudged where a skin says so.

**Text and book**
- The prose voice was set with the author in a completed prose pass. Flag
  errors, ambiguity and inconsistency, not style preferences.
- The book uses Australian/British spelling.
- The Quickstart must print on exactly two facing pages: pages 6–7 of the full
  book, and as a standalone PDF. Any change that lengthens it must say what it
  cuts.
- Layout, typography and art are out of scope until GOLD.

## What to read

1. `manifest.yaml`: the index of rules, skins and prompts.
2. The book, in release order (about 36,000 words):
   - `rules/book/preface.md`
   - `rules/quickstart.md`
   - `rules/book/the_adventurer.md`
   - `rules/core/adventurers_manual.md`
   - `rules/book/the_custodian.md`
   - `rules/core/custodians_almanac.md`
   - `rules/book/customisation.md`
   - `skins/clanfire.md`
   - `rules/scenarios/clanfire_emberfall.md`,
     `clanfire_emberfall_player_handout.md` and
     `clanfire_emberfall_custodian_notes.md`
   - the nine expansion skins in this order:
     1. `iron_and_ruin`
     2. `time_odyssey`
     3. `briar_benedictine`
     4. `rust_and_domes`
     5. `candlelight_dungeons`
     6. `service_duct_blues`
     7. `whispers_in_the_fog`
     8. `free_traders_of_the_drift_marches`
     9. `twilight_of_the_northlands`
   - `rules/book/ai_as_custodian.md`
   - `rules/appendices/ai_play.md`
   - `rules/book/back_cover_blurb.md`
3. The harness:
   - read first: `docs/ai_play_harness.md`, `AGENTS.md`, `skills/` and
     `prompts/`;
   - then `tools/` (about 11,000 lines of Python) and `tests/`;
   - the core modules are `_rules.py`, `_pressure.py`, `_play.py`,
     `_runtime.py`, `play.py`, `advance.py`, `build_prompt.py` and
     `playtest_summary.py`.
4. `PLAN.md`: the living plan, including the triggers for reopening the engine.

`docs/engine_atlas.md` (with `docs/engine_atlas/`) and `docs/independent_engine/`
are analyses of the game's numbers. Treat them as evidence, not as part of the
book, and consult them when judging a numeric claim.

Lower priority: the Candlelight Delvekit (`docs/candlelight_delvekit.md`,
`tools/delvekit_*.py`), the PDF release pipeline and `tools/analysis/`.

Skip `docs/archive/`. Private campaigns are not in the repository.

Keep your view independent. Read `docs/reviews/` and `CHANGELOG.md` only after
you have formed it. Use them only to avoid reporting problems already fixed or
already known. The known open items are listed in
`docs/reviews/2026-10-02-stage4-review.md`. Earlier reviewers' conclusions are
not evidence.

## Lenses

1. **Newcomer and release.**
   - Can someone learn and run the game from the book alone? Where would a
     newcomer stall, misread or have to guess?
   - Does the package (core book, ten skins, starter scenario, AI chapters) hang
     together?
   - Is anything missing that a first release needs?
   - Are there release risks, such as names or content too close to existing
     games, or DriveThruRPG's disclosure rules for AI-generated content?
2. **AI Custodian.**
   - Build a compact prompt with
     `uv run python tools/build_prompt.py --skin clanfire --mode chat`. It holds
     the Quickstart and one skin. Could a capable model run a session correctly
     from it?
   - Which rules is a model most likely to get wrong? Does the prompt carry
     what it needs, and is the cost in prompt length justified?
   - Ask the same of an agent in harness play that follows `AGENTS.md` and
     `skills/`.
3. **Rules consistency.**
   - Contradictions or gaps between the Quickstart, Manual, Almanac,
     Customisation, the scenario and the skins.
   - Skin rules that override the core without saying so.
   - Terms used inconsistently.
   - Worked examples whose numbers do not follow the rules.
4. **Rules against code.**
   - Does the harness enforce what the book says, and nothing the book does not
     say?
   - Look for rules the code adds or omits.
   - Check state integrity, safe retries, and the line between public and
     private output.
5. **Playtest readiness.**
   - Can the reopen triggers in `PLAN.md` be measured from what
     `playtest_summary.py` reports?
   - Are its definitions sound: the session midpoint, the windows spent at
     Pressure step 4, and "more than a few rolls"?
   - What else should the playtests measure?
   - What is the smallest credible programme, in skins, party sizes and
     sessions?

## Running code

If you can run code:

```bash
git clone https://github.com/BWBrook/sinew-and-steel
cd sinew-and-steel
uv sync
uv run python -m unittest discover -s tests -q
uv run python tools/validate_repo.py
```

Python 3.10 or later is needed. Without `uv`, `pip install pyyaml` is enough for
the tests and validation; the optional `pdf` and `analysis` extras are not needed.

Then follow the worked example in `docs/ai_play_harness.md` in a throwaway
campaign called `scratch_demo`. Mark each finding as checked by running code or
by reading. If you cannot run code, say so and review by reading.

## What to return

Return one Markdown document. We will save it in `docs/reviews/`.

1. **Header.** The commit you reviewed; what you read in full, skimmed and
   skipped; and whether you ran code.
2. **Verdict**, in 400 words or fewer. Does the project deliver what it promises
   to its audience? What are the three to five biggest risks to a GOLD release?
3. **Findings**, most severe first, no more than 25 (nits excluded). For each:
   - an ID and a title;
   - severity:
     - **Blocker:** it would mislead play, corrupt state, or invalidate
       playtest evidence.
     - **Major:** a real contradiction, gap or defect that a reader or an AI
       Custodian will hit.
     - **Minor:** a clarity or consistency problem that has a workaround.
   - the lens, 1–5;
   - the location: a file and line, or a chapter and section;
   - the evidence: a short quote of each side for a contradiction, or the
     relevant code;
   - why it matters in play;
   - the smallest fix that works, with concrete wording where it is text;
   - whether it touches a settled decision, and which one;
   - your confidence (high, medium or low), and whether you checked it by
     running code or by reading.
4. **Nits.** Grouped, one line each.
5. **Questions for the author.** Where the intent is unclear, ask rather than
   assume.
6. **Strengths worth keeping.** Briefly: what should not change.
7. **Playtest recommendations.** From lens 5.
