"""Point-buy ledger -- consistency, the tone dial, and exploitability."""
import itertools
from engine import (
    build_cost, cost_to_reach, p_success, expected_exchanges_to_drop,
    ATTR_BASELINE, STAM_BASELINE,
)

print("=" * 78)
print("1. ARE THE TWO PAYMENT ROUTES EQUIVALENT?")
print("=" * 78)
print("""
Route A (trade-offs): every +1 above baseline is paid by -2 total below
                      baseline across other scores.
Route B (build points): +1 above baseline costs 2; +1 below baseline costs 1.

If a step below baseline refunds exactly 1 and a step above costs exactly 2,
then -2 below == +1 above and the two routes are the same ledger.
""")
for s in range(6, 17):
    print(f"  attribute {s:2d}: cost {cost_to_reach(s, ATTR_BASELINE):+3d}")
print()
for s in range(3, 10):
    print(f"  stamina   {s:2d}: cost {cost_to_reach(s, STAM_BASELINE):+3d}")
print()
print("Linear with slope +2 above baseline and +1 below, in both tracks.")
print("The routes are exactly equivalent. No arbitrage between them.")

print()
print("=" * 78)
print("2. DO THE BOOK'S PUBLISHED BUILDS OBEY THE LEDGER?")
print("=" * 78)
BUILDS = [
    ("Scholar (Almanac)",        [7, 10, 14, 10, 11], 4, 0),
    ("Iron Brute (Almanac)",     [15, 7, 6, 7, 10], 8, 0),
    ("Silver-tongue (Almanac)",  [8, 10, 11, 13, 10], 5, 0),
    ("Grak (Clanfire)",          [12, 10, 10, 8, 8], 7, 1),
    ("Tarra (Clanfire)",         [6, 8, 12, 14, 11], 3, 0),
]
allgood = True
for name, attrs, stm, tags in BUILDS:
    c = build_cost(attrs, stm) + 2 * tags
    if c != 6:
        allgood = False
    print(f"  {name:<26} {attrs} STM {stm}: cost {c:>2}  "
          + ("OK" if c == 6 else f"<-- costs {c}, not 6"))
print()
print("All published sample builds price at exactly the standard 6 points."
      if allgood else "MISMATCH FOUND -- see above.")

print()
print("=" * 78)
print("3. THE MIN-MAX FRONTIER (standard 6 build points)")
print("=" * 78)
BUDGET = 6
ATTR_RANGE = range(6, 17)
STM_RANGE = range(3, 10)

legal = []
for attrs in itertools.product(ATTR_RANGE, repeat=5):
    base = sum(cost_to_reach(a, ATTR_BASELINE) for a in attrs)
    if base > BUDGET + 2:
        continue
    for stm in STM_RANGE:
        if base + cost_to_reach(stm, STAM_BASELINE) == BUDGET:
            legal.append((attrs, stm))
print(f"Legal builds at exactly {BUDGET} points: {len(legal):,}")


def score(attrs, focus_weight):
    """Effective success rate if the player steers `focus_weight` of rolls to
    their best attribute and the rest uniformly across the others."""
    others = sorted(attrs)[:-1]
    p_other = sum(p_success(a) for a in others) / len(others)
    return focus_weight * p_success(max(attrs)) + (1 - focus_weight) * p_other


for w in (0.2, 0.4, 0.6, 0.8):
    top = max(legal, key=lambda b: score(b[0], w))
    spread = min(legal, key=lambda b: max(b[0]) - min(b[0]))
    print()
    print(f"  If {int(w * 100)}% of rolls can be steered to the best attribute:")
    print(f"    optimal build : {sorted(top[0], reverse=True)} STM {top[1]}"
          f"  -> {float(score(top[0], w)) * 100:.2f}% effective")
    print(f"    flattest build: {sorted(spread[0], reverse=True)} STM {spread[1]}"
          f"  -> {float(score(spread[0], w)) * 100:.2f}% effective")
    print(f"    gap: {float(score(top[0], w) - score(spread[0], w)) * 100:+.2f}pp")

print()
print("=" * 78)
print("4. WHAT THE MIN-MAXER PAYS FOR IT")
print("=" * 78)
print("A 16 costs 12 points, so a 6-point budget must strip 6 more from Luck,")
print("Stamina and the dump stats -- exactly what keeps you alive and in play.")
print()
CANDIDATES = [
    ("max spike, dump Luck+STM", [16, 10, 10, 8, 8], 3),
    ("max spike, dump attrs",    [16, 6, 6, 10, 11], 5),
    ("strong spike",             [14, 10, 10, 10, 8], 5),
    ("standard signature",       [12, 11, 10, 10, 10], 5),
    ("flat",                     [11, 11, 11, 10, 10], 5),
]
print(f"{'build':<26} {'cost':>5} {'best':>5} {'Luck':>5} {'STM':>4} | "
      f"{'P(best)':>8} {'P(Luck test)':>13} {'exchanges to drop':>18}")
print("-" * 96)
for name, attrs, stm in CANDIDATES:
    dfn = sorted(attrs, reverse=True)[1]
    ttk = expected_exchanges_to_drop(stm, 10, dfn, 1, 1)
    print(f"{name:<26} {build_cost(attrs, stm):>5} {max(attrs):>5} "
          f"{attrs[-1]:>5} {stm:>4} | "
          f"{float(p_success(max(attrs))) * 100:7.2f}% "
          f"{float(p_success(attrs[-1])) * 100:12.2f}% {float(ttk):18.2f}")

print()
print("=" * 78)
print("5. THE TONE DIAL GATES BREADTH, NOT PEAK COMPETENCE")
print("=" * 78)
print("Best single attribute reachable at each budget, paying only with points:")
for budget in (0, 6, 12, 16):
    reach = min(ATTR_BASELINE + budget // 2, 16)
    leftover = budget - 2 * (reach - ATTR_BASELINE)
    print(f"  {budget:>2} points: one attribute at {reach:2d} "
          f"({float(p_success(reach)) * 100:.0f}% success), {leftover} left over")
print()
print("With trade-offs allowed, the 16 ceiling is reachable from 0 points:")
minimal = []
for attrs in itertools.product(ATTR_RANGE, repeat=5):
    if max(attrs) != 16:
        continue
    base = sum(cost_to_reach(a, ATTR_BASELINE) for a in attrs)
    for stm in STM_RANGE:
        if base + cost_to_reach(stm, STAM_BASELINE) == 0:
            minimal.append((sorted(attrs, reverse=True), stm))
print(f"  Legal 16-spike builds at 0 build points: {len(minimal)}")
for b in minimal[:4]:
    print(f"    {b[0]} STM {b[1]}")
print()
print("And the ceiling binds at the top: 12 points already reaches 16, so")
print("'heroic 16' differs from 'pulp 12' only by 4 spare points elsewhere.")

print()
print("=" * 78)
print("6. WHY LUCK IS THE OPTIMAL DUMP STAT")
print("=" * 78)
print("""
Luck's only mechanical roles are the token pool and the roll-under target for
a Luck test. The Almanac advises calling those "sparingly -- one or two per
dozen beats", so the punishment for dumping Luck arrives at a frequency the
Custodian controls. Assume 60% of beats involve a roll steerable to the
signature attribute.
""")
BEATS = 12
for tests in (1, 2, 3, 4):
    for drop in (2, 4):
        cost = tests * (5 * drop) / 100
        gain = 0.6 * BEATS * (5 * (drop // 2)) / 100
        verdict = "FAVOURS DUMPING LUCK" if gain > cost else "luck holds its value"
        print(f"  Luck -{drop} funds +{drop // 2} signature, at {tests} Luck "
              f"test(s)/{BEATS} beats: cost {cost:.2f}, benefit {gain:.2f}, "
              f"net {gain - cost:+.2f}  -> {verdict}")
print()
print("Break-even sits at about four Luck tests per dozen beats -- twice the")
print("rate the book recommends. The token pool is what should hold Luck's")
print("value, and it degrades only linearly.")
