"""Luck token economics."""
from fractions import Fraction
from engine import (
    DIE, ONE, die_dist, is_success, p_success, nudge_policy, luck_test,
    effective_soak,
)


def pct(f) -> float:
    return round(float(f) * 100, 2)


print("=" * 78)
print("1. POST-HOC NUDGING IS STRICTLY EFFICIENT")
print("=" * 78)
print("""
Tokens are spent AFTER the die is read, so you never pay for a roll that
already succeeded, nor for one you cannot save. Under the policy
"spend `deficit` tokens whenever deficit <= n":

    P(success) = attribute/20 + n/20
    E[tokens]  = (1/20) * n(n+1)/2

The n-th rescue tier costs n tokens, fires 5% of the time, and buys a flat
+5pp. Cheap rescues are cheap; deep rescues are quadratically dear.
""")
print(f"{'attr':>5} {'n':>3} | {'P(success)':>11} | {'E[tokens/check]':>16} | "
      f"{'tokens per +5pp':>16}")
print("-" * 62)
for attr in (10, 12):
    for n in range(0, 7):
        p, cost = nudge_policy(attr, n)
        print(f"{attr:>5} {n:>3} | {pct(p):10.2f}% | {float(cost):16.3f} | "
              f"{n:>16}")
    print("-" * 62)

print()
print("=" * 78)
print("2. WHAT A TOKEN COSTS YOU LATER")
print("=" * 78)
print("A Luck test succeeds on roll <= CURRENT tokens, so each token spent")
print("removes exactly 5pp from every future Luck test until restored.")
print()
print(f"{'tokens':>7} | {'P(Luck test)':>13}")
print("-" * 24)
for t in range(0, 13):
    print(f"{t:>7} | {pct(luck_test(t)):12.2f}%")
print()
print("Exchange rate: rescuing a deficit-d miss buys one CERTAIN success now")
print("and costs 5*d percentage points of every future Luck test.")
print()
print("The Almanac's thresholds check out: pool 4 = 20% Luck test, pool 2 = 10%.")

print()
print("=" * 78)
print("3. SUSTAINABILITY: refresh vs burn")
print("=" * 78)
print("Refresh is +1 per short rest plus a full refill at each milestone, so")
print("the budget per milestone cycle is roughly (Luck score + short rests).")
print()
for score in (6, 8, 10, 12):
    for rests in (0, 2, 4):
        b = score + rests
        print(f"  Luck {score:2d}, {rests} short rests -> {b:2d} tokens = "
              f"{b:2d} deficit-1 rescues, {b // 2:2d} deficit-2, "
              f"{b // 3:2d} deficit-3, {b // 4:2d} deficit-4")

print()
print("=" * 78)
print("4. NUDGING FOR ARMOUR PENETRATION (the Almanac's combat note)")
print("=" * 78)
print("Each 4 points of margin strips one point of soak, so how many tokens")
print("actually buy one extra point of damage?")
print()
for soak in (1, 2, 3):
    for edge in (0, 1, 2):
        gains = []
        for r in range(2, DIE):
            attr = 12
            if r > attr:
                continue
            m = attr - r
            base = max(0, 1 + edge - effective_soak(soak, r, m))
            need = 4 * ((m // 4) + 1) - m
            after = max(0, 1 + edge - effective_soak(soak, r, m + need))
            if after > base:
                gains.append(need)
        if gains:
            print(f"  soak {soak}, edge {edge:+d}, attr 12: {len(gains)} of 11 "
                  f"winning rolls can buy +1 damage, mean cost "
                  f"{sum(gains) / len(gains):.1f} tokens")
        else:
            print(f"  soak {soak}, edge {edge:+d}, attr 12: no winning roll can "
                  f"buy extra damage with tokens")
print()
print("Against 1 token to convert a near-miss into a hit, 2.5-3 tokens for one")
print("point of damage is the worst use of the pool in the game.")

print()
print("=" * 78)
print("5. AMBIGUITY: when is Luck spent in an OPPOSED test?")
print("=" * 78)
print("The rules say tokens are spent 'after you see a roll' but not whether,")
print("in an opposed test, you may wait for the opponent's die too.")
print()
attr, dfn = 12, 12
d_dist = die_dist("straight")

p_blind, cost_blind = Fraction(0), Fraction(0)
for a in range(1, DIE + 1):
    for d, pd in d_dist.items():
        p = ONE * pd
        a_eff, spend = a, 0
        if not is_success(a, attr) and a != DIE:
            deficit = a - attr
            if deficit <= 3:
                a_eff, spend = attr, deficit
        a_ok, d_ok = is_success(a_eff, attr), is_success(d, dfn)
        ma, md = attr - a_eff, dfn - d
        if (a_ok and not d_ok) or (a_ok and d_ok and ma > md):
            p_blind += p
        cost_blind += p * spend

p_inf, cost_inf = Fraction(0), Fraction(0)
for a in range(1, DIE + 1):
    for d, pd in d_dist.items():
        p = ONE * pd
        d_ok = is_success(d, dfn)
        md = dfn - d
        best_spend, won = 0, False
        for spend in range(0, 4):
            a_eff = a if a in (1, DIE) else a - spend
            if a_eff < 1:
                break
            a_ok = is_success(a_eff, attr)
            ma = attr - a_eff
            if (a_ok and not d_ok) or (a_ok and d_ok and ma > md):
                best_spend, won = spend, True
                break
        if won:
            p_inf += p
            cost_inf += p * best_spend

base_p = Fraction(0)
for a in range(1, DIE + 1):
    for d, pd in d_dist.items():
        p = ONE * pd
        a_ok, d_ok = is_success(a, attr), is_success(d, dfn)
        if (a_ok and not d_ok) or (a_ok and d_ok and (attr - a) > (dfn - d)):
            base_p += p

print("  att 12 vs def 12, budget 3 tokens per exchange:")
print(f"    no spending          : win {pct(base_p):6.2f}%")
print(f"    blind (own die only) : win {pct(p_blind):6.2f}%  "
      f"at {float(cost_blind):.3f} tokens/exchange  "
      f"= {float((p_blind - base_p) / cost_blind) * 100:.2f}pp per token")
print(f"    informed (both dice) : win {pct(p_inf):6.2f}%  "
      f"at {float(cost_inf):.3f} tokens/exchange  "
      f"= {float((p_inf - base_p) / cost_inf) * 100:.2f}pp per token")
print()
print("A table reading it one way and a table reading it the other are playing")
print("measurably different games. One clause in section 1.4 settles it.")
