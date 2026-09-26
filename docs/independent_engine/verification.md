# Verification and adjudication record

20 September 2026. Baseline `a77d476`; final working-tree repairs described in
[the review](README.md). No release or commit was made.

## Executed checks

- All **27 unit tests** pass, including 17 new dice/sheet/ownership regressions
  and one Soft tiny generator regression. The latter explicitly prevents variety
  fill from forcing either a trap or solo monster after the initial rolls decline them.
- `tools/validate_repo.py` passes.
- All ten manifest skins generate a character with seed `20260920` whose sheet
  passes `tools/validate_sheet.py`; their agent prompts assemble successfully.
  These checks use temporary files, not private campaign state.
- The tracked Clanfire demo prompt was regenerated from the revised source.
- Independent combat scenarios: 74 × 20,000 seeded fights. Exact coupled no-Luck
  recursion checks the stochastic implementation; intervals and Monte Carlo
  errors appear in [combat_analysis.md](combat_analysis.md).
- A separate implementation verified all 16 creation-count cells by convolution.
  Exact simple-check/opposed controls, exhaustive bounded split-nudge controls
  and binomial Pressure identities pass. The resource process is an exact state
  distribution under its declared policy, not a fitted campaign model.
- Delvekit: 9,000 baseline and 9,000 revised sites with matched seeds, zero
  checked structural-invariant failures. Tiny Soft trap incidence changes from
  48.6% to 24.2%, solo-monster incidence from 49.9% to 23.2%. This is not a
  mortality estimate. The other size/difficulty cells are unchanged.
- Both summary figures were visually inspected for readable labels and legends.

The final integration check caught an invocation error when resolving the venv
Python symlink bypassed the environment's PyYAML. Using the venv executable
without resolving that symlink passed all ten skin checks; no dependency or
source change was needed.

## Worked procedure checks

These are adversarial readings of the revised Markdown, not automated narrative
playtests. Generic trackers store values; the Custodian still resolves fictional
consequences and explicitly resets a crisis track.

| Situation | Required result |
|---|---|
| Test Luck with zero tokens and raw 1 | Natural success; it does not create a spendable token. In an opposed test, margins still determine the winner if both succeed. |
| Test current Luck 6 and spend two tokens nudging | The target stays 6 for that roll; the pool becomes 4. A success-only ability cost must also remain affordable. |
| Spend into adjusted 1 or 20 | Use the adjusted ordinary result; no new natural effect. Raw 1/20 remain locked and nudges cannot leave 1–20. |
| Split opposed nudge: scores 6 vs 16, raw 7 vs 2 | The attacker can win by spending six to lower its die to 1 and ten to raise the defender to 12. Cost 16, ordinary margins 5 vs 4. A search restricted to one die would miss this rescue. |
| Arcanum starts at Fatigue 4 | Determine the risky-test surcharge from starting Fatigue, charge it and the +2 tier cost once each, cast, then resolve one crisis and reset to zero. Failure also causes the stated backlash. Do not charge +2 again on success. |
| Reckoning starts at Dread 0 and fails | Pay +2 once, suffer Break, retain Dread 2. Failure alone does not add a Dread crisis. If the cost instead reaches 5, resolve that crisis as well and reset. |
| Wyrd starts at Doom 4 | Apply starting-Doom penalties, mark +3 once, resolve the action, then one crisis and reset without overflow. The tier's separate failure backlash still applies. |
| Trader sells a cargo lot, then visits another port | The sold stake is consumed; a paid job or claim is marked paid. There is no second payout from the same stake. Ship Shares repair Hull only with time, tools and access outside the exchange. |
| Solo traveller faces one declared journey hazard | Resolve its one applicable role test. Unrelated empty roles do not fail automatically; distinct active hazards still need handling, and one PC may cover multiple roles. |
| One HRT-12 spokesperson addresses an assembly | Ordinary success is 60% before nudges or fictional Advantage/Disadvantage. Extra party members supply preparation, not more rolls toward a headcount threshold. |
| Sing again or subdivide the same safe pause | One Song for the company per camp/night; each applicable recovery benefit once per uninterrupted pause. Good care replaces ordinary Stamina recovery rather than adding both. |
| Repeat a free Quick Scan on unchanged evidence | Keep the prior resolution. A further scan needs material new information, access, equipment or method and a stated time/risk consequence. |
| Rest briefly inside a dangerous delve | Spend a turn and advance an applicable declared danger clock. Fortune still requires a warm hearth; stepping through a doorway does not reset the expedition's survival count. |

## Independent audit verdict

The separate adversarial reviewer supports the targeted repairs. It independently
reproduced the relevant no-Luck duel contrast and reran the analyses, tests and
repository validator. It **does not support a claim of universal character
build dominance**, or a mandatory point-buy restriction on that evidence alone.

The strongest outstanding uncertainties are the share of tests using the
signature attribute, plausible defence methods, encounter objectives, recovery
cadence and valuation of weak domains. Combat Luck follows a transparent
heuristic, not an optimal policy. Adaptive stances, morale, retreat, Companionship
and arbitrary spell effects are not jointly modelled.

The next informative experiment is a paired fixed-adventure playtest of the
current ledger and an eight-point refund-cap alternative. Record signature-stat
share, defence modes, Luck use, rests, objectives and non-combat failures.
Model agreement is not empirical play evidence.
