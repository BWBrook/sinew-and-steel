"""Exact probability engine for the Sinew & Steel resolution rules.

Everything here is exact enumeration over the d20 (or 20x20 for opposed
tests). No simulation, so no Monte Carlo error. A separate script
cross-checks these results against random sampling.

Rules encoded (from rules/core/adventurers_manual.md, v0.3.1):
  * roll <= attribute succeeds; lower is better
  * natural 1 = legendary success, natural 20 = catastrophic failure
  * margin = attribute - roll
  * advantage = 2d20 keep lower; disadvantage = 2d20 keep higher
  * opposed: only-one-succeeds wins; both succeed -> higher margin;
    ties favour the defender; both fail -> defender
  * damage = 1 + edge + floor(margin / 5) - soak, minimum 1
  * natural 1 ignores all soak and adds +1 damage
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Tuple

DIE = 20
ONE = Fraction(1, DIE)


# ---------------------------------------------------------------------------
# Die distributions
# ---------------------------------------------------------------------------

def die_dist(mode: str = "straight") -> Dict[int, Fraction]:
    """Return {roll: probability} for the kept die under each mode."""
    if mode == "straight":
        return {r: ONE for r in range(1, DIE + 1)}
    if mode == "advantage":
        # keep lower of 2d20: P(X=k) = (2*(N-k) + 1) / N^2
        return {
            k: Fraction(2 * (DIE - k) + 1, DIE * DIE) for k in range(1, DIE + 1)
        }
    if mode == "disadvantage":
        # keep higher of 2d20: P(X=k) = (2*(k-1) + 1) / N^2
        return {
            k: Fraction(2 * (k - 1) + 1, DIE * DIE) for k in range(1, DIE + 1)
        }
    raise ValueError(f"unknown mode: {mode}")


MODES = ("straight", "advantage", "disadvantage")


# ---------------------------------------------------------------------------
# Simple checks
# ---------------------------------------------------------------------------

def is_success(roll: int, attribute: int) -> bool:
    """Natural 1 always succeeds; natural 20 always fails; else roll <= attr."""
    if roll == 1:
        return True
    if roll == DIE:
        return False
    return roll <= attribute


def p_success(attribute: int, mode: str = "straight") -> Fraction:
    dist = die_dist(mode)
    return sum(p for r, p in dist.items() if is_success(r, attribute))


def margin_dist_on_success(
    attribute: int, mode: str = "straight"
) -> Dict[int, Fraction]:
    """Conditional distribution of margin given the check succeeded."""
    dist = die_dist(mode)
    out: Dict[int, Fraction] = {}
    total = Fraction(0)
    for r, p in dist.items():
        if is_success(r, attribute):
            out[attribute - r] = out.get(attribute - r, Fraction(0)) + p
            total += p
    return {m: p / total for m, p in out.items()}


def mean_margin_on_success(attribute: int, mode: str = "straight") -> Fraction:
    return sum(m * p for m, p in margin_dist_on_success(attribute, mode).items())


def p_natural(attribute: int, mode: str, face: int) -> Fraction:
    """Probability of rolling a specific natural face (1 or 20)."""
    return die_dist(mode)[face]


# ---------------------------------------------------------------------------
# Opposed checks
# ---------------------------------------------------------------------------

def opposed_outcomes(
    att: int,
    dfn: int,
    att_mode: str = "straight",
    dfn_mode: str = "straight",
) -> Dict[str, Fraction]:
    """Enumerate the 400-cell joint space. Returns win probabilities and
    the reason each side won, so the tie/both-fail rules can be audited."""
    a_dist = die_dist(att_mode)
    d_dist = die_dist(dfn_mode)
    res = {
        "attacker": Fraction(0),
        "defender": Fraction(0),
        "att_only": Fraction(0),      # attacker succeeded, defender failed
        "both_succeed_att": Fraction(0),
        "both_succeed_dfn": Fraction(0),  # includes ties -> defender
        "both_fail": Fraction(0),
        "dfn_only": Fraction(0),
    }
    for a, pa in a_dist.items():
        for d, pd in d_dist.items():
            p = pa * pd
            a_ok = is_success(a, att)
            d_ok = is_success(d, dfn)
            if a_ok and not d_ok:
                res["attacker"] += p
                res["att_only"] += p
            elif d_ok and not a_ok:
                res["defender"] += p
                res["dfn_only"] += p
            elif not a_ok and not d_ok:
                res["defender"] += p
                res["both_fail"] += p
            else:
                ma, md = att - a, dfn - d
                if ma > md:
                    res["attacker"] += p
                    res["both_succeed_att"] += p
                else:  # ties favour the defender
                    res["defender"] += p
                    res["both_succeed_dfn"] += p
    return res


def p_attacker_wins(
    att: int, dfn: int, att_mode: str = "straight", dfn_mode: str = "straight"
) -> Fraction:
    return opposed_outcomes(att, dfn, att_mode, dfn_mode)["attacker"]


# ---------------------------------------------------------------------------
# Combat damage
# ---------------------------------------------------------------------------

MARGIN_STEP = 5  # every full MARGIN_STEP points of margin adds +1 damage


def margin_bonus(att_margin: int) -> int:
    return att_margin // MARGIN_STEP if att_margin > 0 else 0


def damage_for(att_roll: int, att_margin: int, edge: int, soak: int) -> int:
    """Damage from a winning attack.

    damage = 1 + edge + margin_bonus - soak, minimum 1.
    A natural 1 ignores soak and adds +1.
    """
    if att_roll == 1:
        return 1 + edge + margin_bonus(att_margin) + 1
    return max(1, 1 + edge + margin_bonus(att_margin) - soak)


def damage_dist(
    att: int,
    dfn: int,
    edge: int,
    soak: int,
    att_mode: str = "straight",
    dfn_mode: str = "straight",
) -> Dict[int, Fraction]:
    """Distribution of damage dealt in one exchange (0 includes misses)."""
    a_dist = die_dist(att_mode)
    d_dist = die_dist(dfn_mode)
    out: Dict[int, Fraction] = {}
    for a, pa in a_dist.items():
        for d, pd in d_dist.items():
            p = pa * pd
            a_ok, d_ok = is_success(a, att), is_success(d, dfn)
            ma, md = att - a, dfn - d
            attacker_wins = (a_ok and not d_ok) or (a_ok and d_ok and ma > md)
            dmg = damage_for(a, ma, edge, soak) if attacker_wins else 0
            out[dmg] = out.get(dmg, Fraction(0)) + p
    return out


def expected_damage(*args, **kwargs) -> Fraction:
    return sum(d * p for d, p in damage_dist(*args, **kwargs).items())


def expected_exchanges_to_drop(
    stamina: int,
    att: int,
    dfn: int,
    edge: int,
    soak: int,
    att_mode: str = "straight",
    dfn_mode: str = "straight",
):
    """Expected exchanges to take a target from `stamina` to 0.

    Solves E[s] = (1 + sum_{d>=1} P(d) E[s-d]) / (1 - P(0)).
    Returns None if no damage is ever possible.
    """
    dd = damage_dist(att, dfn, edge, soak, att_mode, dfn_mode)
    p_zero = dd.get(0, Fraction(0))
    if p_zero == 1:
        return None
    E: Dict[int, Fraction] = {s: Fraction(0) for s in range(-40, 1)}
    for s in range(1, stamina + 1):
        acc = Fraction(1)
        for d, p in dd.items():
            if d >= 1:
                acc += p * E[max(s - d, 0) if s - d >= -40 else -40]
        E[s] = acc / (1 - p_zero)
    return E[stamina]


# ---------------------------------------------------------------------------
# Luck token economics
# ---------------------------------------------------------------------------

def nudge_policy(attribute: int, threshold: int) -> Tuple[Fraction, Fraction]:
    """Post-hoc nudging: after seeing a straight d20, spend `deficit` tokens
    to convert a miss into a bare success whenever deficit <= threshold.
    Natural 20 is locked and cannot be rescued.

    Returns (success probability, expected tokens spent).
    """
    p = p_success(attribute)
    cost = Fraction(0)
    for deficit in range(1, threshold + 1):
        roll = attribute + deficit
        if roll >= DIE:  # natural 20 locked
            break
        p += ONE
        cost += ONE * deficit
    return p, cost


def luck_test(tokens: int) -> Fraction:
    """Luck tests succeed on roll <= current tokens (natural 1 always)."""
    return p_success(tokens)


# ---------------------------------------------------------------------------
# Point-buy ledger
# ---------------------------------------------------------------------------

ATTR_BASELINE = 10
STAM_BASELINE = 5


def cost_to_reach(target: int, baseline: int) -> int:
    """Build-point cost of moving a score from baseline to target.

    +1 at/above baseline costs 2; +1 below baseline costs 1 (climbing back).
    Moving below baseline refunds 1 per step.
    """
    if target >= baseline:
        return 2 * (target - baseline)
    return -(baseline - target)


def build_cost(attrs: List[int], stamina: int) -> int:
    return sum(cost_to_reach(a, ATTR_BASELINE) for a in attrs) + cost_to_reach(
        stamina, STAM_BASELINE
    )
