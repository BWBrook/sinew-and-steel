# Tools

Run from the repository root with `uv run python tools/<tool>.py`. Setup is
`uv sync`; the local harness uses Python and PyYAML. Campaigns live under
`campaigns/` and remain private and untracked.

`play.py` is the campaign engine. It commits sheets, trackers, structured events,
and a receipt together. Use `--dry-run --json` to inspect a proposed action and
`--seed N` for reproducible dice. A stable `--event-id` makes retries return the
saved receipt; reuse it only for the same request in the same session. After an
interrupted write, run `play.py --campaign <slug> status` to restore the campaign;
the read-only tools refuse it until then. Read deferred dice before
choosing Luck expenditure. See [the worked workflow](../docs/ai_play_harness.md)
for combat, Pressure, recovery, and session boundaries.

| Work | Tools |
|---|---|
| New campaign and characters | `campaign_init.py`, `char_builder.py`, `gen_character.py` |
| Mechanical state and rolls | `play.py`; `roll.py` is a stateless dice calculator |
| Milestones and purchases | `advance.py`; `recalc_sheet.py` verifies recorded history and derived pool metadata |
| Prompts and resumes | `build_prompt.py`, `resume_pack.py`, `summary.py` |
| Public narration and exact checkpoint | `session_log.py`, `checkpoint.py` |
| Private memory and sheet metadata | `recap.py`, `update_sheet.py` |
| Checks and playtest evidence | `validate_sheet.py`, `validate_campaign.py`, `validate_repo.py`, `validate_examples.py`, `doctor.py`, `playtest_summary.py` |
| Explicit legacy adoption | `migrate_campaign.py` (preview by default; backs up original files before applying) |

`play.py` runs every campaign command (checks, Pressure, clocks, beats and acts,
sessions, and `retire` for a character leaving play between sessions);
`trackers.py` is an alias for it, and `new_session.py` is shorthand for
`play.py session` that accepts `--campaign` and `--label`. `recap.py` changes memory
only. `update_sheet.py` edits metadata (name, player, notes, inventory), not
attributes, pools, advancement, or mechanical trackers. Use `ss.py <command> ...` as
a short dispatcher if preferred. Every tool and subcommand has `--help`.

Any play action, checkpoint, or advancement makes a saved campaign prompt stale by
design, and `validate_campaign.py` treats a stale prompt as an error. Rebuild the
prompt, with the same `--mode`, `--full`, and `--hidden` options as before, before
validating or resuming.

```bash
uv run python tools/campaign_init.py --slug scratch_demo --skin clanfire \
  --tone standard --random-character Grak --seed 42 --dry-run --json
# Remove --dry-run to create the reviewed scaffold.
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/build_prompt.py --campaign scratch_demo --check --json
uv run python tools/build_prompt.py --section manual:6

uv run python tools/play.py --campaign scratch_demo --character grak --seed 42 \
  --event-id ridge-test check --attribute FLT --method "Cross the icy ridge" \
  --stakes "Reach shelter; failure costs time and adds Shadow" --failure-pressure 1 --defer
# Read the saved dice, then settle without rerolling; add a legal --nudge if chosen.
uv run python tools/play.py --campaign scratch_demo --event-id ridge-settle settle

uv run python tools/advance.py --campaign scratch_demo --character grak \
  --event-id milestone-one award --id ridge --boon "A safe refuge"
uv run python tools/advance.py --campaign scratch_demo --character grak show --json
# Play and advancement made the saved prompt stale: rebuild before validating or resuming.
uv run python tools/build_prompt.py --campaign scratch_demo
uv run python tools/validate_campaign.py --campaign scratch_demo
uv run python tools/resume_pack.py --campaign scratch_demo --public --json
```

New sheets record an immutable creation snapshot and separate advancement entries.
Raises cost 1 point while below baseline and 2 at or above it; creation refunds
are capped at 8 across all scores. Bought tags cost 2 and cannot be funded by
unused refunds. Use `--free-tag GRANT=NAME` for an explicit skin grant. The caps
remain attributes 16 and Stamina 9. See [character build](../skills/character_build.md).

For publishing and dungeon authoring, use `release_build.py`, `md_pdf.py`,
`layout_lab.py`, `new_skin.py`, and the `delvekit_*.py` tools. Their workflows are
in [PDF building](../docs/pdf_building.md), the [Delvekit guide](../docs/candlelight_delvekit.md),
the [layout lab](../examples/layout_lab/README.md), and the [editor notes](../skills/editor_notes.md)
(new skins).
