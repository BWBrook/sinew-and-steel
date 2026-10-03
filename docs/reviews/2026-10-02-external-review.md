# Sinew & Steel — independent external review

**Date:** 2 October 2026  
**Reviewer:** GPT-6 Astra Pro, in the independently commissioned reviewer role  
**Reviewed commit:** `46700761b70545b71ae4bf82b08cde02102e5e72`  
**Repository:** `BWBrook/sinew-and-steel`  
**Disposition:** Targeted repairs, then instrumented playtests; not yet GOLD. Retain the settled numerical engine.

## 1. Scope, independence and verification

The review brief was read first. I read the book in its specified release order, followed by the operational harness documentation, the principal implementation and selected tests, then `PLAN.md`. I recorded my independent candidate findings before reading the Stage 4 implementation/review reports and `CHANGELOG.md`. Those later documents were used to distinguish new findings from acknowledged limitations and repaired defects, not as confirmation that the implementation works.

**Read in full:** the Preface, Quickstart, The Adventurer, Adventurer’s Manual, The Custodian, Custodian’s Almanac, Customisation, all ten main skins, the three specified Emberfall documents, AI as Custodian, AI Play Notes and back-cover blurb. Also the review brief, `manifest.yaml`, `PLAN.md`, `AGENTS.md`, `docs/ai_play_harness.md`, the principal play/setup/state/prompt skills, the chat and agent starter templates, and the Chinese-room prompt and guide. `README.md` and `NOTICE` were checked for onboarding and release scope.

**Detailed implementation review:** `_rules.py`, `_pressure.py`, `_resources.py`, `_play.py`, `_runtime.py`, `play.py`, `advance.py`, `build_prompt.py`, `playtest_summary.py`, `resume_pack.py`, `_dice.py`, and the creation/advancement portion of `_characters.py`. I inspected the resolution-contract, book-example, play-runtime and playtest-summary tests, with particular attention to adversarial cases. This was not a line-by-line review of every tool or every test file.

**Consulted or skimmed:** the historical engine atlas and independent-engine analytical reports, selected numerical tables, the Stage 4 handoff and review, and the changelog. Their uncapped creation results and superseded stance recommendations were not treated as current rules evidence.

**Skipped or not independently verified:** `docs/archive/`, private campaigns, the full migration/validator implementation, most auxiliary tools, Delvekit implementation, expensive analytical reruns, and the PDF release pipeline. Artwork, typography and layout were outside scope. I did not independently render or confirm the two-page Quickstart gate.

### What actually ran

Direct checkout was unavailable in this environment; the GitHub connector supplied the sources. I restored selected pure Python modules locally and verified their exact Git blob hashes before execution. Python 3.13.5 ran the following independent checks:

| Check | Executed coverage | Result |
|---|---|---|
| Resolution and nudging | 41,680 enumerated cases: selected opposed match-ups, all kept-die combinations for straight/Advantage/Disadvantage/cancelled rolls over targets 0–21, and natural/adjusted nudge boundaries | No discrepancies |
| Published opposed probabilities | 36 displayed match-up cells, recomputed over their 400 ordinary opposed outcomes | Agree within displayed rounding |
| Published character prices | 20 skin samples plus three Almanac builds; free grants distinguished from bought tags | All 23 prices agree |
| Current creation ledger | All 1,127,357 labelled allocations of five scores 6–16 and Stamina 3–9, against a separately written capped-ledger formula | No discrepancies; grim maximum attribute 14; attribute 16 with Stamina 9 requires at least 12 points |
| Damage | 99,550 raw/adjusted-face, attribute, edge and soak cases against a separately written formula | No discrepancies |
| Pressure state machine | Forced-crisis reproduction and ordinary crossing, discard, non-rearming, overflow and reset controls | Forced-crisis defect reproduced; ordinary lifecycle controls pass |

These are enumerated inputs and targeted checks, **not** that many independent test functions or simulated sessions. The sample inputs were transcribed from the reviewed text; I did not run the repository’s sample parser.

**Not run here:** the full `unittest` suite, `validate_repo.py`, campaign validation, the end-to-end `scratch_demo` CLI exercise, or an actual `build_prompt.py` invocation. Compact-prompt findings come from reading the exact template, builder and included texts—not a blind model-play experiment. Previous reviewers’ reported test totals are not presented as results of this review. Source-only findings are explicitly marked below.

All repository locations below refer to the pinned commit. To inspect a location, append its path to:

`https://github.com/BWBrook/sinew-and-steel/blob/46700761b70545b71ae4bf82b08cde02102e5e72/`

## 2. Verdict

**Sinew & Steel is a coherent game with an unusually serious supporting harness. It is not yet ready for GOLD or unattended balance playtests. The necessary next step is a bounded procedural repair pass, not another redesign of the numerical engine.**

The full book supplies a workable route from character creation to play. Emberfall earns its place by teaching actual decisions rather than merely providing setting material. The skins create meaningfully different pressures while retaining recognisable core procedures. Independent arithmetic checks support the creation cap, sample characters, opposed resolution and damage rules.

The largest risks sit elsewhere. First, the intended DriveThruRPG release needs an eligibility decision, not merely an AI-disclosure checkbox [S1]. Second, the harness cannot faithfully represent every printed crisis: it equates a pending crisis with Pressure 5, while some spells cause one below 5, and it blocks tests needed to resolve a crisis already underway. Third, Beast Bond cannot directly fund the promised nudges. Fourth, action-taking simple checks lack the combat safeguards applied to attacks and opposed tests. These omissions can turn an apparently clean playtest log into a record of improvised workarounds.

The compact chat packet is also not a complete standalone specification. The existing full-prompt alternative is the right fallback; this is a deployment distinction to make explicit, not a reason to enlarge the two-page Quickstart.

Telemetry is substantially better than a typical prototype’s: it separates incomplete histories, recognises censoring and avoids obvious double-counting. Nevertheless, a structurally complete log is not proof of correct adjudication, and “routinely” still needs a predeclared interpretation.

I found five Major issues and six Minor ones. No finding warrants changing damage, soak, margin steps, natural results, starting budgets, the refund cap, milestone rewards or Twilight’s position values. Repair the representational gaps, run the actual repository suite and workflow, then conduct a small, stratified screening programme. Freeze the text and proceed to layout only after those results and the release route have been triaged.

## 3. Findings

Severity follows the brief. “Major” means a concrete gap likely to be encountered, not a judgement that the project is fundamentally unsound. No new issue is labelled Blocker merely because a feature requires Custodian judgement. The first finding is a release-channel gate rather than a defect in play.

### F01 — DriveThruRPG eligibility is unresolved; disclosure alone is insufficient

**Severity:** Major — release gate. **Lens:** 1.

**Location:** External-review brief, “What the game is”; `rules/book/ai_as_custodian.md`; `rules/appendices/ai_play.md`; publisher Product Standards Guidelines, “AI-Generated Content Policy” [S1].

**Evidence:** The brief describes AI-drafted text and a free DriveThruRPG release. The publisher policy says: “We do not accept any product that includes text generated by AI tools.” It also excludes products intended to elicit AI-generated outputs. The disclosure filter does not override those exclusions [S1].

**Why it matters:** The project’s authorship and AI-play instructions create an eligibility question at the centre of its intended distribution plan. This is not an objection to its AI-first purpose.

**Smallest fix:** Before treating that channel as confirmed, request a written Partner Relations determination covering the actual files, drafting/editing process and free price. Record that decision in the release checklist. Do not assume either human editing or a zero price establishes an exemption; do not conceal provenance. Keep distribution through the project repository as a practical fallback, without representing another storefront’s rules as checked.

**Settled decision:** No game rule changes. The intended release route may need revision.

**Confidence/check:** High that clarification is necessary; the platform decides final eligibility. Checked against official policy retrieved on 2 October 2026. This is not legal clearance.

### F02 — A printed crisis below Pressure 5 has no valid harness representation

**Severity:** Major. **Lenses:** 3, 4, 5.

**Location:** `skins/candlelight_dungeons.md`, spellcraft/Arcanum; `skins/whispers_in_the_fog.md`, Unspeakable tier; Manual §8; `tools/_pressure.py`, `validate_pressure()` and `crisis()`.

**Evidence:** Arcanum and Unspeakable magic impose an upfront two-point Pressure cost and a crisis on failure even when that cost does not reach 5. Manual §8 prevents duplicating that crisis when the same action also reaches the threshold. Conversely, the validator requires:

```python
track.get("crisis_pending") == (current == 5)
```

and `crisis()` rejects any track without `crisis_pending`. In the executed reproduction, a track at 0 receives its two-point upfront cost; recording the failure crisis then raises `ValueError: this track has no pending crisis`. Manually setting the pending flag at 2 makes the state fail validation.

**Why it matters:** The agent must either omit a printed consequence, invent extra Pressure to unlock the command, or leave the normal state/telemetry path. Artificially adding three points also fabricates threshold crossings and source totals. This is a genuine book/code mismatch, not a proposed change to magic balance.

**Smallest fix:** Represent a pending crisis as an explicit event with a cause, affected track and originating action, rather than defining it solely by the numerical threshold. Permit a declared skin-triggered crisis below 5. If that action also reaches 5, coalesce the causes into one crisis. Preserve the existing consequence-before-reset and lasting-effect rules.

**Acceptance check:** Failed Arcanum from 0 ends its upfront stage at 2 and then produces exactly one crisis/reset. Starting at 3 also produces only one. Repeat for personal Insanity and verify that the other investigator’s track is unchanged. Do not extend this to Twilight’s Reckoning: its failure is not the same forced-crisis rule.

**Settled decision:** Implements the existing skin exceptions and single-crisis rule; changes none of their costs or probabilities.

**Confidence/check:** High. Executed against the hash-verified Pressure module with a minimal declared skin fixture; printed spell rules and the absence of a CLI alternative were source-checked. The full CLI reproduction remains to be run.

### F03 — A pending crisis blocks the test needed to resolve its own consequence

**Severity:** Major. **Lenses:** 3, 4, 5.

**Location:** `skins/service_duct_blues.md`, Stress crisis table, result 4; `tools/_play.py`, `ensure_ready()`/action preparation; `tools/play.py`, crisis dispatch and allowed commands during a pending crisis.

**Evidence:** The printed result is “Nanite alarm: test SYS or lose a key system until repaired.” However, readiness checking rejects an ordinary `check` while a crisis is pending. The CLI explicitly permits Pressure, effect-ending, pool, condition, resource and clock changes in that state, but not a resolution check. Its crisis handler requires the adjudicated consequence before it commits the reset.

**Why it matters:** The supported workflow has no nested resolution phase for this result. Resetting first changes the ordering and can remove active Pressure effects before the required test. Using a stateless roller can adjudicate the fiction, but loses the ordinary persisted-roll, nudge and roll-event pathway. The table result is not just descriptive fallout.

**Smallest fix:** Add a narrowly scoped crisis-resolution phase that allows tests belonging to the pending crisis, while still blocking unrelated play. Persist its dice and settlement as normal, record any consequent state changes, then close and reset the crisis once. Do not remove the pending-crisis guard globally. Explicitly distinguish a compelled consequence test from a freely chosen new action when applying tolls.

**Acceptance check:** Force Service Duct result 4, resolve SYS through success, failure and a legal nudge, then retry the commands. There must be one saved test, one consequence and one reset, with no reroll or early reset. Cover a “roll twice” crisis containing that result too.

**Settled decision:** Preserves the existing crisis timing, printed table and choice-based toll principle.

**Confidence/check:** High on the missing standard pathway; checked by reading and tracing dispatch. No end-to-end execution claim.

### F04 — Beast Bond is a counter, but cannot fund settlement nudges

**Severity:** Major. **Lenses:** 2, 4, 5.

**Location:** `skins/clanfire.md`, “Beast Bond”; `manifest.yaml`, Clanfire resources; `tools/_resources.py`; `tools/_play.py`, nudge funding in `finish_action()`; `tools/play.py`, settlement arguments.

**Evidence:** The skin gives the beast three Instinct beads and says to “spend its beads instead of your own, one per point of nudge” when it can help. The manifest/resource system can hold the beast’s pool. Settlement, however, funds adjustments from an involved character’s Luck or the special Companionship mechanism; it has no Beast Bond funding selection. Spending a generic resource does not itself adjust the die. Registering a beast as an unrelated NPC does not make it a permitted third-party payer for its owner’s check.

**Why it matters:** This is a flagship ability in the default teaching skin, not an obscure optional module. Charging the character’s Luck and compensating it later misstates expenditure and recovery; merely reducing the beast counter leaves the die unchanged.

**Smallest fix:** Let a declared nudge identify an eligible funding resource owned by the acting character, with Beast Bond as the first supported instance. Atomically validate the adjustment, deduct the beast’s beads and record the resource-funded nudge without moving the owner’s Luck. The Custodian should still decide whether a bond exists and whether help is plausible. A resource definition must not automatically grant the ability.

**Acceptance check:** Beast 3, owner Luck 0, legal two-point nudge: beast ends at 1, owner stays at 0 and the die changes by two. Naturals remain locked. Spending the last bead records the required loss/care consequence; later use requires the fiction to permit it. Check rest and milestone recovery explicitly.

**Settled decision:** Implements the printed funding exception; does not give the party more beads or broader eligibility.

**Confidence/check:** High; source-checked across the skin, resource handling and settlement interface. Not executed end to end.

### F05 — Simple action checks can bypass combat order and action consumption

**Severity:** Major. **Lenses:** 2, 4, 5.

**Location:** Manual §6; `tools/_play.py`, combat preflight and action completion; `tools/play.py`, `check` and `pass`; harness guidance on using `pass` after non-attack actions.

**Evidence:** The Manual gives each able combatant one action per round in the fixed side order. Combat preflight and automatic action use cover `attack` and `opposed`, but not a simple `check`. The documented workaround is to mark the turn with `pass`. That operation checks membership/action use but does not provide equivalent pre-roll side-order and ability-to-act checks.

**Why it matters:** A combatant can resolve an action-taking check before its side is eligible, or after already acting, before a later `pass` notices anything. A second device activation or self-directed spell can therefore commit its roll, costs and result outside the action budget. The same gap concerns a dropped combatant. This is distinct from the already-fixed opposed-action bug.

**Smallest fix:** Introduce an explicit action-versus-reaction classification for simple checks in combat. A declared combat action must undergo the same preflight as an attack and consume the action when settled; a defence or other genuine reaction must not. Route `pass` through the same eligibility check. Keep the Custodian’s judgement about what constitutes the action, rather than making every incidental check consume a turn.

**Acceptance check:** An action-taking simple check by the wrong side, a character who already acted or a character at 0 Stamina is rejected before dice or costs. A legal one consumes exactly one action. A reaction remains free. Repeating settlement cannot consume a second action.

**Settled decision:** Enforces existing initiative, one-action and free-defence decisions.

**Confidence/check:** High on the unguarded route; source-traced, not executed. An attentive agent can avoid it manually, but the state boundary does not enforce it.

### F06 — Compact chat is not a complete standalone rules packet

**Severity:** Minor, because a documented full-prompt route exists. **Lenses:** 1, 2.

**Location:** `rules/quickstart.md`; `prompts/chat/starter_prompt.md`; `tools/build_prompt.py`, compact/full assembly paths; `skills/build_prompt.md`; README, table/chat quick start.

**Evidence:** Compact assembly embeds the Quickstart and skin and supplies a rules-section lookup index. The Quickstart explains opposed attacks but not the full initiative/round procedure. It also omits the Manual’s cumulative Pressure timing and one-test lifecycle rules. Clanfire does not independently supply all those missing core instructions. A reference to a local command cannot provide them to an isolated chat model.

The README and skill already say to use `--full` when the model cannot read the repository. That is a material mitigation, and this finding is not a claim that the documentation hides the limitation.

**Why it matters:** A capable model may fill the gaps with familiar RPG conventions. Fluency would then look like rules compliance. The compact packet cannot, by itself, determine all the answers requested in the review brief.

**Smallest fix:** Make the generated chat packet itself state its capability requirement: “This compact packet requires access to the referenced core sections. Without that access, use the full packet; do not invent missing procedures.” Prefer a standalone-chat default of full, with explicit compact opt-in. Alternatively, add a short AI-only operational supplement outside the Quickstart.

**Settled decision:** No change to the two-page Quickstart or its page allocation is required. Preserve the existing compact agent workflow where retrieval is available.

**Confidence/check:** High on content sufficiency, not on an empirical model failure rate. Checked by reading the builder, template and included texts; no generated packet or isolated model session was executed.

### F07 — Success-only Luck costs rely on an unpersisted reservation

**Severity:** Minor — documented manual hand-off, not an automatic spell-engine promise. **Lenses:** 2, 4, 5.

**Location:** Manual §3; Candlelight spellcraft, especially Greater Spell; `tools/_play.py`, pending actions and settlement; `play.py` cost arguments; Stage 4 handoff, “What the Custodian still decides”.

**Evidence:** The Manual says mandatory token costs must be set aside before nudging, with success-only costs paid only on success. `--luck-cost` charges upfront. Pending actions do not have a declared conditional Luck reservation that restricts settlement spending and is paid or released with the outcome. The handoff explicitly leaves success-only costs to the Custodian; that boundary is acknowledged rather than concealed.

**Why it matters:** A Greater Spell caster with one remaining Luck cannot use that same token both to rescue the roll and to pay its mandatory success cost. Upfront payment would instead charge a failed casting incorrectly. A careful agent can reserve mentally, settle and then pay on success, but that obligation is fragile across a deferred decision, resumed context or interrupted multi-command sequence.

**Smallest fix:** At minimum, document that exact reservation/settlement/payment recipe and store the reserved obligation in pending state visible on resume. Prefer explicit caller-declared conditional costs applied atomically at settlement. This does not require the tools to infer spells from method text.

**Acceptance check:** With only the reserved token available, settlement cannot spend it on a nudge. A success pays once; failure releases it without payment; retry and resume preserve the obligation. Keep actual spend separate from a reservation in telemetry.

**Settled decision:** Implements Manual §3; changes no cost or nudge rule.

**Confidence/check:** High on the missing persisted mechanism; medium on practical frequency because disciplined manual use avoids it. Source review only.

### F08 — Raising the Luck attribute adds a token without a Luck event

**Severity:** Minor. **Lenses:** 4, 5.

**Location:** `tools/_characters.py`, `raise_stat()`; `tools/advance.py`, campaign event construction; `tools/playtest_summary.py`, Luck accounting in `summarize_session()`.

**Evidence:** Raising the Luck attribute increments both maximum and current tokens. `advance.py` emits a separate Luck event for an `award`, but not for a `raise`. The summariser deliberately counts movement from Luck events rather than adding roll snapshots as expenditure or recovery.

**Why it matters:** A raise from current Luck 3 to 4 is a real pool increase, yet the movement/source ledger omits it. Starting Luck minus logged spending plus logged gains can then disagree with the ending pool. Later beat/roll snapshots may still give the correct low-Luck classification; this finding does **not** imply every midpoint result is wrong.

**Smallest fix:** Compare current Luck before and after every advancement operation and emit exactly one movement event whenever it changes. Identify a capacity/advancement gain separately from rest or milestone recovery, while preserving a reconcilable total pool ledger.

**Acceptance check:** A Luck raise produces one `+1` event, a non-Luck raise produces none, and an idempotent retry produces no second gain. Reconcile the final pool from the initial snapshot and movement events, including a milestone followed by a Luck raise.

**Settled decision:** Preserves the recently fixed rule that a milestone Luck raise leaves the pool full. This finding concerns its omitted telemetry, not that rule or its arithmetic.

**Confidence/check:** High; source-traced through all three components. Not executed through the campaign CLI.

### F09 — Read-only tools do not hold a coherent campaign snapshot

**Severity:** Minor — concurrency hardening. **Lens:** 4.

**Location:** `tools/_runtime.py`, `campaign_lock()`/`ensure_recovered()`; `resume_pack.py`, `collect_resume()`; `build_prompt.py`, campaign reads; `playtest_summary.py`, campaign input path.

**Evidence:** Writers use a campaign lock and transaction journal. Readers check for an existing journal, but do not hold a shared campaign lock over their multi-file reads. The dry-run lock path likewise checks and yields without acquiring the writer’s lock.

**Why it matters:** A possible interleaving is: reader checks that no journal exists; writer begins; reader reads an old sheet; writer replaces tracker/log; reader reads those new files. Each individual file can be valid while the combined resume or report is not one campaign state. The existing protection against an already-interrupted transaction does not eliminate this check-then-read race.

This is not an observed corruption incident or a claim that ordinary serial play is broken. It matters when an agent or user runs summaries, prompt rebuilding or previews concurrently with play.

**Smallest fix:** Use a shared lock for the complete snapshot, with the recovery check made under that lock, and an exclusive lock for writers. Ensure the lock file exists through setup/migration so read-only operations need not create state. An equivalent versioned-snapshot design is acceptable.

**Acceptance check:** Use barriers to pause a writer between file replacements while starting a reader. The reader must return a wholly old or wholly new snapshot, or refuse/retry—not a mixture. Confirm that preview commands leave all campaign bytes unchanged.

**Settled decision:** None. Preserve the existing transaction and read-only guarantees.

**Confidence/check:** Medium, based on a source-level interleaving proof. No concurrent-process test was run. This is distinct from the already-known checkpoint-writing lock issue.

### F10 — The standalone hidden-scenario template promises privacy while displaying its notes

**Severity:** Minor. **Lenses:** 1, 2, 4.

**Location:** `prompts/chat/hidden_scenario_prompt.md`, Background and final output instructions; `prompts/chat/how_to_use_chinese_room.md`; `rules/book/ai_as_custodian.md` and AI Play Notes.

**Evidence:** The standalone template says, “The human player sees only public narrative; secret notes stay hidden.” It later instructs the model to output the private record inside a Chinese `[GM-NOTES zh]` block. That block remains visible and translatable in the same chat. The companion guide recognises the honour-system limitation, and the book gives better secrecy advice.

**Why it matters:** Someone copying just the template can mistake spoiler obfuscation for a separate private channel. The problem is the template’s promise, not using another language as a voluntary convention.

**Smallest fix:** Replace the privacy claim in the template itself: “This chat displays the GM notes in Chinese as spoiler obfuscation only. It is not private storage; anyone with the chat can read or translate it. Use a separate private file or channel when genuinely hidden notes are required.” Keep the no-unrequested-spoilers instruction for ordinary narration.

**Settled decision:** No mechanics or prose-voice change; aligns the standalone operational template with the book’s existing distinction.

**Confidence/check:** High; direct textual comparison. No privacy attack or model experiment is claimed.

### F11 — Two concrete title similarities merit clearance before release branding

**Severity:** Minor — discoverability and association risk, not a finding of infringement. **Lens:** 1.

**Location:** Project title and `skins/whispers_in_the_fog.md`; official external listings [S2–S3].

**Evidence:** Steam lists **Steel And Sinew**, a medieval PvP RPG by SerGuillotin, with release date to be announced [S2]. Its title reverses the project’s two principal words. **Whispers in the Fog** is also the exact title of a psychological horror video game on its official site [S3]. The latter overlaps the skin’s broad genre as well as its name.

**Why it matters:** These are specific search/discovery collisions, not merely a judgement that the skins evoke familiar genres. They can complicate locating the intended game or distinguishing an independent work from an associated product.

**Smallest fix:** Make and record a title-clearance decision before GOLD branding. At minimum, consistently pair the main title with Barry Brook and “tabletop role-playing game” in searchable metadata; consider a more distinctive skin title if the exact horror-game match is unwanted. No forced rename follows from this review.

**Settled decision:** No engine rule touched. This is evidence relevant to naming, not a taste-based objection to the author’s voice.

**Confidence/check:** High that the listings exist; medium about their practical impact. Official-source web check on 2 October 2026. I did not establish trademark priority, jurisdictional rights or infringement, and did not perform a passage-level comparison against third-party rulebooks. Negative search results are not clearance for the remaining titles.

## 4. Newcomer and AI-mode assessment

### The book as a game package

The book works best as **one core with selectable procedures**, not as ten independent games that must all be learned. Clanfire plus Emberfall supplies a sensible first route; the later skins justify their space through different pressures and activities. The worked exchange supports the actual combat procedure, including a defender retaining its action. The complete Manual and selected skin are a substantially stronger learning packet than the Quickstart alone.

The burden is concentrated in stateful qualifications: which Pressure effects persist, which pending effects were discarded, when a toll applies, which pool pays, and what survives a crisis reset. Those are legitimate parts of this design, but “the dice are simple” should not become “there is no procedure to track”. An AI-first release particularly needs those qualifications to survive compression and resume.

### Compact chat: concrete acceptance probes

These are proposed probes, not sessions already performed. Run them with an isolated model that receives only the assembled compact packet, and compare against the core rules.

| Probe | Required answer or behaviour | Information issue |
|---|---|---|
| Two sides begin a fight without a fictional advantage | One side roll each, higher first, ties rerolled; order retained through the fight | Full round/initiative procedure is not in the Quickstart |
| A character defends and later takes its turn | Defence does not consume its action | Cannot safely substitute another RPG’s reaction economy |
| A Pressure cost crosses a penalty/toll step | Resolve using the action-start snapshot; do not retroactively tax that action | Compact summary does not provide the whole timing rule |
| A one-test penalty fires, Pressure falls below it, then rises again | Discard it on recovery; do not rearm until a crisis reset | Needed for skins with explicit next-test penalties |
| A roll and its mandatory conditional cost compete for the last token | Reserve the mandatory cost; never spend the same token twice | Requires the fuller Luck-cost procedure |
| A raw natural 1 loses an opposed margin comparison | Natural success is not automatic victory over the other successful side | Packet should be tested for interpretation, even where the rule is present |

For ordinary chat without source access, use the existing full packet as the baseline. A short, machine-oriented supplement is worth considering only if measured comprehension justifies its length. Add it to the prompt layer, not the two-page Quickstart. Do not claim that a model which asks to load missing rules has failed: that is the correct bounded behaviour.

For repository agents, section retrieval, persistent dice and explicit state help substantially. The remaining challenge is to prevent an agent from treating a successful command as proof that the chosen fictional operation was legal. Tests should audit that translation step separately.

## 5. Grouped nits

- **Back-cover accuracy:** Replace “Roll under a d20” with “Roll a d20 at or below your attribute.”
- **README positioning:** “Everything else is flavour-text” undersells and misdescribes the mechanical skin procedures; “Skins add setting-specific procedures” is accurate.
- **Quickstart Luck timing:** Replace “before any spending on that roll” with “before nudging that roll” to avoid implying that upfront ability costs leave the Luck target unchanged; this shortens rather than lengthens the text.
- **README Luck shorthand:** Distinguish maximum pool size from the current-token Luck-test target; do not let “pool size is the score” imply that spent tokens leave the test target unchanged.

None requires lengthening the Quickstart. Its two-page constraint remains unchanged; any later edit to that file still needs the repository’s actual PDF gate.

## 6. Questions for the author

These do not hold up the rest of the review. They identify choices to settle before tests encode an interpretation.

**Unnudgeable magic and the opponent’s die.** The harness’s `--no-nudge` prevents changing the caster’s die, while an opposed participant can still pay to change the other die. Is that the intended reading of an unnudgeable magical test, or should the protected outcome include both dice? Retain the current behaviour until the intended scope is stated; do not silently broaden the prohibition.

**Free Traders misjump fuel.** Does the additional “Fuel +2” outcome mean two ticks in total for that leg, or two beyond the normal jump’s fuel cost? State the total explicitly in a worked failed leg.

**Symmetric pilot contests.** When both pilots roll DEX for advantage, which side is defending the existing position, and therefore owns a tie? The general opposed rule works once that role is named. Is a no-advantage tie intended when neither side holds a prior advantage?

**Compelled crisis tests.** For Service Duct’s SYS consequence test, confirm whether it is a compelled response rather than a chosen new attempt for toll purposes. This should be a consistent application of the settled choice-based toll rule, not a new involuntary resource drain.

**Release package and approval.** Which exact files constitute the proposed storefront product, as opposed to repository support material? Record the platform’s ruling against that package and the actual authorship workflow, rather than a generic description of “AI assistance”.

**Investigation thresholds.** Will “routinely” mean at least half of eligible observations within a declared playtest stratum, or another proportion? Is the summariser’s strictly-more-than-three-roll interpretation of “a few” the intended provisional investigation threshold? These are measurement decisions, not changes to Pressure or recovery.

## 7. Strengths worth keeping

**Keep the numerical engine.** The checks performed here support it. Natural versus adjusted faces, defender ties, attacker-margin damage and the capped creation ledger are coherent. The results do not demonstrate universal balance, but they give no reason for another speculative tuning pass.

**Keep the explicit Pressure lifecycle.** Cumulative effects, per-character next-test penalties on a shared track, discard without rearming, action-start snapshots and lasting consequences separate from the reset are worth their precision. The principal repair is representing all ways a crisis can arise and be resolved, not simplifying away the design.

**Keep the character provenance model.** Creation snapshots plus replayed advancement avoid confusing a capped creation price with the cost of later improvements. Do not replace that with “recalculate the current build and infer what was spent”.

**Keep persisted dice and idempotent receipts.** Deferred decisions should retain their original rolls. The existing architecture and regression cases take this seriously, including a separate persisted Deflection stage. Add new features through that machinery rather than inventing ad hoc reroll paths.

**Keep the public export allowlist.** Exporting selected fields is safer than trying to redact arbitrary private objects. The removal of free-form conditions from public exports was a considered earlier fix; this review does not reopen it.

**Keep Emberfall and the fiction-first constraints.** The teaching round, stated stakes, legitimate alternate approaches, limits on unchanged retries and insistence on real trade stakes are useful safeguards against both player exploitation and AI improvisation.

**Keep honest analytical labels.** Historical models are identified as historical, completed and incomplete telemetry are separated, and the summary avoids presenting repeated character-session observations as independent population evidence. The playtest programme should preserve that restraint.

## 8. Playtest recommendations

### 8.1 Separate mechanical verification from balance screening

Repair F02–F05 before treating unattended sessions involving those features as evidence. Close F07’s workflow gap and F08’s accounting gap before analysing Luck use. Run the real repository suite and validators on a checkout; the checks in this review do not substitute for that gate.

A deterministic regression packet should force the rare cases, rather than hoping that ordinary sessions encounter them. Use fixed dice to cover both sides of each boundary. The acceptance checks in the findings form its minimum content: forced crises below and at 5, nested crisis tests, Beast Bond funding, simple action-taking checks, conditional cost reservation and Luck-raise events. Include the concurrent-reader case when hardening that path.

Retain the existing controls for current-Luck targets, immutable naturals, cancellation, no double charging, crisis overflow, personal Insanity, injury/Deflection, side order, state rollback and replay. A repair is not successful if it achieves the new case by weakening those guarantees.

These are harness tests, not playtests. Conversely, a fluent session cannot establish transaction correctness.

### 8.2 Smallest credible screening programme

I recommend **40 completed AI-run sessions as an adaptive screening floor**, plus deterministic rare-case probes and a few mode/onboarding trials. This is not a sample-size claim about all possible players or campaigns.

| Set | Skins | Party sizes | Repetitions | Completed sessions |
|---|---|---|---|---:|
| Sentinel matrix | Clanfire, Rust & Domes, Candlelight Dungeons, Whispers in the Fog, Twilight of the Northlands | 1, 2, 4 | Two distinct scenario/seed runs per cell | 30 |
| Remaining-skin screen | Iron & Ruin, Time Odyssey, Briar & Benedictine, Service Duct Blues, Free Traders of the Drift Marches | 1 and 4 | One run per cell | 10 |

The sentinels exercise the default onboarding skin, an unavoidable Pressure action cost, strong spell costs and attack modifiers, personal Pressure, and the most elaborate shared-resource/travel/combat package. The other five still need live procedural coverage; their forced edge cases belong in the deterministic packet even if they do not occur in their single screening run.

Aim for about 20 explicitly recorded scene-scale beats per session, or clearly record the actual length and reason for early ending. Do not manufacture rolls to reach a denominator. Use the printed milestone cadence and legitimate rest opportunities; a no-rest or no-milestone stress test is a separate labelled scenario, not the ordinary baseline.

Two runs per cell can reveal implementation errors and generate pacing hypotheses. They cannot establish a stable distribution or a universal claim of balance. When a cell flags, add at least four fresh, matched runs before describing the behaviour as recurrent; continue if the result depends strongly on scenario or policy. An evenly covered expansion is 60 sessions: ten skins × three party sizes × two runs.

Use at least two scenario types for repeated cells, with meaningful physical, social, exploratory and supernatural demands where appropriate. Do not punish a specialised build by forcing arbitrary weak-stat rolls. Record when the fiction genuinely prevents reusing a signature attribute.

### 8.3 Keep the conditions of each run inspectable

A small sidecar run manifest is sufficient; it need not become another rule subsystem. Record:

- rules commit, campaign/run identifier, scenario revision and seeds;
- model/version and relevant generation settings, plus whether the same model plays both Custodian and players;
- skin, tone budget, roster and starting pools, optional modules such as Delvekit and Injury;
- declared Luck-spending policy, rest/milestone opportunities, shared-hazard charging and Pressure-purge policy;
- rule lookups, manual interventions, overrides, corrections and exclusions.

A model facing itself is useful for integration testing but not independent confirmation of its own rulings. Sample sessions should receive an adjudication audit against the source rules. Change the adjudicating model or use a human check for a subset of consequential decisions; do not treat agreement alone as ground truth.

Keep ordinary play and adversarial policy runs separate. A rule-lawyering player who aggressively exploits a favourite attribute is a useful stress condition, not the only intended audience. Likewise, a Custodian who continually grants generous purges should not be silently pooled with a stricter one.

### 8.4 Operationalise the two reopen triggers

**Luck.** Use the summariser’s newly-at-or-below-one measure among character-sessions starting above one. Report initially low pools separately. Preserve the minimum within the first half; a later milestone refill should not erase an earlier depletion episode.

The current midpoint definition is defensible for scene-scale records: take `floor(last recorded beat number / 2)`, with the cutoff at the event sequence that closes that beat. The already-fixed bug of counting the following scene should remain fixed. With no beat records, midpoint evidence is unavailable. With very few beats, report the limitation rather than calling starting Luck a rich trajectory.

Show both the character-session proportion and the distribution of within-session proportions. Four characters sharing an adventure are not four independent replications. Show depletion by starting Luck, skin and party size; annotate rests, milestones, ability costs and nudge spending. Include the small accounting repair in F08 and reconcile pool movements before comparing recovery rates.

**Red line.** Use strictly more than three affected PC rolls as the provisional interpretation of “more than a few”, matching the current configurable default. Affected means Pressure was at least 4 at the roll’s action-start snapshot, not merely that an upfront cost raised the track to 4 before the die appeared.

Report party-track and personal-track windows separately. Preserve left- and right-censoring. A window still open at session end is not a completed short window; if it has already exceeded three rolls it is nonetheless a confirmed exceedance with an unfinished duration. Where windows persist across sessions, link them by campaign, track and cycle for a supplementary longitudinal view rather than pretending each session created a new independent window.

Also show beats, combat rounds and affected rolls by actor. A fixed roll count describes different amounts of fictional time for one PC and four, and an opposed exchange can contribute more than one PC roll. Do not change the definition after seeing which produces the preferred conclusion.

**“Routinely.”** My provisional investigation flag would be at least half of the eligible observations in a predeclared skin/party/policy stratum, supported across the repeated scenarios. This is a request to inspect the causes, not an automatic rules change or a significance test. Put the exact numerator, denominator and censoring beside every flag. Sparse cells should be expanded before decisions are made.

### 8.5 What the current summary can and cannot establish

The summary can describe low-Luck observations, recorded crisis frequency, high-Pressure roll exposure and roll attributes. Its explicit handling of missing beats and incomplete sessions is valuable. It does not prove that the recorded action was eligible, that a cost was reserved, or that a selected modifier matched the fiction.

The prior Stage 4 review already notes that a defender’s roll event inherits the attacker’s method. Do not relabel that as a newly discovered bug. **It remains a prerequisite for interpreting per-character method shares:** record the defender’s declared method separately, or restrict method analysis to correctly attributed acting rolls and label that restriction. Role-separated attribute shares are useful too; repeated defence rolls should not automatically be interpreted as a player steering every choice into one favourite stat.

Pressure events retain sources, but the summary is not yet a complete causal account of why the fuse filled. Add a report of gains by source, distinguishing requested increments from realised changes at the cap, and ordinary threshold crises from forced skin crises. Do not mistake narrative labels alone for a reliable action taxonomy.

For each audited session, reconcile initial pools, gains, expenditure and final pools; account for crisis resets and discarded overflow; verify the target and duration of every lasting effect. The known roster-retirement limitation should be resolved or explicitly constrained when casualties change the participating party. A nominally complete JSONL history can still contain a systematic rules error.

### 8.6 Onboarding and mode trials

Run a small, separate set of entry tests: the full book plus Emberfall at a human table; isolated compact chat; isolated full chat; and repository-agent play through setup, deferred settlement, save and resume. The goal is to find stalls, invented rules and lost obligations, not estimate player-population probabilities.

A human session or two is particularly useful for whether the chosen terminology and first-play route are intelligible. The planned small human trickle should remain indicative. Do not inflate it into a quantitative validation claim.

For mode comparisons, reuse the same scripted decision points and expected rulings. A compact model that requests missing sections is preferable to one that confidently invents initiative. An agent that cannot express a Beast Bond nudge should report the limitation instead of laundering it through Luck adjustments.

### 8.7 Exit gates

Proceed towards GOLD when the following are evidenced, not merely asserted:

1. The targeted representation defects have tests; the full suite, repository validation and a real throwaway campaign workflow pass on the chosen commit.
2. Chat and agent entry routes clearly state what context and tools they require; rare printed procedures have exercised paths.
3. Screening logs reconcile, significant manual workarounds are disclosed, and any reopen flags have been examined with Barry before changing rules.
4. The actual release package has a confirmed distribution route, with naming and provenance decisions recorded.

Then freeze rules and writing and undertake the deferred layout pass. Preserve the exactly-two-page Quickstart and its full-book placement through the existing release checks. Nothing in this review requires pre-GOLD aesthetic changes or a longer Quickstart.

## 9. Verification appendix

### Exact modules executed

Git blob hashes were calculated as SHA-1 of `b"blob " + byte_length + b"\0" + content`, matching the connector’s blob identifiers:

| Module | Verified Git blob SHA |
|---|---|
| `tools/_rules.py` | `64d5d3a4da9777104f72e166e89b14d66251d16d` |
| `tools/_pressure.py` | `fb3b6684853eab80268084f0f03289fa8e47dc2f` |
| `tools/_dice.py` | `050943317bfafc70e46c2a053171ee575fc77710` |

The enumerations exercised `_rules.py`; the targeted state sequence exercised `_pressure.py`. Restoring `_dice.py` does not establish that the full random/CLI integration was tested. No source module was patched to obtain these results.

### Minimal reproduction of F02

Run from the pinned repository root. This is deliberately a minimal declared skin fixture, not a substitute manifest. The defect is independent of the names of the Pressure steps.

```python
from copy import deepcopy
import sys
sys.path.insert(0, "tools")
import _pressure

skin = {"pressure_scope": "party", "pressure_track": "Fatigue"}
actors = ["caster"]
state = _pressure.new_pressure(skin, actors)
_pressure.change(
    state, skin, actors,
    amount=2, source="Arcanum upfront cost",
    category="action_cost", actor="caster",
)
assert state["tracks"]["party"]["current"] == 2
before = deepcopy(state)
try:
    _pressure.crisis(
        state, skin, actors,
        target="caster", table_result=[1],
        description="Crisis required by failed Arcanum",
    )
except ValueError as exc:
    print(type(exc).__name__ + ": " + str(exc))
else:
    raise AssertionError("Reviewed code unexpectedly accepted the crisis")
assert state == before
```

Observed: `ValueError: this track has no pending crisis`.

The proposed regression after repair should invert that expectation and assert one correctly caused crisis/reset without fabricated Pressure gains.

### Limits of the numerical conclusions

The creation enumeration checked the current ledger over the finite legal score space, not encounter balance or a distribution of likely character choices. The damage checks included raw versus adjusted naturals, edge 0–4 and soak 0–4; those test values do not grant equipment that a skin does not offer. Resolution comparisons used independently written expectations, not agreement between two callers of the same helper.

I did not rerun the historical coupled-combat, Luck-policy or Pressure-pacing analyses. Their conditional conclusions are not converted here into universal claims about difficulty, sustainability or optimal builds. The correct next evidence is logged play under stated policies, with the implementation gaps removed.

## 10. External sources

All external sources were retrieved on **2 October 2026**. Repository evidence is cited by pinned path and section/function in each finding.

**[S1] DriveThru Partners — Product Standards Guidelines.** Sections “AI-Generated Content Policy” and “Creation Method” filter. The page returned at final verification is labelled **7 July 2026**. An earlier progress message referred to September; this review does not establish a September policy change. The relevant claim is the operative wording retrieved for this review, not when it first took effect.  
`https://help.drivethrupartners.com/hc/en-us/articles/12780748778135-Product-Standards-Guidelines`

**[S2] Steel And Sinew — official Steam listing.** Title, developer/publisher, genre and announced release status.  
`https://store.steampowered.com/app/4630390/Steel_And_Sinew/`

**[S3] Whispers in the Fog — official game website.** Title and psychological-horror description.  
`https://whispersinthefog.com/`

---

**Bottom line:** Retain the game. Repair the missing procedural representations. Make the two AI entry modes explicit. Use traceable playtests to investigate pacing, rather than treating code tests or model agreement as proof of balance.
