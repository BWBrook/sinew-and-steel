# Engine analysis

Exact probability analysis of the Sinew & Steel resolution engine. Pure standard
library (`fractions`, `itertools`, `random`), so it runs without the project venv.

Everything is **exact enumeration**, not simulation: single checks enumerate all
20 die faces, opposed checks and combat exchanges enumerate the full 20x20 joint
space, and expected exchanges-to-drop solves the absorbing recursion

    E[s] = (1 + sum_d P(d) * E[s-d]) / (1 - P(0))

rather than sampling it. Probabilities are held as `Fraction` throughout, so the
published tables can be checked to the last decimal.

## Files

| File | What it does |
|---|---|
| `engine.py` | The rules, encoded once: die distributions, success, margin, opposed outcomes, damage with soak and margin steps, time-to-kill, Luck policies, the point-buy ledger. Everything else imports this. |
| `a1_tables.py` | Verifies Tables 9.1 and 9.2 in `rules/core/adventurers_manual.md`. Also margin scaling and natural-result rates under adv/dis. |
| `a2_combat.py` | Expected damage, zero-damage ("grind") rates, the advantage multiplier, and time-to-kill for every NPC tier in the Almanac. |
| `a3_penetration.py` | Armour under the unified damage rule: exhaustive check that no winning hit deals 0, the attribute needed for each margin step, and what each point of soak is worth against each tier. |
| `a4_luck.py` | Luck token economics: the nudge cost curve, the opportunity cost of a token, the armour-nudge clause, and the blind-vs-informed spending gap in opposed tests. |
| `a5_ledger.py` | Ledger consistency, the published sample builds, the min-max frontier over all 26,246 legal 6-point builds, the tone dial, and the Luck-dump analysis. |
| `a6_verify.py` | Independent Monte Carlo cross-check. The rules are re-implemented from the book text so a shared bug cannot hide. ~25 s. |

## Running

```bash
cd tools/analysis
for f in a1_tables a2_combat a3_penetration a4_luck a5_ledger; do
  echo "### $f"; python3 $f.py
done
python3 a6_verify.py          # slow, verification only
```

## Changing a rule and re-checking

Edit the encoded rule in `engine.py` -- each is a small named function
(`is_success`, `damage_for`, `margin_bonus`, `opposed_outcomes`,
`cost_to_reach`) -- then re-run. Changing `MARGIN_STEP` from 5 to 4, or
removing the minimum in `damage_for`, is a one-line change, and
`a2_combat.py` will immediately report what it does to every tier.

## Headline results after the 7 September 2026 ruleset revision

The damage rule is now `1 + edge + 1 per full 5 margin - soak, minimum 1`
(natural 1 ignores soak and adds +1). It replaced per-4 soak erosion plus a
separate +1 at margin 10.

* Tables 9.1 and 9.2 are correct; all five published sample builds price at
  exactly 6 build points; the trade-off and build-point ledgers are equivalent.
* No hard zero: a winning hit always deals damage. A Peasant-tier mob with
  improvised weapons now hurts a character in mail on 27% of exchanges (was
  4.25%), and mail still trims its expected damage by about a fifth.
* The tier ladder is unchanged in shape: an Elite is still an even fight for a
  standard PC (ratio 0.89 for an attribute-12 PC). A Nemesis in plate takes 20
  exchanges to drop at attribute 10 (was 52), 15 at attribute 12.
* Expected damage rises smoothly with attribute at every soak; the old jump at
  attribute 11 (first reach of the margin-10 bonus) is gone.
* Luck timing in opposed tests is now defined in the rules: both dice are read
  before anyone spends. That is the informed reading, worth 50pp per token.
* Advancement now has a stated ceiling (attributes 16, Stamina 9) for life.
* Still open, by design: attacking never reaches parity in a symmetric matchup
  (24.75% at score 6, 46.00% at score 16) because both-fail and ties go to the
  defender; and the tone dial gates breadth, not peak competence.
* `a5_ledger.py` section 6 counts only Luck tests as the cost of dumping Luck.
  It ignores the smaller nudge pool, so it overstates the case for dumping.
