# Stage 4 harness review

Fable's critique of Astra's Stage 4 implementation (`7f595b9`), 1–2 October
2026, following the handoff in `2026-10-01-stage4-harness.md` and board thread
46, message 806. The fixes sit in one change set on top of that commit; Astra's
work is otherwise unchanged.

## Verdict

The architecture is sound and the core holds: the rules module, the Pressure
state machine, the write-ahead journal and the receipts did what the handoff
claims under adversarial sequences. The defects found were at the edges: one
rules mismatch the author then ruled on, a missing manifest step, gaps in the
combat and session boundaries, crash recovery for read-only tools, and a
playtest metric that counted one scene too many. All are fixed below with
regression tests. Nothing found argues for reopening the engine.

## Method

1. Executable book examples (`test_book_examples.py`) read against the current
   Manual, Quickstart, Almanac and Emberfall text.
2. The manifest's Pressure translations checked step by step against all ten
   skins.
3. About 50 adversarial CLI sequences in temporary campaigns: Pressure climbs,
   jumps, discards and crises; Luck targets and nudges; damage at the margins;
   combat order, positions and turn use; Whispers personal tracks; Candlelight
   incoming Advantage; Rust & Domes Heat 4; Twilight Injury and Deflection;
   Companionship; advancement under the refund cap; session open and close;
   summaries and resume packs.
4. A separate code-level review of the runtime, readers and helpers.
5. The documented CLI flow, command by command, against each tool's argparse.

## Author ruling

Barry, 2 October 2026: "Agreed, tolls only on tests a character attempts, not
defence. It was never intended to be involuntarily sapped like that!"

The harness had let a defender pay a Pressure toll (`--defender-toll`) and
charged a toll on Deflection. Tolls and step costs now fall only on the
character attempting a test; step penalties still apply to defence and
Deflection rolls. Manual 8, Almanac 4, the six skins with tolls, the manifest
labels and the harness agree, and the two flags are gone.

## Defects fixed

| Area | Defect | Fix |
|---|---|---|
| Tolls | A defender or a Deflection roll could pay a toll. | Only the acting character pays (ruling above). |
| Manifest | Iron & Ruin's step 4 ("Veil thins") was missing. | Added as a Custodian lever; `_pressure.modifiers()` reports levers from their step. |
| Weapons | Edge above +2 was rejected, though a boon or Heroic Act can lift it. | Edge and soak must be nonnegative integers; skins that cap edge say so. |
| Magic | No way to mark top-tier magic as unnudgeable. | `--no-nudge` on check, opposed and attack refuses nudges to the caster's die at settlement. |
| Combat | An opposed test by a combatant did not use their action, so they could also attack. | It now uses the combatant's action. |
| Sessions | `session-close` was allowed mid-combat. | Refused until `combat-end`. |
| Sessions | A new session's memory file dropped open threads, NPCs and secrets. | They carry over; the summary starts empty. |
| Names | Character names, sheet files and resources matched case-sensitively; resources only by ID. | Case-insensitive names and stems on every filesystem; resources by ID or display name. |
| Crash recovery | After an interrupted transaction, resume packs, summaries, prompts and validation read torn state, and the dry-run error told the user to run a writing command. | Readers refuse until recovery; `play.py status` recovers (and otherwise writes nothing); validation reports the journal alone. |
| Event IDs | IDs were case-sensitive on Linux but not macOS, and an ID could replay a receipt from an earlier session. | IDs are case-insensitive everywhere; receipts record their session, and reuse from another session is refused. |
| Telemetry | `str.splitlines()` split JSONL on U+2028 inside a label, making the log unreadable. | Split on newlines only. |
| Output | A date in a sheet crashed JSON output; non-ASCII names were written as YAML escapes. | `default=str` on JSON output; `allow_unicode` on every YAML dump. |
| Advancement | Raising Luck at a milestone left the pool one token short of the new score. | The raise adds the token, so the pool ends full, as Manual 3 says. |
| Privacy | The public resume pack exported free-form condition keys, which can hold GM secrets. | Public exports omit conditions; private packs keep full sheets. |
| Paths | An absolute character path outside the campaign was accepted. | Absolute paths must sit inside the campaign's characters folder. |
| Permissions | Campaign prompts, which hold hidden notes and private state, and a new campaign's first state files were written 0644; later state writes were 0600. | Both are written owner-only (0600). |
| Summary | "Outstanding effects" counted lasting effects already ended. | Counts active effects only. |
| Playtest metric | The midpoint cut by beat number, so the first half included the scene after the midpoint beat. | The cut is the sequence number of the last beat record at or below the midpoint. |
| Validation | The demo prompt's freshness was not checked by repository validation; a hard-coded total of 20 samples duplicated the per-skin check. | Freshness is checked; the total is replaced by a guard against an empty parse. |
| Dead code | Unused path-editing helpers remained in `_sslib.py`. | Removed. |
| Prompts | A `--full` prompt still told the model to fetch sections and rebuild with `--full`. | It says both books are included. |
| Prompts | Prompt state escaped non-ASCII text and folded multi-line text. | Multi-line strings print as literal blocks with real characters. |

A command-by-command audit of the documentation, each sequence re-run in a
scratch campaign, made 17 fixes across `AGENTS.md`, the README, `tools/README.md`,
the harness guide, the command snippets, the agent prompts, eleven skills, the
`state/` READMEs and the skin template. Examples now use a throwaway slug,
`scratch_demo`, rather than real-sounding campaign names. The docs say that any
play action, checkpoint or advancement makes the saved prompt stale, so rebuild it
(with the same options) before validating or resuming. They also cover combat turn
use, when characters may join, advancing only while a session is open, the
`--no-nudge` tiers, resource IDs, the `resource` and `condition` commands, and
crash recovery. The public resume example no longer promises a log entry, and the
skin template gives the sample-character format that validation prices.

## Checked and unchanged

Score limits, creation pricing under the refund cap, advancement costs,
natural results, nudges, opposed ties, damage, initiative, positions, Injury,
the Pressure lifecycle (accumulation, firing, cancellation, discard without
re-arming, the tipper, atomic crisis reset, separate lasting effects), Whispers
isolation, resource limits and boundary resets, receipts and retries, rollback
after a failed write, migration (a preview writes nothing, incomplete assertions
and re-runs are refused, originals are backed up, the first migrated session
stays partial), and the public export allowlist otherwise. The stale-prompt gate in `validate_campaign.py` stays an error, as
Astra intended; the docs now say to rebuild the prompt first.

## Follow-ups, not fixed

- A retire or death path for roster changes mid-campaign.
- Whether `--event-id` should be required for agent callers.
- Checkpoints are written outside the campaign lock.
- Rewriting YAML drops comments; legacy `.yml` handling is still scattered.
- A defender's roll event carries the attacker's method, which skews per-character
  method shares; the red-line roll threshold is a fixed count whatever the session length.
- Creation snapshots are priced once; a future rules change would need a repricing step.
- `new_skin.py --register` reformats the whole manifest.

## Verification

158 tests pass, 15 of them new for these fixes. Repository validation passes,
including the demo prompt's freshness and the pricing of every published sample,
and `git diff --check` is clean. The Quickstart is untouched. No private campaign
was read or run.
