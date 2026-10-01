# Stage 1: review of the revised Sinew & Steel book

1 October 2026. Reviewed `a545230` against `715ce90`. The checkout was clean at
the start. This report records critique, not adopted changes. No manuscript,
engine, tooling or layout files were edited, and no new balance settings were
implemented.

## Overall judgement

Keep this revision's voice and structure. The text is substantially easier to
learn from: the action sequence names the player's declaration, the Custodian's
ruling, the roll and its consequence; opposed roles are explained; Luck's current
target is explicit; and spell tables distinguish upfront from outcome costs.
The genre passages retain distinct voices without turning into ten unrelated
games. Another general prose rewrite would have little value.

The main remaining weaknesses concern **when a rule applies and how long it
lasts**. Two inherited ambiguities materially change play: Pressure-effect
persistence and Twilight stance commitment. A few new explanatory claims also
need qualifications. None of these findings justifies discarding the prose pass
or silently reversing an author ruling.

## Agreed sequence and review boundary

Barry's four-stage plan is recorded, as a labelled paraphrase, in correspondence
thread 46, message 787, replying to Fable's handoff 786:

1. **Now:** cross-examine the completed revision and report the critique.
2. Decide and implement engine changes with Barry, using the analysis and audit.
3. Align the rules and chapters with those changes while preserving this voice.
4. Re-examine and overhaul the AI Custodian tooling and supporting machinery.

Only Stage 1 is active. The handoff's older suggestion to proceed next to layout
is superseded. The two-page Quickstart constraint remains; I did not render or
verify the reported page count in this review.

I treated the handoff's author rulings as the intended baseline: shared party
Pressure except personal Insanity in Whispers; personal optional conditions;
trade-offs fund raises, not tags; the fixed creation ledger; the retained
red-line Disadvantage; no nudging top-tier magic; and Rust's paid power-unlocking
tag. These are deliberate decisions, not editorial regressions.

## Findings that should shape the next decisions

### 1. Define Pressure-effect persistence before measuring its severity

**Inherited ambiguity; important for Stage 2.** Examples are Candlelight
[93–95](../../skins/candlelight_dungeons.md), Twilight
[142–144](../../skins/twilight_of_the_northlands.md), Free Traders
[134–136](../../skins/free_traders_of_the_drift_marches.md), and Whispers
[96–98](../../skins/whispers_in_the_fog.md). The core states when to sample the
track and resolve a crisis, but never says whether lower-step effects persist.

At Fatigue 4, do incoming attacks retain the Advantage supplied at 3? At Dread 4,
does the step-3 Hope-or-Dread surcharge still apply? Once a delver has used the
step-2 penalty on their next STR/DEX test, does remaining at 2 generate another?
Does a jump from 1 to 3 trigger the skipped step's effect?

These readings produce different resource drains and different time spent at
red line. Specify whether rows replace or accumulate, and how a pending
one-test penalty is created, consumed and cleared. That convention requires a
decision; this review does not select it or recommend softening step 4.

### 2. Give Twilight stances an explicit commitment window

**Inherited ambiguity; important for Stage 2.** Twilight's
[stance procedure](../../skins/twilight_of_the_northlands.md) at lines 203–214
says both “choose each exchange” and “each combat exchange, or round”. The
[Manual](../../rules/core/adventurers_manual.md), line 224, defines a round
containing individual attacks.

If an exchange means each opposed attack, a player can take Vanguard on their
own attack and Watchful on the enemy's: both advantages, neither drawback.
Committing through a whole round preserves the stated trade-off. State the
selection point and expiry explicitly. This is separate from changing the stance
numbers. Our previous experiments held a stance fixed during each fight; they
do not validate the per-attack switching interpretation.

### 3. Complete Emberfall's teaching of a combat round

**Retained teaching gap, made more visible by improved initiative wording.**
[Emberfall](../../rules/scenarios/clanfire_emberfall.md), lines 125 and 143–155,
places both hunters before the wolf. Losing Tarra's intimidation contest can
then let it bite or drag someone, with another consequence, while its normal
turn remains pending.

The advertised Quickstart → Clanfire → Emberfall route never explicitly gives
the two essentials taught in Manual 224: each able combatant acts once per
round; defending uses no action. A newcomer can infer that winning defence
grants an automatic damaging attack, followed by the wolf's own attack.

Put those essentials in the scenario's teaching paragraph, and label the
intimidation failure consequence: does it use the wolf's action, change its
position, or initiate a normal opposed attack? Dragging on a tied or failed
contest also needs distinguishing from the wolf's margin-4 hook at line 115.
This is an ambiguity in the example, not proof that negotiated failure
consequences are forbidden. Preserve the motivated wolf and non-lethal victory.

## Definite corrections to numerical explanations

### 4. Encounter percentages are examples with unstated assumptions

**Introduced.** [Almanac 254](../../rules/core/custodians_almanac.md) supplies
specific party-size win rates while stating only no Luck and no retreat. The
numbers are reproducible, but also assume PCs always act first, all standing
PCs attack the single opponent, and the opponent targets the most wounded PC.

The profiles are attack/defence 12, edge 1, soak 1, Stamina 5 for every PC;
14/14, edge 2, soak 1, Stamina 6 for the Monster; and 16/16, edge 2, **soak 3**,
Stamina 7 for the Nemesis. A tier alone does not prescribe that equipment.

| Encounter | PCs first: printed example | Fair side initiative |
|---|---:|---:|
| Two PCs versus Monster | 68.82% | 62.75% |
| Three PCs versus Monster | 95.68% | 93.49% |
| Four PCs versus Nemesis | 88.32% | 84.69% |

These are exact results under those assumptions, not proposed replacement
encounter ratings. The printed Nemesis example has mean casualties of 1.26 PCs;
“lose one or two” is not a guarantee. State the assumptions briefly, or use
qualitative guidance and point to the worked calculation. Preserve the useful
lesson that numbers and position matter.

### 5. Plate's categorical explanation overlooks legal nudges

**Introduced.** [Almanac 251](../../rules/core/custodians_almanac.md) says plate
never improves on mail against light weapons, and gives a score-12 threshold
for standard weapons. Counterexamples follow directly from the retained rules:

- Score 16, edge 0, raw 2 nudged to an ordinary 1: margin 15, damage 4 before
  soak; mail takes 2, plate 1.
- Score 11, edge 1, the same nudge: margin 10 and the same damage distinction.
- Even without nudging, “any” edge-2 attacker is too broad: score 6 cannot reach
  margin 5 on an ordinary result, so mail and plate still coincide.

The clean explanation is that plate improves on mail when an **ordinary hit
would deal at least 4 damage before soak**. Natural 1s ignore both. No new armour
property or numerical tuning is needed.

### 6. Qualify the Preface's five-percentage-point promise

**Introduced.** [Preface 18](../../rules/book/preface.md) says a one-point stat
increase raises success by one in twenty. That is true for an ordinary single-die
test in the normal attribute range, not a universal rule. With Advantage,
15→16 changes success from 93.75% to 96%, a 2.25-point increase; opposed tests
also differ. Add the ordinary-test qualification. The personal opening and
conviction should stay.

## Smaller, bounded clarifications

These do not call for another general rewrite. They are recorded for the later
aligned text pass; author intent still controls where two readings are possible.

| Location at a545230 | Reader problem and minimal direction |
|---|---|
| Quickstart 87 | Define “perilous beats” as dangerous scenes, as Manual 304 already does. The short reading path can otherwise suggest counting checks, accelerating both milestones and full Luck refills. Substitute within the two-page constraint. |
| The Custodian 28, 40–47 | Stakes precede the roll, but “When a roll fails” then offers a new consequence choice or d6. Say whether the choice occurs before rolling or merely elaborates the declared stakes afterwards. Retained ambiguity. |
| Free Traders 214, 222 | Larger ships may have larger Hull clocks, yet all drives disable at 6. Use the clock's filled threshold if intended, or explain why drive failure and clock size differ. Retained inconsistency. |
| Twilight 122, 174–176 | Does a failed Scout test give its hazard instead of, or as well as, generic travel Fatigue? State the role table's precedence; don't add a second test. Retained ambiguity. |
| Twilight 79, 136 | “Costs are personal” now sits beside shared Dread. Specify personal Hope versus company Dread; neither is paid from Companionship. Unchanged wording made stale by the explicit party-track ruling. |
| Twilight 235, 243 | Healing Rest clears Injury in the explanatory paragraph but omits it in the lookup table. Add it to the row for users of the optional Injury module. |
| Emberfall 163; Custodian Notes 101 | Make the prescribed closing question conditional on it remaining unanswered. If players have earned the deeper truth, close on the next question their actions created. Retained editorial tension with agency. |
| The Adventurer 19, 54 | Distinguish thinking/clarifying from fictional stalling, as The Custodian 65 does; “plainly plausible” also does not by itself remove uncertainty. Small qualifications preserve the brisk tone. |
| Almanac 190, 303 | “Stops power creep” overstates what the ledger proves. Likewise 10 + stat is a rough 2d6 character translation, not a general probability conversion without an outcome threshold. These are inherited claims, not new engine defects. |

## Answers to Fable's four requested checks

**Party size and Pressure.** Party size alone does not determine pacing; the
number of chargeable events does. A shared environmental threat and four
separate ability costs need not have the same granularity. As an illustration,
start at 0 and allow an independent one-point tick with probability 1/3, no
purges or extra costs, over 20 beats:

| PCs | One tick opportunity per PC per beat: expected crises | One opportunity for the whole party per beat |
|---|---:|---:|
| 1 | 0.94 | 0.94 |
| 2 | 2.27 | 0.94 |
| 4 | 4.93 | 0.94 |

The first column is E[floor(Binomial(20N, 1/3)/5)]. These are illustrative exact
calculations, **not forecasts of actual play**. They show why the earlier
one-crisis calibration cannot automatically be copied to every party size or
roll frequency. Stage 2 should log the sources and number of Pressure events,
not normalise every cost by party size by default.

**Red-line duration.** In Rust, Heat 4 explicitly adds a point on the next risky
test, even on success (line 113), so that test triggers the crisis unless the
track is reduced first. In Twilight and Free Traders, duration depends on
whether the step-3 toll persists and whether players pay tokens or Pressure.
At a hypothetical independent 1/3 tick chance it lasts three eligible events on
average; without a trigger it can persist. There is no single justified duration
for the revised game yet. Keep the requested Disadvantage severity.

**The tipper rule.** It handles ordinary sequential actions well. Group or
ambient gains need a named affected character before resolution, or a declared
order when several actions are resolved together. Briar's group fear check
(line 143: one Sin if anyone fails) illustrates an event with no unique tipper.
The existing “unless the fiction points elsewhere” permits a ruling; a short
example would make that responsibility visible. No extra track is required.

**Magic costs.** The four systems' costs and nudge permissions survive the
cross-read coherently, including Candlelight's nudgeable Greater Spells versus
Whispers' un-nudgeable Incantations. Iron's backlash is applied before its final
crisis check. I found no demonstrated reason to charge upfront costs twice,
carry overflow, or add a second crisis. Pressure created during a crisis itself
is a useful example to clarify, but the literal resolve-then-reset sequence is
coherent; it is not evidence for a new recursive subsystem.

## Coverage, checks and limits

The review covered all 22 numbered chapters, the back-cover blurb, all ten
skins and the linked Delvekit overlay. Separate readers reviewed the narrative
chapters/starter, core rules, and skins; I integrated and checked the main
counterexamples against current text and the prior commit.

The exact core check confirmed all 36 opposed-probability cells within rounding,
simple-test probabilities, Grak's accounting and the three Almanac sample builds
(each exactly 6 points). The encounter check independently enumerated the 400
die pairs and solved coupled hit-point states, dividing out unchanged-state
loops. Fair initiative averages the two fixed side orders. No old atlas code
was imported for that check.

Clanfire's Vision Glass/Beast Bond, Iron's casting permissions, Time Odyssey's
single intervention test, Briar's clues, Rust's unlocking tag, Service Duct
Blues' scan limits, and Whispers' personal Insanity all express the intended
rulings coherently. No new contradiction was established in the unchanged
Delvekit. Absence of a finding is not proof against every possible exploit.

This was a Markdown review, not a human playtest, optimal-policy search,
rendered-book inspection or Stage 4 machinery audit. No full simulation suite
or harness tests were rerun. Previous engine evidence retains its stated
assumptions; it is not automatically validation of every new author ruling.

The next useful decision is to settle Pressure-effect persistence and stance
commitment before comparing engine variants. The revised narrative style can
carry those decisions with small, local changes in Stage 3.
