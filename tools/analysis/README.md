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
| `engine.py` | The rules, encoded once: die distributions, success, margin, opposed outcomes, dynamic soak, damage, time-to-kill, Luck policies, the point-buy ledger. Everything else imports this. |
| `a1_tables.py` | Verifies Tables 9.1 and 9.2 in `rules/core/adventurers_manual.md`. Also margin scaling and natural-result rates under adv/dis. |
| `a2_combat.py` | Expected damage, zero-damage ("grind") rates, the advantage multiplier, and time-to-kill for every NPC tier in the Almanac. |
| `a3_penetration.py` | The penetration threshold `attribute >= 4*(soak - edge) + 2`, exhaustively verified across all 432 attribute/edge/soak combinations. |
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
(`is_success`, `effective_soak`, `damage_for`, `opposed_outcomes`,
`cost_to_reach`) -- then re-run. A house rule such as "a successful attack
always deals at least 1 damage" is a one-line change in `damage_for`, and
`a2_combat.py` will immediately report what it does to every tier.

## Headline results as of v0.3.1

* Tables 9.1 and 9.2 are correct; all five published sample builds price at
  exactly 6 build points; the trade-off and build-point ledgers are equivalent.
* Ordinary damage requires `attribute >= 4*(soak - edge) + 2`. Below that only a
  natural 1 gets through, so a Peasant-tier mob with improvised weapons cannot
  hurt a character in mail except on a natural 1 (4.25% of exchanges).
* The tier ladder is well centred -- an Elite is a dead-even fight for a
  standard PC (ratio 1.00) -- but a Nemesis in plate takes 52 exchanges to drop
  at attribute 10.
* Attacking never reaches parity in a symmetric matchup: 24.75% at score 6,
  46.00% at score 16, because both-fail and ties go to the defender.
* Luck spending timing in opposed tests is undefined, and the informed reading
  is 2.5x more token-efficient than the blind one.
* The tone dial gates breadth, not peak competence: 850 legal 16-spike builds
  exist at 0 build points.
