"""Independent Monte Carlo cross-check of the exact engine.

Deliberately re-implements the resolution rules from the book text rather than
importing them, so a shared bug cannot hide. ~25 s.
"""
import random

from engine import (
    p_success, p_attacker_wins, expected_damage, expected_exchanges_to_drop,
    nudge_policy,
)

random.seed(20260904)
N = 2_000_000


def roll_d20(mode="straight"):
    a = random.randint(1, 20)
    if mode == "straight":
        return a
    b = random.randint(1, 20)
    return min(a, b) if mode == "advantage" else max(a, b)


def succeeds(r, attr):
    if r == 1:
        return True
    if r == 20:
        return False
    return r <= attr


def mc_success(attr, mode, n=N):
    return sum(succeeds(roll_d20(mode), attr) for _ in range(n)) / n


def mc_opposed(att, dfn, n=N):
    wins = 0
    for _ in range(n):
        a, d = roll_d20(), roll_d20()
        ao, do = succeeds(a, att), succeeds(d, dfn)
        if ao and not do:
            wins += 1
        elif ao and do and (att - a) > (dfn - d):
            wins += 1
    return wins / n


def mc_damage(att, dfn, edge, soak, n=N):
    tot = 0
    for _ in range(n):
        a, d = roll_d20(), roll_d20()
        ao, do = succeeds(a, att), succeeds(d, dfn)
        ma, md = att - a, dfn - d
        if not ((ao and not do) or (ao and do and ma > md)):
            continue
        eff = 0 if a == 1 else max(0, soak - (ma // 4))
        tot += max(0, 1 + edge - eff) + (1 if (a == 1 or ma >= 10) else 0)
    return tot / n


def mc_exchanges(stamina, att, dfn, edge, soak, n=200_000):
    tot = 0
    for _ in range(n):
        s, k = stamina, 0
        while s > 0 and k <= 5000:
            k += 1
            a, d = roll_d20(), roll_d20()
            ao, do = succeeds(a, att), succeeds(d, dfn)
            ma, md = att - a, dfn - d
            if not ((ao and not do) or (ao and do and ma > md)):
                continue
            eff = 0 if a == 1 else max(0, soak - (ma // 4))
            s -= max(0, 1 + edge - eff) + (1 if (a == 1 or ma >= 10) else 0)
        tot += k
    return tot / n


def mc_nudge(attr, threshold, n=N):
    succ, cost = 0, 0
    for _ in range(n):
        r = roll_d20()
        if succeeds(r, attr):
            succ += 1
        elif r != 20 and (r - attr) <= threshold:
            cost += r - attr
            succ += 1
    return succ / n, cost / n


print("Cross-checking exact enumeration against Monte Carlo")
print(f"(n = {N:,} for probabilities, 200,000 trials for time-to-kill)")
print()

CHECKS = [
    ("P(success) attr 12 straight", float(p_success(12)), mc_success(12, "straight")),
    ("P(success) attr 12 advantage", float(p_success(12, "advantage")), mc_success(12, "advantage")),
    ("P(success) attr 8 disadvantage", float(p_success(8, "disadvantage")), mc_success(8, "disadvantage")),
    ("P(att wins) 12 vs 12", float(p_attacker_wins(12, 12)), mc_opposed(12, 12)),
    ("P(att wins) 16 vs 10", float(p_attacker_wins(16, 10)), mc_opposed(16, 10)),
    ("P(att wins) 6 vs 14", float(p_attacker_wins(6, 14)), mc_opposed(6, 14)),
    ("E[dmg] 12 vs 10, edge+1 soak2", float(expected_damage(12, 10, 1, 2)), mc_damage(12, 10, 1, 2)),
    ("E[dmg] 8 vs 10, edge+0 soak2", float(expected_damage(8, 10, 0, 2)), mc_damage(8, 10, 0, 2)),
    ("E[dmg] 16 vs 10, edge+2 soak3", float(expected_damage(16, 10, 2, 3)), mc_damage(16, 10, 2, 3)),
]
for label, exact, mc in CHECKS:
    delta = mc - exact
    flag = "ok" if abs(delta) < max(0.003, 0.01 * abs(exact)) else "CHECK"
    print(f"  {label:<34} exact {exact:9.5f}   mc {mc:9.5f}   "
          f"delta {delta:+.5f}  {flag}")

print()
TTK = [
    ("Nemesis (STM7 soak3) vs PC att 12", 7, 12, 14, 1, 3),
    ("Elite (STM5 soak1) vs PC att 12", 5, 12, 10, 1, 1),
    ("PC (STM5) vs Monster att 14 edge+2", 5, 14, 10, 2, 0),
]
for label, stm, att, dfn, edge, soak in TTK:
    exact = float(expected_exchanges_to_drop(stm, att, dfn, edge, soak))
    mc = mc_exchanges(stm, att, dfn, edge, soak)
    delta = mc - exact
    flag = "ok" if abs(delta) < max(0.05, 0.02 * exact) else "CHECK"
    print(f"  {label:<38} exact {exact:8.3f}   mc {mc:8.3f}   "
          f"delta {delta:+.3f}  {flag}")

print()
for attr, thr in ((12, 3), (10, 5)):
    ep, ec = nudge_policy(attr, thr)
    mp, mc = mc_nudge(attr, thr)
    print(f"  nudge attr {attr} thr {thr}: "
          f"P exact {float(ep):.5f} mc {mp:.5f} | "
          f"tokens exact {float(ec):.5f} mc {mc:.5f}")
