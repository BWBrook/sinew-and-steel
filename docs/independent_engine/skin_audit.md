# Independent skin mechanics audit

## Decision

**TARGETED REPAIR.** The ten skins remain recognisably lean and most differences are sound genre dials. On the baseline snapshot, several underspecified procedures admitted adverse literal readings, three cross-cutting ambiguities could change outcomes materially, and the Twilight travel rules directly contradicted one another. The later core no-repeat rule closes unchanged retry loops globally, so the port, scan, Song, and time findings are best treated as skin-level procedure clarifications rather than proof that ordinary play creates free resources. None requires a new subsystem.

This audit did not read `tools/analysis/*`, `docs/engine_atlas*`, or their outputs. It reconstructed interactions from the core rules, all ten manifest skins, Candlelight Delvekit, the dice/tracker tools, and the Delvekit generator.

### Implementation disposition (2026-09-20)

The ranked findings below preserve the original `a77d476` rules evidence and pre-repair calculations. The assigned skin-level repairs are now implemented as follows:

- **Findings 1 and 5:** Free Trader trade now requires a concrete stake resolved once per port, and Ship Shares can repair Hull only during a dedicated repair scene outside combat. Jump tests now apply only to separately stated active hazards; unfilled roles are not automatic failures.
- **Finding 2:** Quick Scan has one free use per scene and is limited to available sensor evidence. Repeated scans require a materially changed information state, access, equipment, or method with a stated time/risk; Deep Scan now provides targeted depth.
- **Findings 3, 4, and 8:** Twilight now uses one test for a normal journey and up to three only for separately stated dangers; Song of Rest is once per camp/night with no retry; Assemblies use one spokesperson's HRT test and fictional preparation for Advantage/Disadvantage. I removed the group threshold variant because retaining a second, party-size-sensitive resolution mode would add complexity without serving the lean default.
- **Finding 7:** one Anomaly test now settles a historical intervention, and retry requires materially new information, method, or opportunity. Per the integration decision, successful intervention does not yet add Anomaly.
- **Finding 11:** Free Trader, Candlelight, Twilight, and Whispers Knacks now state their complete costs. Old Name and Detective Intuition cost Fate once; Stout-Heart and Veteran's Nerves cannot pay for ignoring Pressure by marking that same Pressure.
- **Resolved in the integration decision:** Pressure reaches 5, triggers a crisis, and resets to 0; overflow is deliberately discarded. Finding 6 remains as baseline sensitivity evidence, not an open rules defect.
- **Applied by the parallel Delvekit integration:** a brief rest now spends a turn and advances a stated danger clock while the site remains dangerous; the expedition boundary is explicit; Soft tiny variety fill no longer forces a trap or solo monster. Findings 9 and 10 retain the baseline evidence and now include post-repair verification.
- **Applied by the parallel core integration:** nudged results are bounded to 1-20 and cannot manufacture natural results. The nudge item in Finding 12 is retained as baseline evidence.
- **Deferred outside this skin tranche:** Beast Bond, medical aid, and fuel pricing remain open evidence in Finding 12.

Line references in the baseline findings identify the original passages; repairs may have shifted their current line numbers.

## Target and scope

The target is procedural robustness under adversarial but rules-literal play: whether a player can create unbounded resources, information, or retries; bypass a stated cost; obtain materially different outcomes from equally plausible readings; or make a procedure fail solely because of party size. The estimands are exact success probabilities, expected resource gain per permitted action, probability of at least one failure in a multi-roll procedure, and generated-feature frequency. These are properties of the rules and generator, not estimates of table enjoyment.

Assumptions:

- legal player scores are 6-16;
- Advantage does not stack, matching `tools/_dice.py:11-25`;
- repeated actions are allowed only where the text supplies no limit and the fiction can plausibly permit another attempt;
- a Custodian can always veto absurd fiction, but a procedure should not depend on an unstated veto to close an obvious loop;
- Twilight combat positions and injuries are outside this workstream except where they touch Hope, Companionship, rest, or travel;
- Delvekit frequencies use 1,000 deterministic seeds per size/difficulty cell, with binomial Monte Carlo standard error at most 1.581 percentage points.

Reproduce the exact counterfactual tables and the generator results for the current working tree:

```bash
uv run python tools/analysis/independent_skins.py --delve-seeds 1000
```

The baseline 48.6% tiny/Soft trap-room result used commit `a77d476`. The current command returns 24.2% for the same seeds. Reproduce the baseline generator result without changing the working tree:

```bash
git worktree add --detach /tmp/sns-skin-baseline-audit a77d476
mkdir -p /tmp/sns-skin-baseline-audit/tools/analysis
cp tools/analysis/independent_skins.py /tmp/sns-skin-baseline-audit/tools/analysis/
uv run --project "$PWD" python /tmp/sns-skin-baseline-audit/tools/analysis/independent_skins.py --delve-seeds 1000
git worktree remove --force /tmp/sns-skin-baseline-audit
```

## Ranked findings

### 1. Free Trader port calls lack an explicit trade input — wording risk, now closed

**Evidence.** Every PC receives a free Expertise and Knack (`skins/free_traders_of_the_drift_marches.md:67-85`). A trade success creates `+1 Ship Share` or deletes Debt, with no cargo stake, capital cost, share ceiling, or requirement to complete a job (`skins/free_traders_of_the_drift_marches.md:160-182`). Merchant Broker rerolls a failed trade check once per port call (`:77`, `:174`). A safe-berth rest restores the Fate that can pay the reroll cost (`:34-41`).

With score 16, free trade Expertise gives Advantage: `P(success)=0.96`. Merchant Broker makes `P(success after the allowed reroll)=1-(1-0.96)^2=0.9984`. Choosing a Share produces **0.9984 Shares per port call**, so the expected time to mint ten Shares is **10.016 calls**. Even score 10 produces 0.9375 Shares per call.

**Baseline adversarial sequence.** Take Merchant Broker and EDU or SOC Expertise. Enter a port with no cargo. Make the Expertise trade test. On the 4% first-check failure, invoke Broker and pay its cost with one Fate. On success choose `+1 Ship Share`. Rest in the safe berth to recover the Fate. Call again at the same port after a nominal departure, or repeat across nearby ports. The baseline trade paragraph did not name the cargo, job, or claim being converted.

**Classification.** This was a wording risk rather than a confirmed mint in ordinary fiction: real port calls consume time, travel, fuel, and opportunities, and the integrated core bars unchanged retries. Naming the concrete trade stake is still valuable because it makes the intended input explicit and prevents an empty-hold reading.

**Minimal repair.** Add after `Trade test (one per port call)`:

> A trade test requires one cargo lot, completed patron job, or other concrete stake. Resolve each stake once at a port. Success converts that stake into 1 Ship Share or clears 1 Debt; it never creates value from an empty hold.

Do not add a detailed cargo economy unless play later demands it.

### 2. Quick Scan and Deep Scan lacked a firm mode boundary — ambiguity, now closed

**Evidence.** Quick Scan gives Advantage, one concrete data point, no cost, and no frequency limit. Deep Scan is once per scene, costs RES or Stress, rolls straight, and yields two yes/no answers (`skins/service_duct_blues.md:73-81`).

At SYS 10, one Quick Scan succeeds 75% versus 50% for Deep Scan. Four Quick Scans produce **3.0 expected concrete data points** and at least one success with **99.6094%** probability, still at no cost. At SYS 13, four yield 3.51 expected points. The sample scanner already grants Advantage on scans (`:193-200`), but this cannot improve Quick Scan because sources do not stack.

**Baseline adversarial sequence.** In one anomaly scene, run Quick Scan on the field, conduit, victim, and logs as four nominally distinct scans. Collect each successful data point. Use Deep Scan only if a targeted yes/no remains. This sequence treats each nearby object as a new attempt even though the underlying information state has not changed.

**Classification.** The integrated core no-repeat rule already rejects unchanged repetitions. The skin clarification adds the missing qualitative distinction: Quick Scan samples available sensor data broadly, while Deep Scan pays for targeted truthful depth within those sensors' reach.

**Minimal repair.** Change Quick Scan to:

> **Quick Scan (once per scene):** Test SYS with Advantage for one concrete data point. A repeat scan needs a materially new target or method; otherwise it costs time and marks +1 Stress before rolling.

### 3. Twilight travel had incompatible one-roll and three-role procedures — now closed

**Evidence.** The Adventurer-facing rule says each travel leg calls for **one** test (`skins/twilight_of_the_northlands.md:119-130`). The Lorekeeper procedure assigns up to three roles, gives each a test, and treats an unfilled role as failure (`:174-184`). “Up to three” is therefore misleading: every omitted role still inflicts its failure.

With three equal score-12 roles, one test fails 40% of legs. Three independent tests produce at least one failure on **78.4%** of legs and all three succeed on only 21.6%. With one or two PCs, at least one role is automatically failed before dice. Free Traders repeats the same small-party problem for Astrogator, Engineer, and Watch officer (`skins/free_traders_of_the_drift_marches.md:103-113`).

**Consequence.** The same journey can produce one Fatigue check or three coupled hazards. Party size, rather than fiction or difficulty, determines unavoidable attrition.

**Minimal repair.** Use one rule in both skins:

> A normal leg uses one role test chosen for the leg's main danger. A perilous leg may use up to three role tests if those dangers are separately present. An unfilled role gives no benefit; treat it as failure only when the corresponding danger is active and was stated before assignments.

This preserves role texture without requiring three PCs or three failures per journey.

### 4. Song of Rest had no explicit camp cadence — ambiguity, now closed

**Evidence.** A successful HRT test lets every party member regain 1 Hope or clear 1 Fatigue, with no use limit, time unit, or failure consequence (`skins/twilight_of_the_northlands.md:132-135`). This is stronger than personal short-rest recovery and stacks across repeated songs.

**Baseline adversarial sequence.** At any camp, the HRT 14 singer repeats songs until each depleted member is full. Each attempt succeeds 70%; expected attempts per successful party-wide recovery are 1.429. This requires treating each new song as a fresh opportunity despite no material change; the integrated core now rejects that reading, and the skin states the once-per-camp cadence directly.

**Consequence.** Travel Fatigue and Hope expenditure become optional wherever the party can pause, undermining both the travel track and Companionship decisions.

**Minimal repair.** Replace the first clause with:

> **Song of Rest (once per camp or night; no retry):** after the company makes camp, one PC may test HRT...

### 5. Ship Share hull repair had no timing procedure — literal timing gap, now closed

**Evidence.** Spending a Share clears a Hull Damage tick with no timing, location, action, or access requirement (`skins/free_traders_of_the_drift_marches.md:114-122`). Hull Damage is also the live combat defeat clock (`:203-220`).

**Adversarial sequence.** Begin a round at Hull 4/6 with several Shares. A minimum-damage hit moves Hull to 5. Spend a Share immediately to return to 4. Repeat between every hit. Liquid money functions as ablative armour until the pool empties, even in hard vacuum with no repair scene.

**Consequence.** Economic reserves erase tactical attrition at arbitrary timing, and the fiction of yard repairs becomes irrelevant.

**Minimal repair.** Change the spend option to:

> clear 1 Hull Damage in port or during a dedicated repair scene with tools and access; Shares cannot clear Hull Damage during an exchange.

### 6. Multi-point Pressure overflow changes marginal costs — deliberate integration choice

**Evidence.** Core Pressure triggers at 5 and resets to 0 (`rules/core/adventurers_manual.md:295-307`; `rules/core/custodians_almanac.md:59-78`). Skins add two or three points at once: Iron Wrack/Wyrd (`skins/iron_and_ruin.md:69-75`), Candlelight Greater Spell/Arcanum (`skins/candlelight_dungeons.md:82-96`), Twilight Invocation/Reckoning (`skins/twilight_of_the_northlands.md:98-113`), and Whispers Incantation/Unspeakable (`skins/whispers_in_the_fog.md:73-85`). None says whether points beyond 5 survive the reset.

At Pressure 4, `+3` yields either crisis then 0 if overflow is discarded, or crisis then 2 if marked sequentially. Under discard, a Wyrd deliberately cast at Doom 4 pays only one effective Doom, whereas the same cast at Doom 0 leaves Doom 3. The tracker CLI can also store values above the maximum unless `--clamp` is supplied (`tools/trackers.py:85-98`, `:119-132`); clamping silently selects the discard interpretation and still does not trigger a crisis.

**Classification.** The baseline was materially underspecified. Integration has now chosen the lean rule: reaching 5 triggers the crisis and resets Pressure to 0, discarding overflow. The table below remains useful sensitivity evidence: high-tier actions taken at Pressure 4 consequently have lower effective retained Pressure, but the crisis itself is the consequence rather than convertible currency.

**Integration disposition.** Keep reset-to-0 with discarded overflow and state it explicitly in core. Do not carry excess points through a crisis.

### 7. Time Odyssey did not say when an intervention was settled — retry ambiguity, now closed

**Evidence.** Altering major events calls for INT or ING; only failure marks Anomaly (`skins/time_odyssey.md:60-70`). Journals can grant Advantage on reconciliation (`:138-146`). The prose nevertheless claims paradox is paid for in Anomaly (`:146`).

At INT 16 with Advantage, one intervention succeeds 96%. If recalibration permits three attempts, success reaches **99.9936%** and the expected failures, hence expected Anomaly marks, are only **0.0417**. Even a single successful city- or epoch-scale change is mechanically free.

**Baseline conditional adversarial sequence.** Use journals and calculations to gain Advantage, attempt the historical alteration, recalibrate after failure without changing the method or opportunity, and retry. Stop on success.

**Classification.** The global no-repeat rule closes unchanged recalculations, and the skin now confirms that one test settles the intervention. A successful major alteration remains free of Anomaly: the baseline probabilities alone are not evidence that success needs a surcharge.

**Minimal repair applied.** Add:

> One test settles a historical intervention; retry only after materially new information, method, or opportunity.

This clarifies the procedure without penalising successful interventions absent play evidence.

### 8. Fixed Twilight Assembly thresholds strongly encoded party size — now closed

**Evidence.** Every speaking PC rolls once, while thresholds stay 3 and 5 (`skins/twilight_of_the_northlands.md:186-193`). At HRT 12 without token spends, the exact chance to meet threshold 3 is 0% for one speaker, 5.75% for two, 27.675% for three, and 64.415% for five. Threshold 5 is mathematically impossible for one or two speakers and succeeds only 15.088% of the time for five.

**Consequence.** A solo or two-PC company cannot persuade a petty or great lord on equal individual competence, while large parties gain several extra trials and natural-1 opportunities.

**Repair applied.** Use one spokesperson's HRT test. Concrete preparation and leverage grant Advantage; hostility, broken trust, or poor standing grant Disadvantage. This keeps solo play viable and avoids a second party-size-sensitive resolution mode.

### 9. Delvekit made attrition discretionary while “rest briefly” was a formal turn — now closed

**Evidence.** Rest is an exploration-turn choice (`skins/candlelight_delvekit.md:44-61`). At the end of a risky or time-eating turn the Custodian **may** advance Fatigue, light, factions, or threat (`:63-71`). Core short rests restore both one Luck and one Stamina (`rules/core/adventurers_manual.md:166-200`). Hard mode says rest should be pressured, but supplies no cadence (`skins/candlelight_delvekit.md:364-390`).

With no mandatory cost, a character at Fortune 4/12 and Stamina 1/5 reaches full in eight rest turns. This is a conditional loop because an alert Custodian can move factions or the horror, but the formal procedure gives no default to follow.

**Repair applied.** A brief rest now spends one turn, advances a stated light/resource/faction/threat clock while the site remains dangerous, and grants one recovery benefit. The rules also define a delve as one expedition between settlement or sanctuary visits, so stepping outside a doorway does not reset the zero-Stamina ladder.

The baseline minimal repair was:

> Each brief rest spends one turn. After the first rest in the same secured area, every further rest automatically marks light/resource pressure or advances a faction/threat; the Custodian chooses which.

Also define “in a delve” for the zero-Stamina survival count as one expedition from settlement/sanctuary departure to return; otherwise doorway retreats can be argued to reset the Soft/Medium ladder (`:319-332`).

### 10. Tiny Delvekit feature flooring nearly doubled Soft lethal-trap-room incidence — now closed

**Evidence.** Soft config sets lethal trap probability to 0.25 (`tools/_delvekit.py:24-37`). Tiny sites are then forced to at least three feature classes, and the fill loop can force a trap at probability 1 (`:1377-1435`). Every generated trap uses `grimtooth_lethal_room` (`:1479-1514`). Docs promise lower trap-room chance and that most Soft traps hurt before killing (`docs/candlelight_delvekit.md:322-332`; `skins/candlelight_delvekit.md:334-347`).

Across seeds 20260920-20261919, **48.6%** of tiny Soft sites contained a lethal trap room, compared with 26.3% of medium Soft and 26.2% of large Soft sites. Tiny Soft also averaged 3.774 of seven feature classes, versus 3.103/3.244 at larger sizes. All checked structural invariants passed.

**Repair and verification.** Soft tiny variety fill now excludes both `trap` and `solo`, leaving their configured marginal rolls intact. Re-running the same 1,000 seeds gives **24.2%** trap-room incidence and **23.2%** solo-monster incidence, with zero checked invariant failures across all 9,000 post-repair sites. The original 48.6% figure was room-tag incidence, not a player death rate.

### 11. Generic Knack costs collide with entry-specific costs — now closed

**Evidence.** Free Traders says every Knack use costs 1 Fate or 1 Strain, while Old Name again says “Spend 1 Fate” (`skins/free_traders_of_the_drift_marches.md:67-80`). Whispers does the same for Detective Intuition (`skins/whispers_in_the_fog.md:126-138`). Candlelight makes all Knacks cost Fortune/Fatigue and then says Turn Undead failure marks Fatigue “regardless” (`skins/candlelight_dungeons.md:133-148`). Twilight Stout-Heart and Whispers Veteran's Nerves may pay their generic cost in the same Pressure they ignore, giving no net protection (`skins/twilight_of_the_northlands.md:77-90`; `skins/whispers_in_the_fog.md:126-138`).

**Consequence.** Reasonable tables charge Old Name/Detective Intuition either once or twice. Pressure-ignoring Knacks offer a dominated payment option that looks like a trap for the player.

**Repair applied.** Replace each generic section-wide charge with an explicit cost beside every Knack, and mark any extra charge as **additional**. Old Name and Detective Intuition cost one Fate, once. Stout-Heart and Veteran's Nerves cost one personal Luck token, so neither can pay by marking the Pressure point it ignores.

### 12. Several recovery and equipment rules are dominated or incomplete

- **Free Trader medical aid:** it spends one of four supplies, rolls EDU, risks Strain and patient harm, and restores only +1 Stamina (`skins/free_traders_of_the_drift_marches.md:186-195`). Core short rest restores the same +1 without those costs (`rules/core/adventurers_manual.md:193-203`). If “serious injury” blocks ordinary rest, say so; otherwise make successful aid +2 or usable when rest is impossible.
- **Free Trader fuel:** Fuel Depletion defines becoming stranded but no refuel price or procedure (`skins/free_traders_of_the_drift_marches.md:93-100`). Add “refuel in port for 1 Share; desperate fuel creates Debt or a patron obligation.”
- **Clanfire Beast Bond:** a 3-token substitute pool has a terminal consequence but no defined recovery, ownership limit, or stacking rule (`skins/clanfire.md:76-80`), while a milestone can grant another bond (`:150-163`). Add “one active bond per PC; costly care restores the pool at a milestone or after a dedicated clan-safety scene.”
- **Nudge bounds (resolved in parallel core integration):** the baseline core permitted “any number” of tokens but did not say adjusted results remain 1-20 (`rules/core/adventurers_manual.md:180-189`), while the tool rejected results outside 1-20 (`tools/_dice.py:106-118`). Core now states the 1-20 bound and distinguishes adjusted endpoints from natural results.

## Coverage and disposition

| Skin / add-on | Distinct procedures checked | Quantitative or adversarial check | Disposition |
|---|---|---|---|
| Briar & Benedictine | Providence, Insight, poultice, fail-forward clues, Sin gates/crises | Party Stamina transfer and rest comparison | No unique exploit; fail-forward clues are intentional. Poultice is useful only under time pressure, which is acceptable if stakes are stated. |
| Clanfire | Totem Mark, Beast Bond, Shadow-4 rite surcharge, Vision Glass, milestone pools | Pool stacking/recovery sequence | Lean and functional; define one active Bond and its refresh. |
| Iron & Ruin | Four sorcery tiers, Fortune/blood substitution, Doom costs and crises, Heroic Act | `+2/+3` Pressure overflow table | Tier contrast is intentional; core now explicitly discards overflow after one crisis. |
| Time Odyssey | INT/ING Anomaly tests, historical intervention, journal Advantage, boon recovery | Exact single/repeated intervention probabilities | One test now settles an intervention; unchanged retry is closed without adding Anomaly on success. |
| Rust & Domes | Psionic Stamina/Luck substitution, margin scaling, Heat-4 escalation | Cost-path and ordering trace | No runaway unique to the skin. State whether a failed psionic test at Heat 4 marks one or two Heat when the generic risky-test trigger also applies. |
| Candlelight Dungeons | Spell tiers, Fatigue gates, free Knack/Expertise, Arcane Flex, Second Wind, Turn Undead | Spell cost/Pressure overflow and double-cost trace | Tier ladder follows the deliberate core overflow rule; every Knack now states its whole cost and Turn Undead names its additional failure cost. |
| Service Duct Blues | Reroute, Buffer, Cross-Training, three scan modes, Stress-4 gate | Exact repeated-scan probabilities | Quick Scan is now once per scene and limited to available data; Deep Scan supplies targeted truthful depth. |
| Whispers in the Fog | Rite tiers, Insanity gates, Knacks, light clock | Knack double-cost and high-tier overflow trace | Light clock is sound; Knack costs are explicit. Overflow follows the deliberate core reset-to-0 rule. |
| Free Traders | Knacks/Expertise, three jump roles, fuel/hull/debt clocks, Shares, trade, medical aid, ship combat | Exact trade yield; hull-repair witness; role-failure probabilities | Trade input, repair timing, jump hazards, and Knack costs repaired; refuel and medical procedure deferred. |
| Twilight of the Northlands | Hope, Companionship, Knacks, subtle magic, travel Fatigue/roles, Song, Assemblies, downtime, ground | Exact role, Song, and Assembly analyses | Travel, Song, Assembly, and Knack procedures repaired. Companionship remains finite and is not a runaway resource. |
| Candlelight Delvekit | Turns, reveal, blockers, factions, traps, difficulty, survival ladder, generator pipeline | 9,000 baseline plus 9,000 post-repair seeded sites; rest-loop witness; invariant checks | Rest cadence and expedition scope are explicit; Soft tiny fill no longer forces traps or solo monsters; all checked generator invariants pass. |

## Evidence needed for deferred decisions

- Actual play logs should record whether the new concrete-stake trade rule constrains Ship Share accumulation without turning port calls into accounting. Compare a two-port cycle with one completed cargo/job stake against an empty-hold visit.
- The discard-overflow Pressure choice preserves lower retained Pressure when a high-tier action starts at 4. Compare the frequency and severity of crises from the same action mix begun at Pressure 0 versus 4; change the rule only if actual play shows that players reliably exploit the timing and crises do not supply the intended consequence.
- Paired Delvekit playtests, holding map and seed constant while changing difficulty, would determine whether the repaired frequency and prose-level GM knobs produce the intended experienced danger. Generator counts alone cannot establish lethality.

## Verification and residual risks

The exact results use closed-form d20 probabilities. Both the baseline and post-repair generator simulations used identical seed ranges across cells and checked room bounds, at-most-one trap room, faction count 0/2, and initial player-map discovery; no invariant failure occurred in either set of 9,000 generated sites. The simulation does not model Custodian judgment, player adaptation, encounter lethality, faction patrols, or campaign-level recovery. Therefore the findings support procedural repairs, not claims about real-play death rate or fun.

After those repairs, run a short adversarial playtest with: a two-PC Twilight journey, solo and five-PC Assemblies using one spokesperson, one Service Duct anomaly scene, a Free Trader two-port cycle plus ship fight, and one tiny Soft Delvekit seed containing a trap. Freeze interpretations before comparing outcomes.

**A further Sol Max audit is not justified for this bounded skin tranche.** The independent audit has already confirmed the one-spokesperson Assembly procedure and the deliberate discard-overflow Pressure decision. A later whole-engine Max audit would be justified only after the deferred economy/recovery questions are resolved and there is integrated play evidence to challenge.
