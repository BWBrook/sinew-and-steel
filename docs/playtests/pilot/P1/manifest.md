# P1 manifest

| Field | Value |
|---|---|
| Run | P1, pilot protocol revision 2 |
| Rules commit | `b89ad90` |
| Skin | Clanfire |
| Scenario | Emberfall as published (`rules/scenarios/clanfire_emberfall_hidden.md` at `b89ad90`, copied unchanged to the campaign's `hidden_scenario.md`; frozen copy kept in the run folder) |
| Modules | none |
| Orchestrator | Fable (`claude-opus-5-5`), not seated |
| Custodian | one subagent, `claude-sonnet-5-5`, Claude Code general-purpose agent, default settings (no temperature control is exposed) |
| Players | one subagent per character, `claude-sonnet-5-5`, same settings |
| Master seed | 101 (draw N uses seed 101000+N; 14 draws used, 101001–101014) |
| Access | instructed, not enforced |
| Date | 3 October 2026, 07:41–08:05 UTC (about 23 minutes) |
| Outcome | complete: 10 beats, 2 acts, session closed |

## Roster

Emberfall's pregenerated pair, built with `char_builder.py` as in `examples/command_snippets.md`:

- **Grak of Tall Cliffs (Hunter):** MGT 12, FLT 10, CUN 10, SPR 8, INS 8, STM 7. Tag: Megafauna tracker. Stone spear +1, hand-axe +1, hide cloak (soak 1), ochre pouch, sinew cord.
- **Tarra the Ember-Singer (Shaman):** MGT 6, FLT 8, CUN 12, SPR 14, INS 11, STM 3. Bone flute (Advantage when calming beasts), fire-bow drill, herb bundle, scrap of southern cloth.

The sheets' inventory lists were empty. The loadouts reached play through the Emberfall handout in each packet, and the Custodian used them from its prompt.

## Access

The Custodian ran tools and read files in the repository. The players were told to read their packet file once with the Read tool and then use no tools; each player agent made exactly one tool call (the packet read) across the run. The packets (`playtests/runs/P1/packet_*.md`, about 6,000 words) held the Quickstart, The Adventurer, the Adventurer's Manual, Clanfire's player-facing lines 1–91 with the example clansfolk, the Emberfall handout and the character's public export.

**Deviation from the protocol:** the protocol says players receive the packet as text. Here they read a file once, which spared about 6,000 words per relay message but needed one tool call. Players who were not addressed by a reply (a Luck decision for the other character) received it batched with the next reply addressed to them.

## Custodian policies

- **Luck tests:** none called.
- **Purges:** none occurred.
- **Shared hazards:** none occurred. The pack's rush, had it come, was planned as a group combat.
- **Shadow from the parley:** one +1 for the whole contact with the Ysre, not one per roll.

## Interventions

Every orchestrator message to the Custodian other than a relay. Rules rulings were never corrected; three messages went beyond format and pacing, and they are marked.

1. After C1, a format note:
   - put public text between `=== PUBLIC ===` and `=== END PUBLIC ===`;
   - Shadow is public in this game, so mentioning it is fine;
   - **beyond format:** "Adjudicate now: state stakes, roll with --defer as needed, show the dice, and offer Luck to whoever can act on it."
2. After C2, **beyond format:** "when a roll could be changed by a bead, roll with --defer, show the dice, and ask the relevant player for the Luck decision before settling."
3. After C3, a pacing reminder: about ten beats over two acts, with an act break after roughly 4–6 beats.
4. After C5 (round 1), a procedure note: resolve the two combat actions in a sensible order, deferring and asking one player at a time.
5. After C7, a pacing reminder that included a suggestion that the scene can cut forward in time.
6. After C8, a note that the players had made different plans.
7. After C9, **beyond format:** a continuity note that Hesk was with Grak on the ridge, so Tarra's instruction to Hesk at the cave conflicted with where the Custodian had placed him.
8. After C10, a request to aim nearer the 300-word guide.
9. After the later relays, a "Keep the PUBLIC block format" reminder only.

The Custodian once asked the orchestrator for a ruling: whether to roll Grak's watch rather than narrate it. It received no answer.

## Costs

Input tokens come from the platform's stored subagent transcripts, summed over each agent's API calls. Output tokens are not reliable in that record, which logs streaming chunks, so they are left out.

| Role | Replies | Input tokens written to cache | Input tokens read from cache | Active span |
|---|---|---|---|---|
| Custodian | 16 | 192k | 9.67M | 07:41–08:04 UTC; about 22–95 s per reply |
| Grak | 12 | 56k | 1.01M | about 4–6 s per reply |
| Tarra | 14 | 57k | 1.19M | about 4–6 s per reply |
| Orchestrator | n/a | unavailable | unavailable | relay overhead about 5–8 minutes |

Uncached input was under 300 tokens per agent. The Custodian's cost is dominated by cache reads: about 600k tokens per reply, because each tool call re-reads its whole history. Billed money is unavailable.

## Files

Committed in this folder:

- `manifest.md`;
- `transcript.md`;
- `summary.json`;
- `report.md`;
- `audit.md`, by Astra.

Kept for the auditor in the ignored `playtests/runs/P1/`:

- `initial/` and `final/` campaign state, including the JSONL log, 53 receipts, the checkpoints and the recap;
- `frozen_hidden_scenario.md`;
- the player packets;
- `orchestrator_notes.md`;
- `tool_trace.jsonl`, every tool call by every agent, added after the audit.
