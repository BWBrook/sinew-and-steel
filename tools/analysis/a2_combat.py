"""Combat model -- damage by attribute and soak, the no-hard-zero check, time-to-kill by tier."""
from fractions import Fraction
from engine import (
    damage_dist, expected_damage, expected_exchanges_to_drop, p_attacker_wins,
)

SCORES = [6, 8, 10, 12, 14, 16]
SOAKS = [0, 1, 2, 3]


def pct(f) -> float:
    return round(float(f) * 100, 2)


def fmt(f, nd=3) -> str:
    return f"{float(f):.{nd}f}"


print("=" * 78)
print("EXPECTED DAMAGE PER EXCHANGE   (edge +1, defender attribute 10)")
print("=" * 78)
print(f"{'Att':>4} | {'P(win)':>7} |" + "".join(f"{'soak ' + str(s):>10}" for s in SOAKS)
      + f"{'plate/none':>12}")
print("-" * 70)
for a in SCORES:
    row = [expected_damage(a, 10, 1, s) for s in SOAKS]
    print(f"{a:>4} | {pct(p_attacker_wins(a, 10)):6.2f}% |"
          + "".join(f"{fmt(x):>10}" for x in row) + f"{float(row[3] / row[0]):>12.2f}")
print()
print("Expected damage rises smoothly with attribute at every soak. Plate takes")
print("roughly half the damage of an unarmoured target across the whole range.")

print()
print("=" * 78)
print("NO HARD ZERO   P(exchange deals 0 damage) == P(miss), edge +1, defender 10")
print("=" * 78)
print(f"{'Att':>4} |" + "".join(f"{'soak ' + str(s):>12}" for s in SOAKS)
      + f"{'  P(miss)':>12}")
print("-" * 66)
for a in SCORES:
    dd0 = [damage_dist(a, 10, 1, s).get(0, Fraction(0)) for s in SOAKS]
    miss = 1 - p_attacker_wins(a, 10)
    assert all(z == miss for z in dd0), "a winning hit dealt 0 damage"
    print(f"{a:>4} |" + "".join(f"{pct(z):11.2f}%" for z in dd0)
          + f"{pct(miss):11.2f}%")
print()
print("Every winning hit deals at least 1: the only zero-damage exchange is a miss.")

print()
print("=" * 78)
print("EFFECT OF ADVANTAGE IN COMBAT (edge +1, defender 10, soak 2)")
print("=" * 78)
print("Advantage multiplies expected damage by more than it multiplies hit rate,")
print("because keeping the lower die nearly doubles the natural-1 rate (soak")
print("bypass + bonus damage) and deepens margin, which now adds damage directly.")
print()
for a in SCORES:
    sd = expected_damage(a, 10, 1, 2)
    ad = expected_damage(a, 10, 1, 2, att_mode="advantage")
    hw = p_attacker_wins(a, 10, att_mode="advantage") / p_attacker_wins(a, 10)
    print(f"  att {a:2d}: damage x{float(ad / sd):.3f}   hit rate x{float(hw):.3f}")

print()
print("=" * 78)
print("TIME TO KILL BY NPC TIER")
print("Almanac statlines; NPC defends at tier-2; PC attacks with edge +1.")
print("=" * 78)
TIERS = [
    ("Peasant", 8, 3, 0, 0),
    ("Soldier", 10, 4, 1, 1),
    ("Elite", 12, 5, 1, 1),
    ("Monster", 14, 6, 2, 1),
    ("Nemesis", 16, 7, 2, 3),
]
print(f"{'Tier':>9} {'score':>6} {'STM':>4} {'edge':>5} {'soak':>5} | "
      f"{'PC att 10':>10} {'PC att 12':>10} {'PC att 14':>10} {'PC att 16':>10}")
print("-" * 84)
for name, tier, stm, edge, soak in TIERS:
    cells = []
    for pc in (10, 12, 14, 16):
        e = expected_exchanges_to_drop(stm, pc, tier - 2, 1, soak)
        cells.append("never" if e is None else f"{float(e):.2f}")
    print(f"{name:>9} {tier:>6} {stm:>4} {edge:>+5} {soak:>5} | "
          + " ".join(f"{c:>10}" for c in cells))

print()
print("...and the same NPCs dropping a standard PC (STM 5, defends at 10):")
print(f"{'Tier':>9} | {'vs unarmoured PC':>18} | {'vs PC in mail (soak 2)':>24}")
print("-" * 58)
for name, tier, stm, edge, soak in TIERS:
    e_bare = expected_exchanges_to_drop(5, tier, 10, edge, 0)
    e_mail = expected_exchanges_to_drop(5, tier, 10, edge, 2)
    b = "never" if e_bare is None else f"{float(e_bare):.2f}"
    m = "never" if e_mail is None else f"{float(e_mail):.2f}"
    print(f"{name:>9} | {b:>18} | {m:>24}")

print()
print("Race condition: PC (att 12, edge +1, STM 5, soak 1) vs each tier.")
print("Ratio > 1 means the NPC drops the PC faster than the PC drops it.")
print("-" * 72)
for name, tier, stm, edge, soak in TIERS:
    pc_kills = expected_exchanges_to_drop(stm, 12, tier - 2, 1, soak)
    npc_kills = expected_exchanges_to_drop(5, tier, 10, edge, 1)
    if pc_kills is None or npc_kills is None:
        print(f"{name:>9} | unresolvable (a side can never deal damage)")
        continue
    print(f"{name:>9} | PC needs {float(pc_kills):6.2f}   "
          f"NPC needs {float(npc_kills):6.2f}   "
          f"ratio {float(pc_kills / npc_kills):5.2f}")
