"""Task 1 & 6: verify the book's published tables; adv/dis natural rates."""
from fractions import Fraction
from engine import (
    DIE, MODES, die_dist, p_success, p_attacker_wins, opposed_outcomes,
    mean_margin_on_success, margin_dist_on_success,
)

SCORES = [6, 8, 10, 12, 14, 16]


def pct(f: Fraction) -> float:
    return round(float(f) * 100, 2)


print("=" * 74)
print("TABLE 9.1 CHECK  --  chance to succeed by score")
print("=" * 74)
BOOK_91 = {
    6:  (30, 51, 9),
    8:  (40, 64, 16),
    10: (50, 75, 25),
    12: (60, 84, 36),
    14: (70, 91, 49),
    16: (80, 96, 64),
}
print(f"{'Score':>5} | {'straight':>18} | {'advantage':>18} | {'disadvantage':>18}")
print(f"{'':>5} | {'exact  book':>18} | {'exact  book':>18} | {'exact  book':>18}")
print("-" * 74)
for s in SCORES:
    row = []
    for i, m in enumerate(MODES):
        e = pct(p_success(s, m))
        b = BOOK_91[s][i]
        flag = "" if abs(e - b) < 0.51 else "  <-- MISMATCH"
        row.append(f"{e:6.2f} {b:5d}{flag}")
    print(f"{s:>5} | " + " | ".join(f"{r:>18}" for r in row))

print()
print("Exact advantage/disadvantage formulae (keep lower / keep higher of 2d20):")
for s in SCORES:
    a, d = p_success(s, "advantage"), p_success(s, "disadvantage")
    print(f"  score {s:2d}:  adv = {a} = {pct(a):.2f}%   dis = {d} = {pct(d):.2f}%")

print()
print("=" * 74)
print("TABLE 9.2 CHECK  --  attacker wins an opposed check (%)")
print("=" * 74)
BOOK_92 = {
    6:  [25, 22, 19, 16, 13, 10],
    8:  [35, 31, 27, 23, 19, 15],
    10: [45, 41, 36, 31, 26, 21],
    12: [55, 51, 46, 40, 34, 28],
    14: [65, 61, 56, 50, 44, 37],
    16: [75, 71, 66, 60, 54, 46],
}
hdr = "  Att |" + "".join(f"{d:>14}" for d in SCORES)
print(hdr)
print("      |" + "".join(f"{'exact / book':>14}" for _ in SCORES))
print("-" * len(hdr))
mismatches = []
for a in SCORES:
    cells = []
    for j, d in enumerate(SCORES):
        e = pct(p_attacker_wins(a, d))
        b = BOOK_92[a][j]
        if abs(e - b) >= 0.51:
            mismatches.append((a, d, e, b))
            cells.append(f"{e:5.1f}/{b:<4d}*")
        else:
            cells.append(f"{e:5.1f}/{b:<4d} ")
    print(f"{a:>5} |" + "".join(f"{c:>14}" for c in cells))
print()
if mismatches:
    print(f"{len(mismatches)} cell(s) differ by >0.5pp (marked *):")
    for a, d, e, b in mismatches:
        print(f"  att {a:2d} vs def {d:2d}: exact {e:5.2f}%  book {b:3d}%  "
              f"(delta {e - b:+.2f}pp)")
else:
    print("All 36 cells match the book within 0.5pp.")

print()
print("Where do the attacker's losses come from? (att 12 vs def 12)")
o = opposed_outcomes(12, 12)
for k in ("att_only", "both_succeed_att", "both_succeed_dfn", "dfn_only",
          "both_fail", "attacker", "defender"):
    print(f"  {k:<20} {pct(o[k]):6.2f}%")

print()
print("Symmetric matchups (attacker == defender) -- attacker win share:")
for s in range(6, 17):
    o = opposed_outcomes(s, s)
    print(f"  {s:2d} vs {s:2d}: attacker {pct(o['attacker']):5.2f}%  "
          f"defender {pct(o['defender']):5.2f}%  "
          f"(both fail {pct(o['both_fail']):5.2f}%, "
          f"defender takes a tie {pct(o['both_succeed_dfn']):5.2f}%)")

print()
print("=" * 74)
print("MARGIN SCALES WITH ATTRIBUTE  (the soak-erosion driver)")
print("=" * 74)
print(f"{'Score':>5} | {'P(success)':>10} | {'E[margin|success]':>18} | "
      f"{'E[soak eroded|success]':>22} | {'P(margin>=10|succ)':>19}")
print("-" * 88)
for s in range(6, 17):
    mm = mean_margin_on_success(s)
    md = margin_dist_on_success(s)
    e_erode = sum((m // 4) * p for m, p in md.items())
    p_big = sum(p for m, p in md.items() if m >= 10)
    print(f"{s:>5} | {pct(p_success(s)):9.2f}% | {float(mm):18.3f} | "
          f"{float(e_erode):22.3f} | {pct(p_big):18.2f}%")

print()
print("=" * 74)
print("NATURAL RESULT RATES UNDER ADV / DIS")
print("=" * 74)
print(f"{'mode':>14} | {'P(nat 1)':>10} | {'P(nat 20)':>10} | {'ratio 1:20':>12}")
print("-" * 56)
for m in MODES:
    d = die_dist(m)
    p1, p20 = d[1], d[DIE]
    print(f"{m:>14} | {pct(p1):9.2f}% | {pct(p20):9.2f}% | "
          f"{float(p1 / p20):11.2f}x")
