# P2 manifest

| Field | Value |
|---|---|
| Run | P2, pilot protocol revision 3 |
| Rules commit | `515f598` |
| Skin | Clanfire |
| Scenario | Emberfall continued: session 2 of P1's campaign (`playtests/campaigns/p1_clanfire`); the hidden scenario is unchanged from P1 |
| Modules | none |
| Orchestrator | Fable (`claude-opus-5-5`), not seated |
| Custodian | a fresh subagent, `claude-sonnet-5-5`, Claude Code general-purpose agent, default settings; it received the revision 3 brief plus the bootstrap only |
| Players | P1's two player agents, continued (`claude-sonnet-5-5`), each with its P1 history |
| Master seed | 102 (seeds 102001–102024 used; no table draws) |
| Access | instructed, not enforced; checked against the full tool trace |
| Date | 3 October 2026; setup about 09:40 UTC, play 09:48–10:27 UTC (about 39 minutes) |
| Outcome | complete: 10 beats, 2 acts, session closed |

## Setup

**Gear reconciliation.** Revision 3 requires P2 to reconcile gear from P1's end rather than restore the starter kit. Before session 2 opened, `update_sheet.py` recorded on the sheets:
- **Grak:** spear, hand-axe, hide cloak, ochre pouch and sinew cord, all retained.
  - The spear was dropped at C5 and retrieved at P7.
  - Ketha took only a pinch from the pouch (C10).
  - His session 1 boon, the remembered migration path, went into the sheet notes.
- **Tarra:**
  - retained: the flute (dropped at P5, back at her belt by C10), the fire-bow drill and the cloth scrap;
  - consumed: the herb bundle (P12, and "the last of the herbs" at P14);
  - gained: the antler dart-point (C14) and the amber pendant (the C16 boon).

P1's frozen final snapshot was left unchanged.

**Drives:**
- **Grak:** "Keep the clan fed and whole through this winter, and finish the wounded wolf before it teaches the pack the way in."
- **Tarra:** "Keep both peoples alive through the winter, and stop the Ysre sickness before it spreads through the cave."

**Packets.** The P1 packets still applied. Each player also read a packet addendum once:
- the brief changes;
- their drive;
- their public export, with reviewed notes (2 unspent build points, the boons);
- Clanfire's Shadow track, `skins/clanfire.md` lines 96–109 (the step effects, gain and purge, but not the crisis table);
- the session 1 dialogue that player had not seen.

| Addendum | SHA-256 |
|---|---|
| `packet_addendum_grak.md` | `e0928136a380c2f927c8f53229c41105f1d8b938974fd4e2ca1e8699f26ced88` |
| `packet_addendum_tarra.md` | `365cdc092f34f4d3993c22e928bafb395cab2f518864032beb16f042a8ab9e67` |

**The Custodian.** It got the revision 3 brief, the campaign path and the seed schedule. It was told to resume through `skills/agent_bootstrap.md`, and not to read `playtests/runs/`, `docs/playtests/pilot/` or `campaigns/`.

## Access

The tool trace is in `playtests/runs/P2/tool_trace.jsonl`, extracted from the platform's stored subagent transcripts.

| Agent | Tool calls |
|---|---|
| Custodian | 101 Bash, 1 Read (the handbook), 23 hand-backs. No command touched `playtests/runs/`, `docs/playtests/` or `campaigns/`. |
| Grak | 1 Read (his addendum), then hand-backs only |
| Tarra | 1 Read (her addendum), then hand-backs only |

## Custodian policies

These are as the Custodian applied them; it wrote no separate policy file.

- **Luck tests:** none called by the Custodian. Tarra made one player-invoked Instinct test with the vision shard. It was recorded as a check against her current pool, not with `--luck-test`, which is reserved for Custodian-called tests.
- **Purges:** one Shadow purge at the close, tied to a great hunt and a hard-won return to clan safety (both listed purge sources).
- **Shared hazards:** none charged.

## Interventions

There were no format or pacing reminders, and no rules corrections. Everything other than verbatim relay is listed here.

1. **Setup message to each player:** read the addendum once, then reply "Ready".
2. **Routing note to the Custodian, with P006:** Tarra had not yet seen the last four replies and would receive them with her next turn.
3. **Relay error at G014:** the reply sent to Tarra ended "Answer as Grak only". A correction followed at once ("You play Tarra…"). Tarra had already answered as Tarra. Her answer opened with a meta line to the orchestrator, which was removed before relay; the in-character answer was relayed verbatim.

The Custodian asked the orchestrator for no rulings.

## Relay and records

- **Checkpoint check.** The orchestrator saved each public body as `replies/gm_NNN.md` and compared it with `state/checkpoints/last.md` before forwarding. All 23 matched (`checkpoint_checks.jsonl`).
- **Player answers.** Saved as `replies/pNNN_<character>.md`.
- **Queued replies.** A player not due to answer received the queued replies and the other player's answers, in order and verbatim, with their next turn.

## Costs

Input tokens are from the stored subagent transcripts, summed over API calls from 09:46 UTC. Output tokens are not reliable in that record and are omitted.

| Role | Replies | Written to cache | Read from cache | Notes |
|---|---|---|---|---|
| Custodian | 23 | 259k | 19.8M | about 30–130 s per reply |
| Grak | 22 (21 answers and "Ready") | 128k | 2.44M | about 3–8 s per reply |
| Tarra | 16 (14 answers, "Ready", "Stands") | 190k | 1.72M | about 3–7 s per reply |
| Orchestrator | n/a | unavailable | unavailable | relay and records |

Billed money is unavailable.

## Files

Committed in this folder:
- `manifest.md`, `transcript.md`, `summary.json` and `report.md`;
- `audit.md`, by Astra, when it is done.

Kept for the auditor in the ignored `playtests/runs/P2/`:
- `initial/` and `final/` campaign state, including both sessions' JSONL logs, receipts, checkpoints and memory;
- `replies/`;
- `checkpoint_checks.jsonl`;
- `check_reply.sh`;
- the packet addenda;
- the public exports;
- `tool_trace.jsonl`;
- `orchestrator_notes.md`.
