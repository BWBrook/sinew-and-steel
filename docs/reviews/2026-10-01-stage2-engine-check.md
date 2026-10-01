# Stage 2: engine check after the author rulings

1 October 2026. Started from clean `d332a32`, after reading correspondence
thread 46 through message 791. This follows the
[Stage 1 critique](2026-10-01-stage1-review.md). `PLAN.md` remains the active
staged plan; the older handover is historical.

## Recommendation

**Retain the current numerical engine and creation ledger.** The latest rulings
settle the major timing ambiguities. This pass adds Barry's decision about
unused Pressure penalties and corrects two errors in the independent combat
analysis. The corrected results still distinguish offensive and defensive
Twilight objectives; they do not justify changing the stance bonuses.

Specialisation remains a question for play evidence. The legal score-16,
Stamina-9 specialist is strong in a favourable duel, but that result does not
price weaknesses across a campaign. A refund cap remains an optional design
alternative, not a repair established as necessary by the audit.

## Fable's updates, verified in the checkout

- Pressure effects accumulate. One-test penalties fire on the first reach or
  crossing of their step, and re-arm only after a crisis.
- Twilight positions are declared before each round and held through it.
- Side initiative is established once per fight; each side chooses its member
  order each round. The fair-initiative encounter calculations already used
  fixed side order. Fixed member order remains a legal model policy, although
  it does not exploit every tactical ordering choice.
- The Preface qualifies its ordinary-roll probability claim. The Almanac
  qualifies plate's benefit and gives the encounter profiles and assumptions
  for its revised 63% / 93% / 85% examples.
- The Stage 1 review is committed as `332bd97`. The rulings and corrections
  are in `f7c719a` and `d332a32`; layout remains deferred.

Fable reproduced the encounter and Pressure calculations, while explicitly
distinguishing agreement between models from playtest evidence. No previously
settled author choice is reversed here.

## New author ruling: unused Pressure penalties

Barry selected **“Discard the unused penalty”** when recovery lowers Pressure
below its triggering step. The Manual and Almanac now say:

> If the track falls below that step, discard any unused penalty from it.

The existing restriction on re-arming remains. Recovery can remove an unused
penalty without starting a new cycle. The tracked demonstration prompt has
been regenerated with the same two core-rule changes.

The resulting procedure can be checked without inventing new probabilities:

| Sequence | Result |
|---|---|
| Shared Strain rises from 1 to 3 after an action | Each crew member owes the step-2 penalty on their next qualifying EDU/SOC test. Step 3's toll applies to subsequent risky tests. |
| One crew member makes that test | That member consumes their penalty. Other crew members retain theirs. Advantage may cancel its effect but does not preserve it for another test. |
| Recovery lowers Strain to 1 before another member uses theirs | Discard that unused step-2 penalty. |
| Strain rises from 1 to 3 again before a crisis | The step-3 toll resumes. Step 2 does not fire again this cycle. |
| An action jumps from 1 to 5 | Resolve that action using its starting Pressure, then the crisis and reset. No unused penalty from the old climb survives the reset. |
| The crisis itself creates a future penalty | Keep it for its stated duration. It is a crisis consequence, not an old threshold penalty erased by resetting the track. |

The shared step-2 rows already name every recipient: each delver, crew member,
or companion. The tipper convention concerns individual crisis targets and
does not reduce those party-wide step effects to one character. Whispers keeps
its personal Insanity exception.

The worked example belongs in Stage 3. Stage 4 must distinguish pending effects
per character, thresholds already fired during the current cycle, and effects
created by a crisis. A clock value alone cannot represent that state.

## Corrections to the independent combat analysis

### Isolated exchange controls

Two Halvar rows accidentally applied his defensive stance modifier to the
Elite's defence. A Vanguard attacker should gain Advantage on his own attack;
the ordinary Elite does not inherit his defensive Disadvantage. Watchful had
the corresponding reverse error.

The corrected exact values, for Halvar attack 14 and edge 2 against an Elite
defence 12 and soak 1, are:

| Halvar's position | Hit probability | Damage per attack |
|---|---:|---:|
| Vanguard | 71.175% | 2.568875 |
| Steady | 50.500% | 1.682500 |
| Watchful | 29.825% | 0.796125 |

The whole-combat code already applied modifiers to their owners correctly;
this particular error was confined to two isolated-exchange rows.

### Vanguard after Injury

The earlier simulation continued to use Vanguard in later rounds after Injury,
although an Injured character cannot declare it. The model now stores the
declared stance separately from the preferred stance. Injury penalties apply
immediately, the current round's declaration holds, and the next declaration
uses Steady if Injury forbids the preferred Vanguard.

Steady is a stated simulation policy. The game also allows the player to choose
another legal position; this patch does not prescribe a player's choice or
claim to optimise adaptive tactics.

Four affected scenarios were rerun at 20,000 fights each, with the original
master seed `20260920` and scenario-derived random seeds:

| Vanguard case | Previous victory | Corrected victory | Observed change |
|---|---:|---:|---:|
| Halvar versus Elite, Hope 12 | 96.610% | 96.285% | -0.325 percentage points |
| Halvar versus Monster, Hope 0 | 70.170% | 69.920% | -0.250 percentage points |
| Halvar versus Monster, Hope 12 | 81.330% | 81.075% | -0.255 percentage points |
| Halvar and Tolly versus two Soldiers | 99.585% | 99.595% | +0.010 percentage points |

These are changes between seeded Monte Carlo estimates, not exact correction
effects. The full intervals remain in the
[combat report](../independent_engine/combat_analysis.md). Seventy-nine
unaffected result rows were retained unchanged; the two exact rows and four
simulation rows were replaced. The associated summary and figure are updated.

The practical conclusion survives. Against the defined Monster with no Hope,
Vanguard wins about 69.9%, Steady 59.3%, and Watchful 36.8%. Their probabilities
of standing through three rounds are about 78.8%, 81.0%, and 85.0%, respectively.
One position does not dominate both objectives in this comparison.

## What the older evidence can still support

- **Creation and core combat:** the natural-result, margin, damage, soak,
  Luck and ledger rules are unchanged. The old creation enumeration already
  prevents trade-off refunds buying tags. Core combat comparisons omit
  optional Injury and Pressure, so these corrections do not alter them.
- **Encounter profiles:** the independent specialist duel uses a Nemesis with
  soak 2; the Almanac's newer party example explicitly uses soak 3. Their
  percentages should not be interchanged merely because both say Nemesis.
- **Counterfactual builds:** an attribute floor of 8, no refund below 8, and
  an eight-point total refund cap are different rules. The simulated
  `[16,8,8,8,8]`, Stamina-6, Hope-8 profile is legal under all three, but does
  not compare their complete character economies. The report and figure
  labels now make that limitation clear.
- **Pressure:** the 0.94-crises example remains a valid prescribed tick
  process, not a model of cumulative penalties, payment choices or their
  feedback on failure. It cannot establish that a redline needs softening.
  In Twilight, Free Traders and Whispers, a character at step 4 can pay the
  persistent toll with Pressure and bring on a crisis rather than spending
  another token to stay there. Crisis consequences must remain real.

The older atlas's recommendation to retune Twilight from isolated damage
ratios should be read alongside the later coupled-combat evidence. Keep the
numbers while testing different objectives. Before changing the creation
ledger, use a credible mixed adventure that records applicable attributes,
defence methods, Luck spending, recovery and objectives; do not manufacture
weak-stat checks simply to punish a specialist.

## Verification and scope

- All **30 tests** pass, including three new regressions for stance ownership,
  immediate Injury penalties, and declaration timing across rounds.
- All **12 existing analytical controls** pass; the three saved Monte Carlo
  mirror-duel checks remain within their specified bounds against exact
  coupled recursion.
- Repository validation passes. The demonstration prompt regeneration was
  checked to change only the two approved Pressure sentences.
- The four affected simulations total **80,000 new fights**. This was not a
  rerun of all 1.48 million historical fights or the full skin/generator suite.
- The updated figure was inspected. No book rendering, Stage 3 prose sweep,
  private campaign mutation or Stage 4 harness overhaul was performed.

To reproduce the complete current combat dataset, use
`uv run python tools/analysis/independent_combat.py`; its default is 20,000
fights per scenario and seed 20260920. Then use
`uv run --extra analysis python tools/analysis/independent_figures.py` to
render the summary figure. Historical baseline files remain unchanged.
