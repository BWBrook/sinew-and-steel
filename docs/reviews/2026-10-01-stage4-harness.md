# Stage 4 harness implementation

Implemented by Astra on 1–2 October 2026 from the signed-off Stage 3 baseline `0a7eb23`, following
Barry's instruction to lead the overhaul and Fable's preparation in board thread
46, message 800. This is the implementation handoff for Fable's critique and fixes.
Stage 4 review, simulated playtests, and GOLD remain separate gates in `PLAN.md`.

## What changed

| Requirement | Implementation |
|---|---|
| One enforced rules core | `_rules.py` owns score limits, creation pricing, advancement costs, check/opposed resolution, natural results, nudges, and damage. `_dice.py` supplies draws. `_pressure.py` owns the pure Pressure state transitions; CLIs use these shared operations. |
| Published examples as executable claims | `test_book_examples.py` reads the current Manual, Quickstart, Almanac and Emberfall examples. `validate_examples.py`, also called by repository validation, parses and prices all 20 published skin characters. |
| Structured Pressure | Schema-2 trackers hold scope, cycle, fired steps, per-character pending penalties, crisis targets and lasting effects. Whispers creates personal Insanity tracks; the other nine skins share a party track. |
| Separate advancement history | Sheets retain an immutable creation snapshot and replay ordered milestone, raise and tag purchases. Recalculation cannot erase spending hidden by the creation refund cap. |
| Session evidence | Atomic JSONL events record methods, attributes, dice, modifier sources, costs, Luck recovery, Pressure sources, crises and narrative beats. `playtest_summary.py` separates skins, party sizes and completed/incomplete sessions. |
| Attacks and combat | `play.py` resolves opposed attacks, damage and Stamina together; records side initiative once; holds Twilight positions for a round; and supports optional Injury with separately persisted Deflection dice. |
| Skin bookkeeping | Manifest-defined pools, use limits, free grants and named clocks scaffold and validate for every skin. Limits reset at the relevant scene, session, port or camp boundary. |
| Headless operation | Seeded draws, dry-runs, JSON results, stable event IDs, campaign locking and rollback transactions support repeatable callers and safe retries. |
| Prompt economy | Compact prompts combine Quickstart, skin, state and hidden material; detailed sections can be fetched on demand. Fingerprints detect changed sources, state inventory or saved prompt text. |
| Clear tool boundaries | Removed `beat.py` and `apply_roll.py`; `trackers.py` and `new_session.py` delegate to the runtime. `recap.py` writes memory only; `update_sheet.py` edits descriptive fields. Character creation, generation and ledger replay retain distinct jobs. |
| Public/private separation | Public resume/summary exports use an explicit field allowlist and preserve the exact public checkpoint. Hidden notes, clocks, logs, metadata and local paths stay private. |

The tracked demo, templates and seed fixtures use the new schema, and the CLI
guide, skills and agent instructions describe the new workflow. Existing private
campaigns were not migrated. Historical creation-economy analyses are labelled
as uncapped evidence; this implementation does not rerun those simulations or
present their creation frontiers as current.

## State and session contracts

An action snapshots Pressure before upfront costs, consumes applicable pending
penalties even when Advantage cancels them, and retains raw dice until settlement.
Lowering Pressure discards unused penalties below their step without re-arming
them. A recorded crisis resets its track and cycle together; lasting consequences
remain separate until explicitly ended.

Raw Deflection is a second persisted stage. Failed or unaffordable settlement
leaves those dice pending; retrying cannot obtain a new roll. A stable event ID
returns the original receipt without a second charge, roll or event. Reusing an
ID for a different request fails. A write-ahead journal restores all affected
campaign files together after a failed write or before the next writing command
following an interrupted transaction.

Create characters before the first logged action, or after closing a session and
before opening the next. Each session then has one party-size stratum. Adding a
character preserves existing Pressure and use counters, changes shared capacity
without refilling spent tokens, and leaves completed telemetry unchanged.

Legacy migration is explicit and previewed by default. The user supplies reviewed
Pressure/resource state or asserts a known fresh state. Unadvanced legacy sheets
can adopt a creation snapshot only with that assertion; ambiguous advancement is
rejected. Applied migration backs up original YAML and retains prior session
evidence. No inference reconstructs missing play history.
The first migrated session is explicitly partial; only a subsequent session can
enter the summary's completed-session evidence.

## Verification

The complete `uv run python -m unittest discover -s tests -v` suite passed
143 tests at implementation closeout. Repository validation, automatic pricing
of all 20 skin samples, demo campaign validation and the demo prompt's freshness
check passed. `git diff --check` was clean.

Ten temporary campaigns, one for each skin, also passed a real CLI workflow:
seeded creation, prompt assembly, a deferred check and settlement, idempotent
retry, a jump to crisis and recorded reset, two narrative beats, session closure,
summary generation, stale-prompt detection and regeneration. These were mechanical
smoke fixtures, not the planned AI-run playtest programme. All smoke state was
temporary.

The regression cases include cancellation and consumption of one-test penalties,
crossing several steps, discard without re-firing, crisis gains wiped by reset,
personal Insanity isolation, capped creation versus advancement expenditure,
tag grants, round-long positions, initiative, natural results, current-Luck
targets, resource limits, deterministic settlement, retry receipts, failed writes,
private export canaries, prompt freshness, and legacy state boundaries.

The release pipeline now rejects a standalone Quickstart other than two pages,
or a full book where it is not pages 6–7 followed by The Adventurer on page 8.
This is a release gate; it is not a new book-layout pass.
A fresh standalone Quickstart PDF passed the gate at two pages. The saved screen
and print full books each passed at 117 pages with Quickstart pages 6–7. The rule
and skin Markdown has no diff from the signed-off baseline, so those full books
were checked without another complete render. The fresh build used
`tools/release_build.py --bundle quickstart --pdf --json --out-dir <temporary-dir>`.

## What the Custodian still decides

- Whether a roll is needed; which attribute, contexts and tags fit; the declared
  stakes; and any modifiers based on the fiction. Method strings are labels,
  not an automatic classifier of spells or actions.
- Ability eligibility, prose-specific effects, restrictions on nudging particular
  magic, and any success-only costs. The harness records declared costs and use
  limits; it does not grant every ability whose counter exists.
- Crisis table choices, target when no individual tipped the track, and the
  duration and application of lasting consequences. Store their descriptions and
  durations, apply their modifiers when relevant, then explicitly end them.
- Recovery permission and pacing. A scene, camp, port or session boundary resets
  its use limits; it does not silently refill Luck, Stamina, Pressure or pools.

These decisions remain visible in the workflow instead of being inferred from
unstructured prose. The tool records the arithmetic and state once adjudicated.

## Playtest interpretation and follow-on review

The summary uses recorded beat numbers: midpoint is half the last recorded beat,
rounded down. Without beats, midpoint and beat-rate metrics are unavailable.
Low-Luck observations distinguish initially low pools from pools that newly reach
1 or less. Red-line windows count affected PC rolls, use Pressure at action start,
and remain censored at missing boundaries or session end. More than three affected
rolls is the configurable reporting default for “a few”, not a new rule or a
decision to reopen the engine. Sessions and characters are descriptive repeated
observations, not independent empirical samples.

Fable should start with the executable book examples, then the adversarial state
sequences and full CLI workflow. Particular review targets are the manifest's
translation of Pressure conditions, declared versus automatically charged costs,
schema migration, public exports, and the definitions of the reopening metrics.
Simulated multi-skin sessions follow that review; tests of the harness are not
evidence that the settled engine needs changing.
