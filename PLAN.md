# Plan

The living plan for Sinew & Steel, set by Barry on 1 October 2026 and recorded on the project board (thread 46, message 787). Finished work is in `CHANGELOG.md`. The old snapshot file is archived at `docs/archive/HANDOVER_2026-09-30.md` and is no longer maintained.

## Stages

1. **Cross-examine the prose-pass revision.** Done: Astra's review is `docs/reviews/2026-10-01-stage1-review.md`.
2. **Decide and implement engine changes with Barry,** informed by the independent engine review (`docs/independent_engine/`), the engine atlas (`docs/engine_atlas.md`) and the Stage 1 review. In progress. Decisions made so far are below.
3. **Align the rules and chapters with those changes,** keeping the narrative voice the prose pass established. Small clarifications found before then go in the tally below rather than being fixed piecemeal.
4. **Overhaul the AI Custodian harness and supporting tools.** A stage of its own, not incidental cleanup. Notes below.

Layout comes last. It waits until the rules and writing are GOLD. Until then, every text change must still keep the Quickstart on exactly two facing pages.

## Stage 2 decisions so far

- 1 October 2026: Pressure step effects add up, as exhaustion does: everything at or below the current step applies while the track stays there. A one-test penalty fires once when the track first reaches or passes its step, and re-arms only after a crisis resets the track. Written into Manual 8 and Almanac 4.
- 1 October 2026: Twilight combat positions are declared at the start of each round and held for every attack and defence that round; the bonus and the drawback come as a bundle. Written into the Twilight skin.
- 1 October 2026: unless the fiction settles who acts first, each side rolls a d20 once, at the start of the fight, and that order holds for the whole fight; each side chooses its own members' order every round. Written into Manual 6 and the Emberfall teaching round.
- 1 October 2026: if Pressure falls below a step, discard any unused one-test penalty from that step. This does not re-arm it; only a crisis resets the cycle. Barry chose "Discard the unused penalty" in the Stage 2 follow-up. Written into Manual 8 and Almanac 4.

The [Stage 2 engine check](docs/reviews/2026-10-01-stage2-engine-check.md) records the evidence against the latest rulings, including corrections to the Twilight analysis. Astra recommends retaining the current engine numbers and creation ledger; any refund cap remains an unadopted alternative, not an outstanding repair. The older atlas's stance-tuning recommendation should be read alongside this later check and the independent review.

## Stage 3 tally

From the Stage 1 review, plus items raised since. Barry decides wherever two readings are possible.

- **Emberfall teaching round:** state the two round essentials (each able combatant acts once per round; defending uses no action). Make a lost intimidation contest mean the wolf holds its ground and takes its normal turn, not an extra bite or drag (Fable's proposal, not yet ruled). Distinguish dragging on a loss from the wolf's margin-4 hook.
- **Emberfall and Custodian Notes:** make the closing question conditional on it still being unanswered; otherwise close on the next question play created.
- **Quickstart:** define "perilous beats" as dangerous scenes, within the two-page limit.
- **The Custodian:** say whether the failure-consequence choice is made before the roll (as declared stakes) or only elaborates them afterwards.
- **The Adventurer:** distinguish thinking and clarifying from stalling in the fiction; "plainly plausible" does not by itself remove uncertainty.
- **Almanac:** "stops power creep" overstates what the ledger proves; 10 + stat is a rough 2d6 character translation, not a probability conversion.
- **Tipper rule:** add a short example for group checks and ambient gains, where no single action tipped the track (for example, the Custodian names the first to fail). Also show what happens to Pressure gained during a crisis: resolve, then reset.
- **Pressure recovery:** illustrate discarding unused step penalties below their threshold without re-arming them. A crisis reset clears old step penalties but leaves consequences created by that crisis to run for their stated duration. Each named recipient uses their own next-test penalty, even when Advantage cancels it.
- **Free Traders:** larger Hull clocks still disable the drive at 6; use the clock's filled threshold.
- **Twilight travel:** state whether a failed Scout test gives its hazard instead of, or as well as, generic travel Fatigue.
- **Twilight knacks:** "Costs are personal" now sits beside shared Dread; say instead that Hope is personal and Dread is the company's, and neither is paid from Companionship.
- **Twilight Healing Rest:** the paragraph clears Injury, but the undertakings table does not; add it to the row.

## Stage 4 notes

- The harness predates the 0.4.0 and prose-pass rulings throughout. Check sheets, validators, `gen_character.py` and `build_prompt.py` against them: Pressure off character statlines, no bought tags at the grim budget, the M-field sensitive tag, personal Insanity in Whispers, and step-effect accumulation.
- `campaign_init.py` sets up one shared Pressure clock, but Whispers needs one Insanity clock per investigator. `trackers.py clock` already handles named clocks.
- Stage 1 suggests logging Pressure events by source in play, so pacing can be judged by event counts rather than normalised by party size.
- Track pending one-test penalties per affected character and which thresholds have fired since the last crisis. Recovery discards unused penalties below their thresholds without re-arming them; crisis reset clears old step penalties and starts a new cycle. Keep crisis-created consequences separate from these step penalties.
