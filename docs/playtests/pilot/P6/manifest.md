# P6 — Candlelight Dungeons pilot manifest

Status: **incomplete, suspended by platform capacity failure during G004**. Cross-team audit remains pending; no completed-session result.

- Protocol revision 3; SHA-256 `7ddc519a05e2c647a5f244cc0c1fb54989c52c1a3f1014925d1dc96ad7d76c62`.
- Rules/harness/protocol commit: `515f598d23cd28e7848a4a1d7d6117f5545527f4`. Rules and engine were unchanged from P5; guidance, evidence and delivery procedure were revised after the first round.
- Orchestrator: Astra in this Codex conversation; exact root model ID and reasoning setting unavailable in the collaboration API.
- Custodian: `gpt-6-sol`, reasoning `medium`, fresh history, `p6_custodian`.
- Players: four separate `gpt-6-sol`, reasoning `medium`, fresh histories: `p6_bram`, `p6_iona`, `p6_mara`, `p6_pip`. Each keeps a separate history. The platform's concurrency limit may serialize some turns; pending answers are withheld until all addressed players have replied.
- Access: one explicitly permitted initial packet-reader command per player, then tools/files forbidden by instruction. Shared tools/filesystem remain available; this is not enforced isolation. The reader records a hash receipt when it emits the packet verbatim; this does not prove comprehension, forbid other access or replace a complete tool trace.
- Skin: Candlelight Dungeons; four PCs; heroic 16-point budget as suggested by the skin. Delvekit, Injury, gritty and Wealth modules off.
- Character generation seeds: Bram 610031 (primary STR), Iona 610032 (LOR), Mara 610033 (FTH), Pip 610034 (DEX). Primary biases and free grants chosen before generation. No rerolls or score changes.
- Free Knack/Expertise pairs: Bram Second Wind / Fighter (STR); Iona Arcane Flex / Hedge magic (LOR); Mara Turn Undead / Grave tender (FTH); Pip Jack-of-Trades / Pathfinder (DEX). No bought tags.
- Loadouts and drives: `playtests/runs/P6/roster_setup.json`, preserved in the initial sheets. Each has one owned Knack; generic resource counters do not grant additional knacks, which the packet explicitly explains.
- Named spells: agreed before play in `playtests/runs/P6/public_spellbook.md` and the casters' sheet notes, then included verbatim in every public packet. Printed tier rules and costs apply; no extra magic stat or free tag was invented.
- Master gameplay seed: 61003; Nth new dice command uses 61003000+N. Character generation uses its separate seeds. Retry index, event ID and seed remain unchanged.
- Setup started (UTC): 2026-10-03T09:41:28.052298+00:00. Character/kit preparation began while revision 3 awaited commit; no public play or logged mechanics preceded the pin. Four players ready: 2026-10-03T09:50:59.806506+00:00.
- Hidden scenario: `playtests/runs/P6/frozen_hidden_scenario.md`, SHA-256 `859022f57d5a3b91ddc79f468d68934ae1663d3c684dc0132a0bc55543f99211`. Frozen by the Custodian before public play; not sent to players. Initial snapshot: `playtests/runs/P6/initial/p6_candlelight/`, frozen 2026-10-03T09:48:53.522022+00:00.
- Opening checkpoint recorded (UTC): 2026-10-03T09:52:22.701675+00:00. Suspension recorded: 2026-10-03T10:10:18.536316+00:00. No game ending or session-close. Suspension snapshot: `playtests/runs/P6/suspended/p6_candlelight/`. Four public Custodian replies, eleven player replies; one recorded beat, no completed acts, rolls or crises. Current party Fatigue: 0.
- Per-role token usage, compute time and monetary costs: unavailable from the live collaboration API. Do not infer them from reply counts or account limits. Wall-clock timestamps are recorded.
- Setup command failures: three, all before public play: two unquoted-colon metadata parses (one orchestrator, one Custodian dry-run), and one Custodian metadata call before Iona existed. Successful later calls are retained. No dice or scores changed. No game-ruling intervention. Scheduling failures and diagnostic interrupts are recorded below.

## Fixed character drives

- Bram Cinder: Bring every member of the company home; take the exposed position when someone must.
- Iona Thistle: Recover endangered lore intact, while accepting that living companions come before an irreplaceable book.
- Mara Fen: Give the restless dead a peaceful ending and protect living people from the price of careless magic.
- Pip Reed: Earn an honest share of treasure to clear a family debt; look for a safe exit before choosing a profitable risk.

## Exact player packets

All packets contain the required public core text, Candlelight's player-facing rules and Pressure steps/triggers, the agreed public spellbook, the player's drive, and their public export. The crisis table and Custodian section are excluded. Each source was emitted verbatim by one initial reader invocation, with hash receipts in `packet_delivery.jsonl`.

- Bram Cinder: `bram_cinder`, `1d0be55a73faf1dc7be06c65087948c8cb0f64eeb01e0b484d5c563b1ba042dc`.
- Iona Thistle: `iona_thistle`, `71f92fccbbc460fd021bb6bb8f7db0377b0aeaac4e3db7a2e64283fb436db105`.
- Mara Fen: `mara_fen`, `3d992f9fd895f27a325be02800837eb1d86d458160d537c681bb5c7cbb8aa987`.
- Pip Reed: `pip_reed`, `c9ff6077c72af25c4381e9231b9f72d66ec97f6d00c7be388a0080dcf7002780`.

## Evidence conventions

Run-local `record_cli.py` records harness argv, results, statuses, seeds and times without adjudicating mechanics. `messages.jsonl` and `transcript.md` preserve public dialogue; each Custodian body also has a `gm_NNN.md` file. Public markers and TO routing are excluded from the player body/checkpoint. Each compared checkpoint is independently copied into `checkpoint_versions/`, and comparisons go to `checkpoint_checks.jsonl`. Full completed public dialogue is delivered before each new player decision. These records are not a full agent-tool/access trace.

## Predeclared Custodian policies

# P6 Custodian policies, declared before play

## Fortune tests

Call “Test your Fortune” only when blind chance alone decides a consequential fact the characters cannot meaningfully control, such as whether a patrolling scavenger happens to have left a crossing clear. Use a relevant action test when a delver searches, listens, maps, hides, bargains, or otherwise changes the odds through a method. Do not use Fortune to manufacture a failed clue or a compulsory hazard. Treat the Almanac's one or two tests per dozen beats as restraint, never as a quota. The test targets current Fortune coins before any post-roll spend.

## Purging shared Fatigue

Sleep in genuine safety, a hearty stew with time and shelter, or a credible miracle can clear Fatigue under the skin. Before applying a purge, establish what the party gives up and what makes the refuge safe; a quick pause in a threatened corridor does not count. A warm hearth permits the skin's separate short-rest recovery of 1 personal Fortune coin. Do not promise a purge as a pacing correction after a crisis or erase a lasting crisis consequence with the track reset. Use the harness to record each actual change.

## Shared hazards and crisis targets

Charge a common hazard once for the party when one stretch of threatened time, one noisy group passage, or one environmental exposure affects everyone in the same beat. Individual spell costs, knack choices, wounds, and distinct reckless actions remain separate; simultaneous choices do not automatically merge. Declare the trigger and stakes before charging Fatigue, and never charge real-world thinking time. If a shared hazard reaches 5 with no single actor responsible, name the exposed character the fiction points to before drawing and resolving the crisis; if no one is more exposed, use the person leading that passage or action. Record the crisis target and consequence before the reset, retaining any lasting effect separately.

## Platform interruption and resume boundary

At G004, Bram and Iona replied; their B004/I004 responses are saved but have not been forwarded to the Custodian. Reactivating Mara failed three times with `collab tool failed: agent thread limit reached`, including after Iona completed. Pip's G004 activation was not attempted. Earlier, the same error while activating Iona at G001 cleared after Bram completed.

The agent listing then showed only the root, completed P5 Jori and Rhea, and P6 Bram as `pending_init`, despite the other P6 roles having produced replies. Interrupting those three listed agents did not release capacity. Those diagnostic calls are orchestration interventions, not player declarations. No replacement player, state correction, reroll or global configuration change was made. The current tool interface exposes no close-agent operation. This is a platform failure, not an observed game stall.

Resume with the existing Mara and Pip histories and the chronological public-only G004 relay bundles. Do not expose B004/I004 until all four replies are collected. If the original histories cannot be recovered, retain this as an interrupted run and explicitly declare a restart or reconstruction; do not silently count it as continuous play. The next unused gameplay draw index is 1.
