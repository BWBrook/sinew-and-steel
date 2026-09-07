"""Armour under the unified damage rule: the floor, the margin steps, and what
soak is worth against each attacker."""
from fractions import Fraction
from engine import damage_dist, damage_for, expected_damage, MARGIN_STEP, DIE

print("=" * 78)
print("THE FLOOR")
print("=" * 78)
print(f"""
damage = 1 + edge + floor(margin / {MARGIN_STEP}) - soak, minimum 1.

Because of the minimum, a winning hit always deals damage. The old closed form
attribute >= 4*(soak - edge) + 2, below which only a natural 1 could hurt an
armoured target, no longer exists. Exhaustive check that no winning roll deals 0:
""")
bad = [(r, m, e, s) for r in range(1, DIE) for m in range(0, DIE)
       for e in range(0, 3) for s in range(0, 5) if damage_for(r, m, e, s) < 1]
print("  " + ("NO zero-damage hits across all roll/margin/edge/soak combinations."
              if not bad else f"FAIL: {bad[:5]}"))

print()
print("=" * 78)
print("MARGIN STEPS: the smallest attribute that can reach each bonus")
print("=" * 78)
print("The best ordinary (non-natural-1) margin is attribute - 2, so:")
for bonus in range(1, 4):
    need = MARGIN_STEP * bonus + 2
    print(f"  +{bonus} damage needs margin {MARGIN_STEP * bonus:>2}  ->  attribute >= {need}")
print()
print("The first step is reachable from attribute 7, so there is no attribute at")
print("which a component of damage flips from impossible to possible for most PCs;")
print("each step is worth the same +1, on top of a floor that is always there.")

print()
print("=" * 78)
print("WHAT SOAK IS WORTH   E[damage] as a share of the unarmoured value")
print("=" * 78)
print(f"{'attacker':>28} |  soak 1  soak 2  soak 3")
print("-" * 58)
CASES = [
    ("Peasant fist (8, +0)", 8, 0), ("Soldier blade (10, +1)", 10, 1),
    ("Elite blade (12, +1)", 12, 1), ("Monster maul (14, +2)", 14, 2),
    ("Nemesis maul (16, +2)", 16, 2),
]
for label, attr, edge in CASES:
    base = expected_damage(attr, 10, edge, 0)
    row = [expected_damage(attr, 10, edge, s) / base for s in (1, 2, 3)]
    print(f"{label:>28} |" + "".join(f"{float(x):8.2f}" for x in row))
print()
print("Against weak blows, mail and plate converge on the floor; plate earns its")
print("weight against strong attackers, where it removes whole points of damage.")

print()
print("=" * 78)
print("THE OLD HARD ZERO, REVISITED")
print("=" * 78)
dd = damage_dist(8, 10, 0, 2)
print("Peasant tier (8), improvised weapon (edge +0), vs a PC in mail (soak 2):")
print("  damage distribution: "
      + ", ".join(f"{d} dmg {float(p) * 100:.2f}%" for d, p in sorted(dd.items())))
dd0 = damage_dist(8, 10, 0, 0)
print("Same peasant against an unarmoured PC (soak 0):")
print("  damage distribution: "
      + ", ".join(f"{d} dmg {float(p) * 100:.2f}%" for d, p in sorted(dd0.items())))
print(f"  E[dmg] mail {float(expected_damage(8, 10, 0, 2)):.3f} vs bare "
      f"{float(expected_damage(8, 10, 0, 0)):.3f}: the mob can now wear you down.")
