# Plan

The living plan for Sinew & Steel, set by Barry on 1 October 2026 and recorded on the project board (thread 46, message 787). Finished work is in `CHANGELOG.md`. The old snapshot file is archived at `docs/archive/HANDOVER_2026-09-30.md` and is no longer maintained.

## Stages

1. **Cross-examine the prose-pass revision.** Done: Astra's review is `docs/reviews/2026-10-01-stage1-review.md`.
2. **Decide and implement engine changes with Barry.** Closed on 1 October 2026; decisions below. The evidence is the independent engine review (`docs/independent_engine/`), the engine atlas (`docs/engine_atlas.md`), and the Stage 1 review and Stage 2 engine check (`docs/reviews/`).
3. **Align the rules and chapters with those changes,** keeping the narrative voice the prose pass established. Fable implemented it on 1 October 2026; Astra reviewed and signed off the changes at `14b6544` on the same day. The changes are listed below.
4. **Overhaul the AI Custodian harness and supporting tools.** Astra's implementation is ready for Fable's review and fixes. The handoff is `docs/reviews/2026-10-01-stage4-harness.md`; this stage is not signed off yet.

After Stage 4 come simulated playtests: AI-run sessions across several skins and party sizes, logged well enough to test the reopen triggers below. Barry's human sessions will add an indicative trickle ("more vibes than distributional probabilities"). Then the rules and writing are declared GOLD, and only then comes layout. Until then, every text change must still keep the Quickstart on exactly two facing pages.

## Stage 2 decisions

The engine numbers stay: damage, soak, margin steps, natural results, Luck, and the Twilight stance values. The atlas's older stance-tuning recommendation is superseded by the Stage 2 engine check. The decisions, all made on 1 October 2026:

- **Pressure steps add up,** as exhaustion does: everything at or below the current step applies while the track stays there. A one-test penalty fires once when the track first reaches or passes its step, and re-arms only after a crisis resets the track. If the track falls below that step, discard any unused penalty from it (Barry: "Discard the unused penalty"). Manual 8, Almanac 4.
- **Twilight combat positions** are declared at the start of each round and held for every attack and defence that round; the bonus and the drawback come as a bundle. Twilight skin.
- **Initiative:** unless the fiction settles who acts first, each side rolls a d20 once, at the start of the fight, and that order holds for the whole fight; each side chooses its own members' order every round. Manual 6, Emberfall.
- **Refund cap:** lowering scores below baseline pays back at most 8 build points in total. In Barry's words, it works "to further de-emphasise min-maxxing… Initial specialisation can only go so far, after that, milestones are required to get more extremes out of the characters, and the Custodian can ultimately overrule anything." A 16 with Stamina 9 now needs the pulp budget, and no attribute starts above 14 on the grim budget. The Almanac's Iron Brute was rebuilt to fit; every other sample build already did. Manual 2.2 and 2.4, Quickstart, Almanac Part I and the tone dial, Customisation; the ledger, generator and tests enforce it.
- **Pressure and party size:** Barry: "real play will sit somewhere in between, and can be 'tuned' [by] the Custodian if required." The Almanac now tells Custodians that a bigger party fills the fuse faster, and how to slow it: charge shared hazards once per beat for the whole party, or purge more generously.
- **Tolls fall on choices** (2 October 2026, during the Stage 4 review): Pressure tolls and step costs apply only to tests a character attempts, never to a defence or Deflection roll; step penalties still apply to those rolls. Barry: "It was never intended to be involuntarily sapped like that!" Manual 8, Almanac 4, the six skins with tolls, the manifest labels and the harness (the defender and Deflection toll flags are gone).

### Reopen triggers for the simulated playtests

- **Luck:** if characters routinely drop to 1 token or fewer by mid-session, revisit rest recovery.
- **Red line:** if step-4 windows routinely last more than a few rolls, revisit the step-4 effects.

The playtest logs should record the attribute and method behind each roll, Pressure gains by source, Luck spent and recovered, and each crisis with its target.

## Stage 3 changes, signed off

Implemented by Fable on 1 October 2026, from the Stage 1 tally. Items marked "choice" took one reading where two were possible; Astra's review accepted these readings.

- **Emberfall teaching round:** states the round essentials (each able combatant acts once per round; defending uses no action). Choice: a lost intimidation contest lets the wolf hold its ground, with no extra action; on its turn it attacks Tarra or snatches the meat. Choice: the wolf's drag hook needs an attack won by a margin of 4 or more, not a successful dodge.
- **Emberfall and Custodian Notes:** the closing question applies only if play has not answered it; otherwise close on the question play created.
- **Quickstart:** "perilous beats (dangerous scenes)"; checked in both the full book and the standalone PDF.
- **The Custodian:** choice: the failure consequence is chosen before the roll, as part of the stated stakes. When two fit, name both, and if the roll fails let a d6 pick between them; the failure adds detail, not new costs.
- **The Adventurer:** thinking aloud is fine and only stalling costs time; a roll-free outcome needs no real chance of failure, or no interesting cost.
- **Almanac:** power creep is "kept in check", not stopped, and the d20 step is "on an ordinary roll"; 10 + stat is a rough character translation for 2d6 games, not a probability match.
- **Tipper rule (Manual 8, Almanac 4):** when no single action tipped the track, the Custodian names the character the fiction points to. A worked example in Almanac 4 (Free Traders' Strain) covers group gains, per-character next-test penalties (spent even when Advantage cancels them), discarding on recovery, no re-firing, crisis effects outlasting the reset, and Pressure gained during a crisis being wiped by it.
- **Free Traders:** a ship's drive fails when its own Hull Damage clock fills, so larger clocks work.
- **Twilight travel:** choice: a failed role test takes the role's own failure instead of the general travel Fatigue.
- **Twilight knacks:** Hope comes from your own pool and Dread lands on the company's track; neither comes from Companionship.
- **Twilight Healing Rest:** the undertakings table now clears Injury too.

Astra's closeout check passed all 31 tests and repository validation. Independent pricing checked 2,600 generated characters across all ten skins and four budgets, plus every published sample. The saved book and Quickstart assemblies match the current sources; PDF inspection confirms two standalone Quickstart pages and full-book pages 6-7. The older uncapped analyses are explicitly labelled historical pending Stage 4 refresh.

## Stage 4 implementation and review

Implemented on 1–2 October 2026. Detailed contracts, verification and remaining
Custodian judgments are in `docs/reviews/2026-10-01-stage4-harness.md`.

- Shared rules code, with executable book examples and automatic pricing of all
  20 skin samples. The Quickstart's two-page spread is a release check.
- Schema-2 Pressure state: party scope except personal Insanity in Whispers;
  fired thresholds, per-character pending penalties, discard without re-arming,
  atomic crisis reset, and separate lasting effects.
- Immutable creation snapshots and replayable advancement entries. The pulp
  `[16,6,6,6,8]`, Stamina 9 example now retains its 1-point advancement charge
  when a 6 becomes 7 even though the capped creation price remains 12.
- Atomic campaign actions and receipts, deferred Luck decisions, attack/damage
  resolution, fixed side initiative, Twilight positions and optional Injury,
  manifest-defined resource bookkeeping, and explicit backed-up migration.
- Structured session logs and a descriptive summariser for the reopen triggers.
  Completed sessions are kept separate from unfinished or migrated partial
  histories; roster changes occur between logged sessions.
- Compact prompts, on-demand rules sections, stale-prompt checks, safe public
  exports, and updated CLI documentation/skills. Private campaigns remain in
  their existing format until explicitly migrated.
- Historical creation-economy scripts and outputs are labelled as uncapped;
  the expensive analyses have not been rerun.

Fable's review (2 October 2026, `docs/reviews/2026-10-02-stage4-review.md`) found
the core sound and fixed the defects at its edges. Defence and Deflection no longer
pay tolls (author ruling above), and Iron & Ruin's missing step 4 is restored as a
Custodian lever. Edge may exceed +2, top-tier magic can be marked `--no-nudge`, and
an opposed test uses a combatant's action. A session cannot close mid-combat, and a
new session carries open threads, NPCs and secrets. Read-only tools refuse torn
state until `play.py status` recovers it. Event IDs are case-insensitive and
session-bound. A milestone Luck raise leaves a full pool, and the playtest midpoint
no longer counts the scene after its beat. The documentation was audited command by
command. 158 tests pass. Follow-ups that were noted but not fixed are listed in the
review.

Next: Barry signs off Stage 4. Then run the planned simulated sessions across skins
and party sizes. Harness tests do not replace those playtests or authorize GOLD and
layout.
