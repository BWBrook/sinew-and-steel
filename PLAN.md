# Plan

The living plan for Sinew & Steel, set by Barry on 1 October 2026 and recorded on the project board (thread 46, message 787). Finished work is in `CHANGELOG.md`. The old snapshot file is archived at `docs/archive/HANDOVER_2026-09-30.md` and is no longer maintained.

## Stages

1. **Cross-examine the prose-pass revision.** Done: Astra's review is `docs/reviews/2026-10-01-stage1-review.md`.
2. **Decide and implement engine changes with Barry.** Closed on 1 October 2026; decisions below. The evidence is the independent engine review (`docs/independent_engine/`), the engine atlas (`docs/engine_atlas.md`), and the Stage 1 review and Stage 2 engine check (`docs/reviews/`).
3. **Align the rules and chapters with those changes,** keeping the narrative voice the prose pass established. Fable implemented it on 1 October 2026; Astra reviewed and signed off the changes at `14b6544` on the same day. The changes are listed below.
4. **Overhaul the AI Custodian harness and supporting tools.** A stage of its own, not incidental cleanup. Astra takes the first pass and Fable reviews and critiques it. Notes below.

After Stage 4 come simulated playtests: AI-run sessions across several skins and party sizes, logged well enough to test the reopen triggers below. Barry's human sessions will add an indicative trickle ("more vibes than distributional probabilities"). Then the rules and writing are declared GOLD, and only then comes layout. Until then, every text change must still keep the Quickstart on exactly two facing pages.

## Stage 2 decisions

The engine numbers stay: damage, soak, margin steps, natural results, Luck, and the Twilight stance values. The atlas's older stance-tuning recommendation is superseded by the Stage 2 engine check. The decisions, all made on 1 October 2026:

- **Pressure steps add up,** as exhaustion does: everything at or below the current step applies while the track stays there. A one-test penalty fires once when the track first reaches or passes its step, and re-arms only after a crisis resets the track. If the track falls below that step, discard any unused penalty from it (Barry: "Discard the unused penalty"). Manual 8, Almanac 4.
- **Twilight combat positions** are declared at the start of each round and held for every attack and defence that round; the bonus and the drawback come as a bundle. Twilight skin.
- **Initiative:** unless the fiction settles who acts first, each side rolls a d20 once, at the start of the fight, and that order holds for the whole fight; each side chooses its own members' order every round. Manual 6, Emberfall.
- **Refund cap:** lowering scores below baseline pays back at most 8 build points in total. In Barry's words, it works "to further de-emphasise min-maxxing… Initial specialisation can only go so far, after that, milestones are required to get more extremes out of the characters, and the Custodian can ultimately overrule anything." A 16 with Stamina 9 now needs the pulp budget, and no attribute starts above 14 on the grim budget. The Almanac's Iron Brute was rebuilt to fit; every other sample build already did. Manual 2.2 and 2.4, Quickstart, Almanac Part I and the tone dial, Customisation; the ledger, generator and tests enforce it.
- **Pressure and party size:** Barry: "real play will sit somewhere in between, and can be 'tuned' [by] the Custodian if required." The Almanac now tells Custodians that a bigger party fills the fuse faster, and how to slow it: charge shared hazards once per beat for the whole party, or purge more generously.

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

## Stage 4 notes

- The harness predates the 0.4.0 and prose-pass rulings throughout. Check sheets, validators, `gen_character.py` and `build_prompt.py` against them: Pressure off character statlines, no bought tags at the grim budget, the M-field sensitive tag, personal Insanity in Whispers, and step-effect accumulation. The refund cap is already enforced: `_sslib.REFUND_CAP`, a generator limit of 4 trade-off steps, and a regression test.
- `campaign_init.py` sets up one shared Pressure clock, but Whispers needs one Insanity clock per investigator. `trackers.py clock` already handles named clocks.
- Track pending one-test penalties per affected character and which thresholds have fired since the last crisis. Recovery discards unused penalties below their thresholds without re-arming them; a crisis reset clears old step penalties and starts a new cycle. Keep crisis-created consequences separate from these step penalties.
- Build the playtest logging above into the harness, so that simulated sessions can test the reopen triggers.
- The creation-economy outputs in the analysis tools (the atlas and the independent review's enumeration) still assume the uncapped ledger; rerun or relabel them.
- Keep advancement expenditure separately from the current sheet's creation price. For example, the pulp build `[16,6,6,6,8]`, Stamina 9 costs 12 creation points both before and after raising one 6 to 7, because its reductions still exceed the refund cap; that advancement nevertheless costs 1 point. A state-only recalculation must not erase the expenditure.
