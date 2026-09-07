"""The penetration threshold: a closed-form result behind every soak cliff."""
from fractions import Fraction
from engine import damage_dist, die_dist, is_success, effective_soak, DIE

print("=" * 78)
print("PENETRATION THRESHOLD")
print("=" * 78)
print("""
A hit deals damage only if  1 + edge - max(0, soak - floor(margin/4)) > 0,
i.e. only if  floor(margin/4) >= soak - edge,  i.e.  margin >= 4*(soak - edge).

The best margin available to an ordinary (non-natural-1) success is
attribute - 2, because roll 1 is the natural-1 case that bypasses soak
outright. So an attacker can deal ordinary damage through a given soak
only if:

    attribute >= 4 * (soak - edge) + 2

Below that threshold the ONLY way through is a natural 1: 5% of rolls,
9.75% with advantage.
""")


def threshold(soak: int, edge: int) -> int:
    return max(4 * (soak - edge) + 2, 1)


print(f"{'soak':>5} {'edge':>5} | {'min attribute for ordinary damage':>34}")
print("-" * 46)
for soak in range(0, 5):
    for edge in range(0, 3):
        need = threshold(soak, edge)
        note = "any" if need <= 1 else str(need)
        if need > 16:
            note += "  (unreachable at creation caps)"
        print(f"{soak:>5} {edge:>+5} | {note:>34}")

print()
print("EXHAUSTIVE VERIFICATION of the closed form")
bad = []
for attr in range(3, 21):
    for edge in range(0, 4):
        for soak in range(0, 6):
            can = False
            for roll in range(2, DIE):  # exclude nat 1 and nat 20
                if roll <= attr:
                    m = attr - roll
                    if 1 + edge - effective_soak(soak, roll, m) > 0:
                        can = True
                        break
            predicted = attr >= threshold(soak, edge)
            if can != predicted:
                bad.append((attr, edge, soak, can, predicted))
if bad:
    print(f"  FORMULA FAILS on {len(bad)} case(s):")
    for b in bad[:20]:
        print("   ", b)
else:
    print("  Formula holds for all 18 x 4 x 6 = 432 combinations. No exceptions.")

print()
print("Boundary cases, by enumeration (defender attribute 10):")
CASES = [
    ("peasant fist vs mail", 8, 0, 2),
    ("score 9 fist vs mail", 9, 0, 2),
    ("score 10 fist vs mail", 10, 0, 2),
    ("score 9 blade vs plate", 9, 1, 3),
    ("soldier blade vs plate", 10, 1, 3),
    ("elite blade vs plate", 12, 1, 3),
    ("great-axe vs plate", 10, 2, 3),
]
for label, attr, edge, soak in CASES:
    dd = damage_dist(attr, 10, edge, soak)
    p_nonzero = sum(p for d, p in dd.items() if d > 0)
    d_dist = die_dist("straight")
    p_nat1 = Fraction(0)
    for d, pd in d_dist.items():
        if (not is_success(d, 10)) or ((attr - 1) > (10 - d)):
            p_nat1 += Fraction(1, DIE) * pd
    print(f"  {label:<24} attr {attr:2d} edge {edge:+d} soak {soak}: "
          f"P(dmg>0) {float(p_nonzero) * 100:5.2f}%  "
          f"(nat-1 path {float(p_nat1) * 100:4.2f}%)  "
          f"threshold {threshold(soak, edge)}")

print()
print("=" * 78)
print("THE HARD ZERO")
print("=" * 78)
dd = damage_dist(8, 10, 0, 2)
print("Peasant tier (8), improvised weapon (edge +0), vs a PC in mail (soak 2):")
print("  damage distribution: "
      + ", ".join(f"{d} dmg {float(p) * 100:.2f}%" for d, p in sorted(dd.items())))
print("  A whole mob of them threatens the PC only via natural 1s.")
print()
dd0 = damage_dist(8, 10, 0, 0)
print("Same peasant against an unarmoured PC (soak 0):")
print("  damage distribution: "
      + ", ".join(f"{d} dmg {float(p) * 100:.2f}%" for d, p in sorted(dd0.items())))
print()
r = (sum(p for d, p in dd0.items() if d > 0) / sum(p for d, p in dd.items() if d > 0))
print(f"Mail is a {float(r):.1f}x reduction in threat, from two points of soak.")
