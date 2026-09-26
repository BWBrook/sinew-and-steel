#!/usr/bin/env python3
"""Independent combat analysis for Sinew & Steel.

This module intentionally encodes the published rules directly.  It does not
import or depend on the engine-atlas implementation.  It provides exact d20
opposed/damage distributions and small, seeded, coupled combat simulations.

Run from the repository root:

    python3 tools/analysis/independent_combat.py

Outputs are written under ``docs/independent_engine`` by default.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
import statistics
from collections import Counter
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence


MODE_PLAIN = "plain"
MODE_ADV = "advantage"
MODE_DIS = "disadvantage"
MODES = (MODE_PLAIN, MODE_ADV, MODE_DIS)


def roll_pmf(mode: str) -> dict[int, float]:
    """Exact PMF of the kept face for plain, advantage, or disadvantage."""
    if mode == MODE_PLAIN:
        return {face: 1.0 / 20.0 for face in range(1, 21)}
    counts: Counter[int] = Counter()
    for first in range(1, 21):
        for second in range(1, 21):
            if mode == MODE_ADV:
                kept = min(first, second)
            elif mode == MODE_DIS:
                kept = max(first, second)
            else:
                raise ValueError(f"unknown roll mode: {mode}")
            counts[kept] += 1
    return {face: count / 400.0 for face, count in sorted(counts.items())}


ROLL_PMFS = {mode: roll_pmf(mode) for mode in MODES}


def succeeds(
    score: int,
    face: int,
    natural1: bool | None = None,
    natural20: bool | None = None,
) -> bool:
    is_natural1 = face == 1 if natural1 is None else natural1
    is_natural20 = face == 20 if natural20 is None else natural20
    if is_natural1:
        return True
    if is_natural20:
        return False
    return face <= score


def attacker_wins(
    att_score: int,
    att_face: int,
    def_score: int,
    def_face: int,
    att_natural1: bool | None = None,
    att_natural20: bool | None = None,
    def_natural1: bool | None = None,
    def_natural20: bool | None = None,
) -> bool:
    """Published opposed-test rule, including defender-favoured ties/failures."""
    att_ok = succeeds(att_score, att_face, att_natural1, att_natural20)
    def_ok = succeeds(def_score, def_face, def_natural1, def_natural20)
    if att_ok != def_ok:
        return att_ok
    if not att_ok:  # both fail
        return False
    att_margin = att_score - att_face
    def_margin = def_score - def_face
    return att_margin > def_margin  # ties favour defender


def damage_on_hit(
    att_score: int,
    att_face: int,
    edge: int,
    soak: int,
    natural1: bool | None = None,
) -> int:
    """Damage after a hit; a raw/kept 1 is treated as the natural-1 result."""
    margin = att_score - att_face
    bonus = max(0, margin) // 5
    is_natural1 = att_face == 1 if natural1 is None else natural1
    if is_natural1:
        return 1 + edge + bonus + 1  # ignore soak and add one
    return max(1, 1 + edge + bonus - soak)


def effective_margin(
    att_score: int,
    att_face: int,
    def_score: int,
    def_face: int,
    def_natural1: bool | None = None,
    def_natural20: bool | None = None,
) -> int:
    att_margin = att_score - att_face
    if succeeds(def_score, def_face, def_natural1, def_natural20):
        return att_margin - (def_score - def_face)
    return att_margin


def exact_exchange(
    att_score: int,
    def_score: int,
    edge: int = 1,
    soak: int = 1,
    att_mode: str = MODE_PLAIN,
    def_mode: str = MODE_PLAIN,
) -> dict[str, float]:
    """Enumerate an attack/defence exchange exactly, without resource spends."""
    hit_probability = 0.0
    unconditional_damage = 0.0
    damage_pmf: Counter[int] = Counter()
    injury_trigger_nat1 = 0.0
    injury_trigger_gritty = 0.0
    for att_face, att_prob in ROLL_PMFS[att_mode].items():
        for def_face, def_prob in ROLL_PMFS[def_mode].items():
            weight = att_prob * def_prob
            if not attacker_wins(att_score, att_face, def_score, def_face):
                damage_pmf[0] += weight
                continue
            hit_probability += weight
            damage = damage_on_hit(att_score, att_face, edge, soak)
            unconditional_damage += weight * damage
            damage_pmf[damage] += weight
            if att_face == 1:
                injury_trigger_nat1 += weight
            if att_face == 1 or effective_margin(
                att_score, att_face, def_score, def_face
            ) >= 8:
                injury_trigger_gritty += weight
    conditional_damage = unconditional_damage / hit_probability if hit_probability else 0.0
    result = {
        "hit_probability": hit_probability,
        "expected_damage_per_action": unconditional_damage,
        "expected_damage_given_hit": conditional_damage,
        "injury_trigger_nat1_per_action": injury_trigger_nat1,
        "injury_trigger_gritty_per_action": injury_trigger_gritty,
    }
    for damage, probability in sorted(damage_pmf.items()):
        result[f"p_damage_{damage}"] = probability
    return result


def exact_damage_pmf(
    att_score: int,
    def_score: int,
    edge: int,
    soak: int,
    att_mode: str = MODE_PLAIN,
    def_mode: str = MODE_PLAIN,
) -> dict[int, float]:
    """Exact unconditional damage PMF for one declared action."""
    pmf: Counter[int] = Counter()
    for att_face, att_prob in ROLL_PMFS[att_mode].items():
        for def_face, def_prob in ROLL_PMFS[def_mode].items():
            weight = att_prob * def_prob
            if attacker_wins(att_score, att_face, def_score, def_face):
                damage = damage_on_hit(att_score, att_face, edge, soak)
                pmf[damage] += weight
            else:
                pmf[0] += weight
    assert math.isclose(sum(pmf.values()), 1.0, abs_tol=1e-12)
    return dict(sorted(pmf.items()))


def exact_duel_win_probability(
    pc_spec: "CombatantSpec", npc_spec: "CombatantSpec", pc_first: bool
) -> float:
    """Exact coupled no-Luck/no-Injury duel probability.

    Each recursion step is a full round.  The only cycle is a double miss,
    which is removed analytically.  Every other transition lowers at least one
    Stamina value, so memoised recursion terminates.
    """
    pc_damage = exact_damage_pmf(
        pc_spec.attack,
        npc_spec.defence,
        pc_spec.edge,
        npc_spec.soak,
        attack_mode(Fighter.fresh(pc_spec)),
        defence_mode(Fighter.fresh(npc_spec), screened=False),
    )
    npc_damage = exact_damage_pmf(
        npc_spec.attack,
        pc_spec.defence,
        npc_spec.edge,
        pc_spec.soak,
        attack_mode(Fighter.fresh(npc_spec)),
        defence_mode(Fighter.fresh(pc_spec), screened=False),
    )
    self_loop = pc_damage.get(0, 0.0) * npc_damage.get(0, 0.0)

    @lru_cache(maxsize=None)
    def solve(pc_stamina: int, npc_stamina: int) -> float:
        numerator = 0.0
        if pc_first:
            for dealt, p_dealt in pc_damage.items():
                if dealt >= npc_stamina:
                    numerator += p_dealt
                    continue
                for taken, p_taken in npc_damage.items():
                    weight = p_dealt * p_taken
                    if dealt == 0 and taken == 0:
                        continue
                    if taken >= pc_stamina:
                        continue
                    numerator += weight * solve(
                        pc_stamina - taken, npc_stamina - dealt
                    )
        else:
            for taken, p_taken in npc_damage.items():
                if taken >= pc_stamina:
                    continue
                for dealt, p_dealt in pc_damage.items():
                    weight = p_taken * p_dealt
                    if dealt == 0 and taken == 0:
                        continue
                    if dealt >= npc_stamina:
                        numerator += weight
                    else:
                        numerator += weight * solve(
                            pc_stamina - taken, npc_stamina - dealt
                        )
        return numerator / (1.0 - self_loop)

    return solve(pc_spec.stamina, npc_spec.stamina)


def draw_roll(rng: random.Random, mode: str) -> int:
    first = rng.randint(1, 20)
    if mode == MODE_PLAIN:
        return first
    second = rng.randint(1, 20)
    if mode == MODE_ADV:
        return min(first, second)
    if mode == MODE_DIS:
        return max(first, second)
    raise ValueError(f"unknown roll mode: {mode}")


def combine_mode(advantages: int = 0, disadvantages: int = 0) -> str:
    """Use the lean non-stacking interpretation: opposing states cancel."""
    if advantages and disadvantages:
        return MODE_PLAIN
    if advantages:
        return MODE_ADV
    if disadvantages:
        return MODE_DIS
    return MODE_PLAIN


@dataclass(frozen=True)
class CombatantSpec:
    name: str
    side: str
    attack: int
    defence: int
    stamina: int
    edge: int
    soak: int
    hope: int = 0
    player: bool = False
    stance: str = "steady"
    ranged: bool = False
    tagged_attack: bool = False


@dataclass
class Fighter:
    spec: CombatantSpec
    stamina: int
    hope: int
    injured: bool = False
    injuries: int = 0
    luck_spent: int = 0

    @classmethod
    def fresh(cls, spec: CombatantSpec) -> "Fighter":
        return cls(spec=spec, stamina=spec.stamina, hope=spec.hope)

    @property
    def alive(self) -> bool:
        return self.stamina > 0


@dataclass(frozen=True)
class Scenario:
    name: str
    pcs: tuple[CombatantSpec, ...]
    npcs: tuple[CombatantSpec, ...]
    initiative: str = "random"  # pc_first, npc_first, or fair side-order draw
    targeting: str = "focus"  # focus, random, pc_focus, or npc_focus
    injury_rule: str = "none"  # none, natural1, or gritty
    luck_policy: str = "decisive"  # none or decisive
    hope_cap: int = 2  # maximum tokens per flip/Deflection/KO-deepening decision
    max_rounds: int = 50
    hold_rounds: int = 3
    group: str = "duel"
    note: str = ""


@dataclass(frozen=True)
class CombatResult:
    winner: str
    rounds: int
    first_side: str
    pc_survivors: int
    npc_survivors: int
    pc_stamina_lost: int
    npc_stamina_lost: int
    pc_injured: int
    npc_injured: int
    pc_luck_spent: int
    pcs_alive_at_hold: int
    pc_stamina_at_hold: int


def attack_mode(fighter: Fighter) -> str:
    advantages = 0
    disadvantages = 0
    if fighter.spec.stance in ("vanguard", "ranged"):
        advantages += 1
    elif fighter.spec.stance == "watchful":
        disadvantages += 1
    if fighter.spec.tagged_attack:
        advantages += 1
    if fighter.injured:
        disadvantages += 1
    return combine_mode(advantages, disadvantages)


def defence_mode(fighter: Fighter, screened: bool) -> str:
    advantages = 1 if fighter.spec.stance == "watchful" else 0
    disadvantages = 1 if fighter.spec.stance == "vanguard" else 0
    if fighter.spec.stance == "ranged" and not screened:
        disadvantages += 1
    if fighter.injured:
        disadvantages += 1
    return combine_mode(advantages, disadvantages)


def min_attack_nudge(
    attacker: Fighter,
    defender: Fighter,
    att_face: int,
    def_face: int,
    att_natural1: bool,
    att_natural20: bool,
    def_natural1: bool,
    def_natural20: bool,
    cap: int = 2,
    allow_other_die: bool = True,
) -> tuple[int, int] | None:
    """Cheapest legal (attacker down, defender up) shift that creates a hit."""
    if attacker_wins(
        attacker.spec.attack,
        att_face,
        defender.spec.defence,
        def_face,
        att_natural1,
        att_natural20,
        def_natural1,
        def_natural20,
    ):
        return None
    for total in range(1, min(cap, attacker.hope) + 1):
        for own_cost in range(total, -1, -1):
            other_cost = total - own_cost
            if other_cost and not allow_other_die:
                continue
            if own_cost and (att_natural1 or att_natural20):
                continue
            if other_cost and (def_natural1 or def_natural20):
                continue
            adjusted_att = att_face - own_cost
            adjusted_def = def_face + other_cost
            if adjusted_att < 1 or adjusted_def > 20:
                continue
            if attacker_wins(
                attacker.spec.attack,
                adjusted_att,
                defender.spec.defence,
                adjusted_def,
                att_natural1,
                att_natural20,
                def_natural1,
                def_natural20,
            ):
                return own_cost, other_cost
    return None


def min_defence_nudge(
    attacker: Fighter,
    defender: Fighter,
    att_face: int,
    def_face: int,
    att_natural1: bool,
    att_natural20: bool,
    def_natural1: bool,
    def_natural20: bool,
    cap: int = 2,
    allow_other_die: bool = True,
) -> tuple[int, int] | None:
    if not attacker_wins(
        attacker.spec.attack,
        att_face,
        defender.spec.defence,
        def_face,
        att_natural1,
        att_natural20,
        def_natural1,
        def_natural20,
    ):
        return None
    for total in range(1, min(cap, defender.hope) + 1):
        for own_cost in range(total, -1, -1):
            other_cost = total - own_cost
            if other_cost and not allow_other_die:
                continue
            if own_cost and (def_natural1 or def_natural20):
                continue
            if other_cost and (att_natural1 or att_natural20):
                continue
            adjusted_def = def_face - own_cost
            adjusted_att = att_face + other_cost
            if adjusted_def < 1 or adjusted_att > 20:
                continue
            if not attacker_wins(
                attacker.spec.attack,
                adjusted_att,
                defender.spec.defence,
                adjusted_def,
                att_natural1,
                att_natural20,
                def_natural1,
                def_natural20,
            ):
                return other_cost, own_cost
    return None


def spend(fighter: Fighter, amount: int) -> None:
    fighter.hope -= amount
    fighter.luck_spent += amount


def deepen_for_ko(
    attacker: Fighter,
    defender: Fighter,
    att_face: int,
    att_natural1: bool,
    att_natural20: bool,
    current_damage: int,
    cap: int = 2,
) -> tuple[int, int]:
    """Spend only when the next margin threshold changes this hit into a KO."""
    if att_natural1 or att_natural20 or current_damage >= defender.stamina:
        return att_face, current_damage
    max_cost = min(cap, attacker.hope, max(0, att_face - 1))
    for cost in range(1, max_cost + 1):
        adjusted = att_face - cost
        damage = damage_on_hit(
            attacker.spec.attack,
            adjusted,
            attacker.spec.edge,
            defender.spec.soak,
            natural1=False,
        )
        if damage >= defender.stamina:
            spend(attacker, cost)
            return adjusted, damage
    return att_face, current_damage


def deflection_failure(
    rng: random.Random, defender: Fighter, luck_policy: str, hope_cap: int
) -> bool:
    score = 10 + 2 * defender.spec.soak
    face = rng.randint(1, 20)
    if face <= score:
        return False
    if (
        luck_policy in ("decisive", "own_decisive")
        and defender.spec.player
        and face not in (1, 20)
    ):
        needed = face - score
        if 1 <= needed <= hope_cap and needed <= defender.hope:
            spend(defender, needed)
            return False
    return True


def choose_target(
    rng: random.Random,
    actor: Fighter,
    opponents: Sequence[Fighter],
    targeting: str,
) -> tuple[Fighter, bool]:
    alive = [target for target in opponents if target.alive]
    if not alive:
        raise ValueError("no living target")
    frontliners = [target for target in alive if not target.spec.ranged]
    if not actor.spec.ranged and frontliners:
        eligible = frontliners
    else:
        eligible = alive
    if targeting == "random":
        target = rng.choice(eligible)
    elif targeting == "focus":
        target = min(eligible, key=lambda x: (x.stamina, x.spec.name))
    else:
        raise ValueError(f"unknown targeting policy: {targeting}")
    screened = target.spec.ranged and bool(frontliners)
    return target, screened


def targeting_for_actor(scenario_policy: str, actor_side: str) -> str:
    if scenario_policy in ("focus", "random"):
        return scenario_policy
    if scenario_policy == "pc_focus":
        return "focus" if actor_side == "pc" else "random"
    if scenario_policy == "npc_focus":
        return "random" if actor_side == "pc" else "focus"
    raise ValueError(f"unknown targeting policy: {scenario_policy}")


def resolve_attack(
    rng: random.Random,
    attacker: Fighter,
    defender: Fighter,
    screened: bool,
    injury_rule: str,
    luck_policy: str,
    hope_cap: int,
) -> None:
    att_face = draw_roll(rng, attack_mode(attacker))
    def_face = draw_roll(rng, defence_mode(defender, screened))
    att_natural1 = att_face == 1
    att_natural20 = att_face == 20
    def_natural1 = def_face == 1
    def_natural20 = def_face == 20

    # Only PCs hold Hope in the scenarios.  A PC defender protects itself first;
    # a PC attacker then tries to turn a miss.  This avoids an unspecified
    # counter-spending game between two resource-bearing sides.
    uses_decisive = luck_policy in ("decisive", "own_decisive")
    allow_other_die = luck_policy == "decisive"
    if uses_decisive and defender.spec.player:
        shifts = min_defence_nudge(
            attacker,
            defender,
            att_face,
            def_face,
            att_natural1,
            att_natural20,
            def_natural1,
            def_natural20,
            cap=hope_cap,
            allow_other_die=allow_other_die,
        )
        if shifts is not None:
            attack_up, defence_down = shifts
            att_face += attack_up
            def_face -= defence_down
            spend(defender, attack_up + defence_down)
    if uses_decisive and attacker.spec.player:
        shifts = min_attack_nudge(
            attacker,
            defender,
            att_face,
            def_face,
            att_natural1,
            att_natural20,
            def_natural1,
            def_natural20,
            cap=hope_cap,
            allow_other_die=allow_other_die,
        )
        if shifts is not None:
            attack_down, defence_up = shifts
            att_face -= attack_down
            def_face += defence_up
            spend(attacker, attack_down + defence_up)

    if not attacker_wins(
        attacker.spec.attack,
        att_face,
        defender.spec.defence,
        def_face,
        att_natural1,
        att_natural20,
        def_natural1,
        def_natural20,
    ):
        return
    damage = damage_on_hit(
        attacker.spec.attack,
        att_face,
        attacker.spec.edge,
        defender.spec.soak,
        att_natural1,
    )
    if uses_decisive and attacker.spec.player:
        att_face, damage = deepen_for_ko(
            attacker,
            defender,
            att_face,
            att_natural1,
            att_natural20,
            damage,
            cap=hope_cap,
        )
    defender.stamina = max(0, defender.stamina - damage)
    if not defender.alive or injury_rule == "none":
        return

    trigger = att_natural1
    if injury_rule == "gritty":
        trigger = trigger or effective_margin(
            attacker.spec.attack,
            att_face,
            defender.spec.defence,
            def_face,
            def_natural1,
            def_natural20,
        ) >= 8
    elif injury_rule != "natural1":
        raise ValueError(f"unknown injury rule: {injury_rule}")
    if not trigger or not deflection_failure(
        rng, defender, luck_policy, hope_cap
    ):
        return
    defender.injuries += 1
    if defender.injured:
        defender.stamina = 0
    else:
        defender.injured = True


def simulate_once(scenario: Scenario, rng: random.Random) -> CombatResult:
    pcs = [Fighter.fresh(spec) for spec in scenario.pcs]
    npcs = [Fighter.fresh(spec) for spec in scenario.npcs]
    if scenario.initiative == "random":
        first_side = rng.choice(("pc", "npc"))
    elif scenario.initiative in ("pc_first", "npc_first"):
        first_side = "pc" if scenario.initiative == "pc_first" else "npc"
    else:
        raise ValueError(f"unknown initiative: {scenario.initiative}")
    sides = ((pcs, npcs), (npcs, pcs)) if first_side == "pc" else ((npcs, pcs), (pcs, npcs))

    pcs_alive_at_hold = -1
    pc_stamina_at_hold = -1
    completed_rounds = 0
    for round_number in range(1, scenario.max_rounds + 1):
        for actors, opponents in sides:
            for actor in actors:
                if not actor.alive or not any(target.alive for target in opponents):
                    continue
                target, screened = choose_target(
                    rng,
                    actor,
                    opponents,
                    targeting_for_actor(scenario.targeting, actor.spec.side),
                )
                resolve_attack(
                    rng,
                    actor,
                    target,
                    screened,
                    scenario.injury_rule,
                    scenario.luck_policy,
                    scenario.hope_cap,
                )
        completed_rounds = round_number
        if round_number == scenario.hold_rounds:
            pcs_alive_at_hold = sum(f.alive for f in pcs)
            pc_stamina_at_hold = sum(f.stamina for f in pcs)
        if not any(f.alive for f in pcs) or not any(f.alive for f in npcs):
            break

    if pcs_alive_at_hold < 0:
        pcs_alive_at_hold = sum(f.alive for f in pcs)
        pc_stamina_at_hold = sum(f.stamina for f in pcs)
    pc_alive = sum(f.alive for f in pcs)
    npc_alive = sum(f.alive for f in npcs)
    if pc_alive and not npc_alive:
        winner = "pc"
    elif npc_alive and not pc_alive:
        winner = "npc"
    else:
        winner = "draw"
    return CombatResult(
        winner=winner,
        rounds=completed_rounds,
        first_side=first_side,
        pc_survivors=pc_alive,
        npc_survivors=npc_alive,
        pc_stamina_lost=sum(f.spec.stamina - f.stamina for f in pcs),
        npc_stamina_lost=sum(f.spec.stamina - f.stamina for f in npcs),
        pc_injured=sum(f.injured for f in pcs),
        npc_injured=sum(f.injured for f in npcs),
        pc_luck_spent=sum(f.luck_spent for f in pcs),
        pcs_alive_at_hold=pcs_alive_at_hold,
        pc_stamina_at_hold=pc_stamina_at_hold,
    )


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials == 0:
        return (math.nan, math.nan)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return centre - half, centre + half


def mean_se(values: Sequence[float]) -> tuple[float, float]:
    mean = statistics.fmean(values)
    if len(values) < 2:
        return mean, math.nan
    return mean, statistics.stdev(values) / math.sqrt(len(values))


def scenario_seed(master_seed: int, name: str) -> int:
    digest = hashlib.sha256(f"{master_seed}:{name}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def run_scenario(scenario: Scenario, reps: int, master_seed: int) -> dict[str, object]:
    rng = random.Random(scenario_seed(master_seed, scenario.name))
    results = [simulate_once(scenario, rng) for _ in range(reps)]
    wins = sum(result.winner == "pc" for result in results)
    holds = sum(result.pcs_alive_at_hold > 0 for result in results)
    win_low, win_high = wilson_interval(wins, reps)
    hold_low, hold_high = wilson_interval(holds, reps)
    round_mean, round_se = mean_se([result.rounds for result in results])
    loss_mean, loss_se = mean_se([result.pc_stamina_lost for result in results])
    luck_mean, luck_se = mean_se([result.pc_luck_spent for result in results])
    survivor_mean, survivor_se = mean_se([result.pc_survivors for result in results])
    injury_mean, injury_se = mean_se([result.pc_injured for result in results])
    npc_injury_mean, npc_injury_se = mean_se(
        [result.npc_injured for result in results]
    )
    first_pc = [result for result in results if result.first_side == "pc"]
    first_npc = [result for result in results if result.first_side == "npc"]
    p_win_pc_first = (
        sum(result.winner == "pc" for result in first_pc) / len(first_pc)
        if first_pc
        else math.nan
    )
    p_win_npc_first = (
        sum(result.winner == "pc" for result in first_npc) / len(first_npc)
        if first_npc
        else math.nan
    )
    return {
        "section": "simulation",
        "group": scenario.group,
        "scenario": scenario.name,
        "reps": reps,
        "seed": scenario_seed(master_seed, scenario.name),
        "p_pc_win": wins / reps,
        "p_pc_win_ci_low": win_low,
        "p_pc_win_ci_high": win_high,
        "p_hold_survival": holds / reps,
        "p_hold_ci_low": hold_low,
        "p_hold_ci_high": hold_high,
        "mean_rounds": round_mean,
        "se_rounds": round_se,
        "mean_pc_stamina_lost": loss_mean,
        "se_pc_stamina_lost": loss_se,
        "mean_pc_survivors": survivor_mean,
        "se_pc_survivors": survivor_se,
        "mean_pc_injured": injury_mean,
        "se_pc_injured": injury_se,
        "mean_npc_injured": npc_injury_mean,
        "se_npc_injured": npc_injury_se,
        "mean_pc_luck_spent": luck_mean,
        "se_pc_luck_spent": luck_se,
        "p_pc_win_given_pc_first": p_win_pc_first,
        "p_pc_win_given_npc_first": p_win_npc_first,
        "initiative": scenario.initiative,
        "targeting": scenario.targeting,
        "injury_rule": scenario.injury_rule,
        "luck_policy": scenario.luck_policy,
        "hope_cap": scenario.hope_cap,
        "note": scenario.note,
    }


def npc(
    name: str,
    tier: int,
    stamina: int,
    edge: int,
    soak: int,
    count: int = 1,
    defence: int | None = None,
) -> tuple[CombatantSpec, ...]:
    return tuple(
        CombatantSpec(
            name=f"{name}_{index + 1}",
            side="npc",
            attack=tier,
            defence=tier if defence is None else defence,
            stamina=stamina,
            edge=edge,
            soak=soak,
        )
        for index in range(count)
    )


def pc(
    name: str,
    attack: int,
    defence: int,
    stamina: int,
    edge: int,
    soak: int,
    hope: int,
    **kwargs: object,
) -> CombatantSpec:
    return CombatantSpec(
        name=name,
        side="pc",
        attack=attack,
        defence=defence,
        stamina=stamina,
        edge=edge,
        soak=soak,
        hope=hope,
        player=True,
        **kwargs,
    )


NPC_TIERS = {
    "peasant": npc("peasant", 8, 3, 0, 0),
    "soldier": npc("soldier", 10, 4, 1, 1),
    "elite": npc("elite", 12, 5, 1, 1),
    "monster": npc("monster", 14, 6, 2, 1),
    "nemesis": npc("nemesis", 16, 7, 2, 2),
}


def build_scenarios() -> list[Scenario]:
    balanced = pc("balanced", 12, 10, 7, 1, 1, 8)
    balanced_dual = pc("balanced_dual", 12, 12, 7, 1, 1, 8)
    minmax_dual = pc("minmax_dual", 16, 16, 9, 1, 1, 8)
    minmax_split = pc("minmax_split", 16, 6, 9, 1, 1, 8)
    floor8_dual = pc("floor8_dual", 16, 16, 6, 1, 1, 8)
    minmax_tag_base = pc("minmax_tag_base", 16, 16, 9, 1, 1, 6)
    minmax_tagged = replace(
        minmax_tag_base, name="minmax_tagged", tagged_attack=True
    )
    scenarios: list[Scenario] = []

    for tier_name, enemies in NPC_TIERS.items():
        for build_name, hero in (
            ("balanced", balanced),
            ("balanced_dual", balanced_dual),
            ("minmax_dual", minmax_dual),
            ("minmax_split", minmax_split),
        ):
            scenarios.append(
                Scenario(
                    name=f"duel_{build_name}_vs_{tier_name}",
                    pcs=(hero,),
                    npcs=enemies,
                    group="build_vs_tier",
                    note="Core baseline: random side initiative, finite personal Hope, no optional Injury.",
                )
            )
        scenarios.append(
            Scenario(
                name=f"duel_floor8_dual_vs_{tier_name}",
                pcs=(floor8_dual,),
                npcs=enemies,
                group="build_counterfactual",
                note="Counterfactual creation floor 8 yields legal 16/16, STM 6, Hope 8.",
            )
        )
    scenarios.append(
        Scenario(
            name="duel_minmax_tag_base_vs_nemesis_niche",
            pcs=(minmax_tag_base,),
            npcs=NPC_TIERS["nemesis"],
            group="build_vs_tier",
            note="Matched Hope-6 extreme without applying its niche tag.",
        )
    )
    scenarios.append(
        Scenario(
            name="duel_minmax_tagged_vs_nemesis_niche",
            pcs=(minmax_tagged,),
            npcs=NPC_TIERS["nemesis"],
            group="build_vs_tier",
            note="Attack Advantage applies only in the assumed tag niche.",
        )
    )

    mirror_pc = pc("mirror_pc", 10, 10, 4, 1, 1, 0)
    mirror_npc = npc("mirror_npc", 10, 4, 1, 1)
    for initiative in ("pc_first", "npc_first", "random"):
        scenarios.append(
            Scenario(
                name=f"mirror_no_luck_{initiative}",
                pcs=(mirror_pc,),
                npcs=mirror_npc,
                initiative=initiative,
                injury_rule="none",
                luck_policy="none",
                group="initiative",
                note="Identical combatants isolate first-action effects.",
            )
        )

    halvar_base = pc("halvar", 14, 14, 7, 2, 1, 12)
    for stance in ("vanguard", "steady", "watchful"):
        scenarios.append(
            Scenario(
                name=f"halvar_{stance}_vs_elite",
                pcs=(replace(halvar_base, stance=stance),),
                npcs=NPC_TIERS["elite"],
                injury_rule="natural1",
                group="stance_duel",
                note="Win and three-round survival are separate stance objectives.",
            )
        )
    for hope_label, hope in (("hope0", 0), ("hope12", 12)):
        for stance in ("vanguard", "steady", "watchful"):
            scenarios.append(
                Scenario(
                    name=f"halvar_{stance}_vs_monster_{hope_label}",
                    pcs=(replace(halvar_base, stance=stance, hope=hope),),
                    npcs=NPC_TIERS["monster"],
                    injury_rule="natural1",
                    group="stance_threat",
                    note="Harder Twilight stance test against a one-score Monster.",
                )
            )

    tolly = pc(
        "tolly", 14, 14, 5, 0, 0, 12, stance="ranged", ranged=True
    )
    for stance in ("vanguard", "steady", "watchful"):
        scenarios.append(
            Scenario(
                name=f"twilight_pair_halvar_{stance}_vs_two_soldiers",
                pcs=(replace(halvar_base, stance=stance), tolly),
                npcs=npc("soldier", 10, 4, 1, 1, count=2),
                injury_rule="natural1",
                group="twilight_party",
                note="Halvar screens Tolly from melee while alive; fixed focus targeting.",
            )
        )

    party = tuple(pc(f"mirror_pc_{i + 1}", 10, 10, 4, 1, 1, 0) for i in range(3))
    enemies = npc("mirror_npc", 10, 4, 1, 1, count=3)
    for targeting in ("pc_focus", "npc_focus", "focus", "random"):
        scenarios.append(
            Scenario(
                name=f"three_vs_three_{targeting}_targeting",
                pcs=party,
                npcs=enemies,
                targeting=targeting,
                injury_rule="none",
                luck_policy="none",
                group="targeting",
                note="Identical sides isolate target coordination; casualties immediately lose actions.",
            )
        )

    for injury_rule in ("none", "natural1", "gritty"):
        scenarios.append(
            Scenario(
                name=f"balanced_vs_elite_injury_{injury_rule}",
                pcs=(balanced,),
                npcs=NPC_TIERS["elite"],
                injury_rule=injury_rule,
                group="injury",
                note="Gritty adds effective-margin 8+ to the natural-1 trigger.",
            )
        )
    for tier_name in ("elite", "monster", "nemesis"):
        one_score = NPC_TIERS[tier_name][0]
        tier_minus2 = replace(
            one_score,
            name=f"{tier_name}_tier_minus2_defence",
            defence=one_score.defence - 2,
        )
        for build_name, hero in (
            ("balanced", balanced),
            ("balanced_dual", balanced_dual),
            ("minmax_dual", minmax_dual),
        ):
            scenarios.append(
                Scenario(
                    name=f"npc_stats_{build_name}_vs_{tier_name}_defence_minus2",
                    pcs=(hero,),
                    npcs=(tier_minus2,),
                    group="npc_stats",
                    note="NPC attacks at tier but defends at tier minus 2; core baseline uses tier for both.",
                )
            )
    for luck_policy in ("none", "decisive"):
        scenarios.append(
            Scenario(
                name=f"balanced_vs_elite_luck_{luck_policy}",
                pcs=(balanced,),
                npcs=NPC_TIERS["elite"],
                luck_policy=luck_policy,
                group="luck",
                note="Decisive Hope spends at most two to flip an exchange or secure a KO.",
            )
        )
    for build_name, hero in (
        ("balanced_dual", balanced_dual),
        ("minmax_dual", minmax_dual),
    ):
        scenarios.append(
            Scenario(
                name=f"hope_scope_{build_name}_vs_nemesis_own_die",
                pcs=(hero,),
                npcs=NPC_TIERS["nemesis"],
                luck_policy="own_decisive",
                group="luck_scope",
                note="Sensitivity reproduces the narrower own-die-only Hope heuristic.",
            )
        )
    for tier_name in ("monster", "nemesis"):
        for build_name, hero in (
            ("balanced_dual", balanced_dual),
            ("minmax_dual", minmax_dual),
        ):
            for cap in (0, 4, 8):
                scenarios.append(
                    Scenario(
                        name=f"hope_cap{cap}_{build_name}_vs_{tier_name}",
                        pcs=(hero,),
                        npcs=NPC_TIERS[tier_name],
                        luck_policy="decisive",
                        hope_cap=cap,
                        group="hope_cap",
                        note="Matched Hope per-decision cap sensitivity; cap 8 is pool-bounded.",
                    )
                )
    return scenarios


def validation_checks() -> list[str]:
    checks: list[str] = []
    for mode in MODES:
        total = sum(ROLL_PMFS[mode].values())
        assert math.isclose(total, 1.0, abs_tol=1e-12)
        checks.append(f"{mode} PMF sums to 1")
    equal = exact_exchange(10, 10, edge=0, soak=0)
    assert math.isclose(equal["hit_probability"], 145 / 400, abs_tol=1e-12)
    checks.append("equal 10 vs 10 hit probability = 145/400 = 0.3625")
    assert succeeds(0, 1)
    assert not succeeds(20, 20)
    checks.append("natural 1 succeeds even at score 0; natural 20 fails even at score 20")
    boundary = exact_exchange(0, 20, edge=2, soak=0)
    assert math.isclose(boundary["hit_probability"], 1 / 400, abs_tol=1e-12)
    checks.append("score 0 attacker vs score 20 defender wins only on natural 1 vs natural 20 (1/400)")
    assert damage_on_hit(10, 1, edge=1, soak=3) == 4
    checks.append("natural 1 at score 10, edge 1 deals 4 and ignores soak 3")
    assert damage_on_hit(10, 10, edge=0, soak=3) == 1
    checks.append("minimum damage on a non-natural hit is 1")
    assert succeeds(20, 20, natural1=False, natural20=False)
    assert damage_on_hit(10, 1, edge=1, soak=3, natural1=False) == 1
    checks.append("nudging to 1/20 does not manufacture a natural result")
    nudge_pc = Fighter.fresh(pc("nudge_pc", 10, 10, 5, 1, 1, 2))
    nudge_npc = Fighter.fresh(npc("nudge_npc", 10, 5, 1, 1)[0])
    assert min_attack_nudge(
        nudge_pc,
        nudge_npc,
        10,
        10,
        False,
        False,
        False,
        False,
    ) in ((1, 0), (0, 1))
    checks.append("decisive Hope finds a legal one-token flip using either opposed die")
    # Synthetic recovery check for the sampler against the independently
    # enumerated equal-score probability.
    recovery_rng = random.Random(918273)
    recovery_reps = 100_000
    recovery_hits = 0
    for _ in range(recovery_reps):
        if attacker_wins(
            10,
            draw_roll(recovery_rng, MODE_PLAIN),
            10,
            draw_roll(recovery_rng, MODE_PLAIN),
        ):
            recovery_hits += 1
    recovered = recovery_hits / recovery_reps
    expected = 145 / 400
    recovery_se = math.sqrt(expected * (1 - expected) / recovery_reps)
    assert abs(recovered - expected) < 5 * recovery_se
    checks.append(
        f"100,000-action sampler recovers equal-10 exact hit probability "
        f"({recovered:.4f} vs {expected:.4f}; <5 MC SE)"
    )
    # Seed recovery: separate fresh RNGs must reproduce a whole combat exactly.
    scenario = build_scenarios()[0]
    seed = scenario_seed(123, scenario.name)
    assert simulate_once(scenario, random.Random(seed)) == simulate_once(
        scenario, random.Random(seed)
    )
    checks.append("fresh identical scenario seeds reproduce the full combat result")
    return checks


def exact_duel_rows() -> list[dict[str, object]]:
    mirror_pc = pc("mirror_pc", 10, 10, 4, 1, 1, 0)
    mirror_npc = npc("mirror_npc", 10, 4, 1, 1)[0]
    first = exact_duel_win_probability(mirror_pc, mirror_npc, pc_first=True)
    second = exact_duel_win_probability(mirror_pc, mirror_npc, pc_first=False)
    assert math.isclose(first + second, 1.0, abs_tol=1e-12)
    return [
        {
            "section": "exact_duel",
            "group": "coupled_control",
            "scenario": "mirror_no_luck_pc_first_exact",
            "p_pc_win": first,
            "initiative": "pc_first",
            "injury_rule": "none",
            "luck_policy": "none",
        },
        {
            "section": "exact_duel",
            "group": "coupled_control",
            "scenario": "mirror_no_luck_npc_first_exact",
            "p_pc_win": second,
            "initiative": "npc_first",
            "injury_rule": "none",
            "luck_policy": "none",
        },
        {
            "section": "exact_duel",
            "group": "coupled_control",
            "scenario": "mirror_no_luck_random_exact",
            "p_pc_win": (first + second) / 2,
            "initiative": "random",
            "injury_rule": "none",
            "luck_policy": "none",
        },
    ]


def validate_simulated_duel_control(
    simulated: Sequence[dict[str, object]], coupled: Sequence[dict[str, object]]
) -> list[str]:
    checks: list[str] = []
    for initiative in ("pc_first", "npc_first", "random"):
        observed = row_by_name(simulated, f"mirror_no_luck_{initiative}")
        truth = row_by_name(coupled, f"mirror_no_luck_{initiative}_exact")
        p_exact = float(truth["p_pc_win"])
        p_mc = float(observed["p_pc_win"])
        reps = int(observed["reps"])
        se = math.sqrt(p_exact * (1 - p_exact) / reps)
        assert abs(p_mc - p_exact) < 5 * se
        checks.append(
            f"coupled duel MC recovers {initiative} exact win probability "
            f"({p_mc:.4f} vs {p_exact:.4f}; <5 MC SE)"
        )
    return checks


def exact_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cases = [
        ("equal10_plain", 10, 10, 1, 1, MODE_PLAIN, MODE_PLAIN),
        ("equal10_attack_adv", 10, 10, 1, 1, MODE_ADV, MODE_PLAIN),
        ("equal10_defence_adv", 10, 10, 1, 1, MODE_PLAIN, MODE_ADV),
        ("halvar_vanguard_vs_elite", 14, 12, 2, 1, MODE_ADV, MODE_DIS),
        ("halvar_steady_vs_elite", 14, 12, 2, 1, MODE_PLAIN, MODE_PLAIN),
        ("halvar_watchful_vs_elite", 14, 12, 2, 1, MODE_DIS, MODE_ADV),
        ("minmax16_vs_nemesis16", 16, 16, 1, 2, MODE_PLAIN, MODE_PLAIN),
        ("minmax16_tag_vs_nemesis16", 16, 16, 1, 2, MODE_ADV, MODE_PLAIN),
    ]
    for name, att, defence, edge, soak, att_mode, def_mode in cases:
        result = exact_exchange(att, defence, edge, soak, att_mode, def_mode)
        rows.append(
            {
                "section": "exact",
                "group": "exchange",
                "scenario": name,
                "attack": att,
                "defence": defence,
                "edge": edge,
                "soak": soak,
                "attack_mode": att_mode,
                "defence_mode": def_mode,
                **result,
            }
        )
    return rows


def fmt_pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def fmt_ci(row: dict[str, object], key: str, low: str, high: str) -> str:
    return (
        f"{fmt_pct(float(row[key]))} "
        f"[{fmt_pct(float(row[low]))}, {fmt_pct(float(row[high]))}]"
    )


def row_by_name(rows: Iterable[dict[str, object]], name: str) -> dict[str, object]:
    return next(row for row in rows if row.get("scenario") == name)


def render_markdown(
    exact: list[dict[str, object]],
    coupled: list[dict[str, object]],
    simulated: list[dict[str, object]],
    checks: list[str],
    reps: int,
    seed: int,
) -> str:
    lines = [
        "# Independent combat analysis",
        "",
        "Generated by `tools/analysis/independent_combat.py` directly from the published core and Twilight rules.",
        "The implementation is independent of the engine-atlas code.",
        "",
        "## Scientific target and scope",
        "",
        "The estimands are rules-model probabilities: an attack wins an opposed exchange, damage per declared action, a side wins a coupled combat, and PCs remain standing after three rounds. They are not empirical probabilities of enjoyment or historical combat. Scope is human-scale core combat and the optional Twilight positions/Injury module; Fatal harm, morale, terrain, Dread, healing between encounters, NPC hooks, and creative non-damage objectives are outside the numerical model.",
        "",
        "The simulated observation process is complete: every attack and defence roll, casualty, lost action, fixed within-side order, target choice, optional Injury test, and finite Hope spend changes subsequent state. The core's statless side-initiative roll gives either side probability one half after tied rolls are rerolled, so main scenarios sample that equivalent fair side order once per combat; sensitivity cases force each side first. Core build-versus-tier baselines use no optional Injury; Twilight stance/company cases explicitly use natural-1 Injury. PCs use a transparent conservative Hope policy: the default spends at most two personal Hope per decision to flip an opposed result, pass Deflection, or secure an immediate knockout, while the cap sensitivity uses 0, 4, and pool-bounded 8; NPCs have no Luck as written. No Companionship is spent.",
        "",
        f"Monte Carlo results use {reps:,} independent combats per scenario, master seed {seed}; each scenario derives a stable SHA-256 seed so scenario ordering cannot change its random stream. Brackets are 95% Wilson intervals for proportions; reported mean Monte Carlo uncertainty is one standard error.",
        "",
        "## Exact exchange controls",
        "",
        "| Case | Hit | Damage/action | Damage/hit | Nat-1 Injury trigger | Gritty trigger |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in exact:
        lines.append(
            "| {scenario} | {hit} | {dpa:.3f} | {dph:.3f} | {nat} | {gritty} |".format(
                scenario=row["scenario"],
                hit=fmt_pct(float(row["hit_probability"])),
                dpa=float(row["expected_damage_per_action"]),
                dph=float(row["expected_damage_given_hit"]),
                nat=fmt_pct(float(row["injury_trigger_nat1_per_action"])),
                gritty=fmt_pct(float(row["injury_trigger_gritty_per_action"])),
            )
        )

    lines += [
        "",
        "The exact calculation enumerates the kept-face PMFs, including all 160,000 raw 2d20-by-2d20 combinations when both sides have Advantage/Disadvantage. A damage-zero mass represents misses. Luck is excluded from this table because it is a path-dependent finite resource in combat.",
        "",
        "Natural results apply to the final kept die: a kept natural 1 succeeds regardless of score and a kept natural 20 fails regardless of score. Nudges cannot alter a raw natural 1/20, and the model never nudges another result into a natural 1.",
        "",
        "## NPC baseline specification",
        "",
        "| Tier | Attack | Defence | Stamina | Edge | Soak |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for tier_name, enemies in NPC_TIERS.items():
        foe = enemies[0]
        lines.append(
            f"| {tier_name.title()} | {foe.attack} | {foe.defence} | {foe.stamina} | {foe.edge} | {foe.soak} |"
        )
    lines += [
        "",
        "These are the Almanac's one-score NPCs: tier governs both main attacks and defence. The sensitivity below keeps attack at tier but moves defence to tier minus 2, matching the strong/weak-pair guidance for an unexceptional secondary attribute.",
        "",
        "## Six-build-point allocation stress test",
        "",
        "The legal extreme uses attributes `[16, 6, 6, 6, 8]`, Stamina 9, and the six starting build points: +10 total above baseline costs 20 ledger units; the four reduced attributes supply 14 and the build points supply 6. The dual-use case permits the 16 to govern both a forceful attack and a parry when the fiction supports it. The split-role case forces defence onto a score of 6. The balanced build is reported both as split attack 12/defence 10 and as dual-use 12/12, with Stamina 7 and Hope 8 in both cases. All carry edge 1 and soak 1 so the comparison isolates allocation rather than gear. A tag-bearing extreme is modelled separately because buying the tag makes Hope 6, not 8.",
        "",
        "| Opponent | Balanced split 12/10 | Balanced dual 12/12 | Extreme dual 16/16 | Extreme split 16/6 | Floor-8 16/16 STM 6 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for tier in NPC_TIERS:
        balanced = row_by_name(simulated, f"duel_balanced_vs_{tier}")
        balanced_dual = row_by_name(simulated, f"duel_balanced_dual_vs_{tier}")
        dual = row_by_name(simulated, f"duel_minmax_dual_vs_{tier}")
        split = row_by_name(simulated, f"duel_minmax_split_vs_{tier}")
        floor8 = row_by_name(simulated, f"duel_floor8_dual_vs_{tier}")
        lines.append(
            f"| {tier.title()} | {fmt_ci(balanced, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(balanced_dual, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(dual, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(split, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(floor8, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} |"
        )
    tagged = row_by_name(simulated, "duel_minmax_tagged_vs_nemesis_niche")
    tag_base = row_by_name(simulated, "duel_minmax_tag_base_vs_nemesis_niche")
    lines += [
        "",
        "The floor-8 alternative is a deliberately small creation-rule counterfactual: keeping every attribute at 8+, or equivalently granting no trade-off refund below 8, makes `[16, 8, 8, 8, 8]`, Stamina 6 exactly legal with six build points. It preserves a score-16 signature and the same combat procedure while removing the simultaneous Stamina-9 extreme. This is evidence for discussion, not an adopted fix.",
        "",
        f"For the separate legal tag extreme `[16, 6, 6, 6, 6]`, Stamina 9, Hope 6, a niche-fitting attack tag raises its matched Nemesis duel from {fmt_pct(float(tag_base['p_pc_win']))} to {fmt_pct(float(tagged['p_pc_win']))}. This is a conditional ceiling, not a universal-tag assumption.",
        "",
        "## Initiative, targeting, and coupled casualties",
        "",
    ]
    pc_first = row_by_name(simulated, "mirror_no_luck_pc_first")
    npc_first = row_by_name(simulated, "mirror_no_luck_npc_first")
    random_first = row_by_name(simulated, "mirror_no_luck_random")
    pc_first_exact = row_by_name(coupled, "mirror_no_luck_pc_first_exact")
    npc_first_exact = row_by_name(coupled, "mirror_no_luck_npc_first_exact")
    random_exact = row_by_name(coupled, "mirror_no_luck_random_exact")
    pc_focus = row_by_name(simulated, "three_vs_three_pc_focus_targeting")
    npc_focus = row_by_name(simulated, "three_vs_three_npc_focus_targeting")
    both_focus = row_by_name(simulated, "three_vs_three_focus_targeting")
    both_random = row_by_name(simulated, "three_vs_three_random_targeting")
    lines += [
        f"For identical score-10, Stamina-4 fighters with no Luck or Injury, exact coupled recursion gives PC win {fmt_pct(float(pc_first_exact['p_pc_win']))} acting first, {fmt_pct(float(npc_first_exact['p_pc_win']))} acting second, and {fmt_pct(float(random_exact['p_pc_win']))} under a fair initiative coin. Monte Carlo recovers {fmt_pct(float(pc_first['p_pc_win']))}, {fmt_pct(float(npc_first['p_pc_win']))}, and {fmt_ci(random_first, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')}, respectively. The exact recursion removes double-miss self-loops and propagates every casualty and lost action; it is not a time-to-defeat ratio.",
        "",
        f"With otherwise identical three-person sides, PCs win {fmt_ci(pc_focus, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} when only they focus fire and {fmt_ci(npc_focus, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} when only NPCs focus. When both sides focus the estimate is {fmt_ci(both_focus, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')}; when both spread randomly it is {fmt_ci(both_random, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')}. Target coordination is therefore part of the estimand, not harmless simulation detail.",
        "",
        "## NPC score sensitivity",
        "",
        "| PC build and opponent | One-score NPC | Defence at tier - 2 | Change |",
        "|---|---:|---:|---:|",
    ]
    for tier in ("elite", "monster", "nemesis"):
        for build in ("balanced", "balanced_dual", "minmax_dual"):
            baseline = row_by_name(simulated, f"duel_{build}_vs_{tier}")
            alternate = row_by_name(
                simulated, f"npc_stats_{build}_vs_{tier}_defence_minus2"
            )
            delta_pp = 100 * (
                float(alternate["p_pc_win"]) - float(baseline["p_pc_win"])
            )
            lines.append(
                f"| {build.replace('_', ' ').title()} vs {tier.title()} | "
                f"{fmt_ci(baseline, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
                f"{fmt_ci(alternate, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
                f"{delta_pp:+.1f} pp |"
            )
    lines += [
        "",
        "The one-score version is the reported baseline, not an invisible default. Encounter claims should identify which NPC construction is used because a two-point defensive texture changes PC win probability while leaving NPC attacks unchanged.",
        "",
        "## Twilight positions and objectives",
        "",
        "| Scenario | Win | Standing after 3 rounds | Mean Stamina lost (SE) | Mean rounds (SE) |",
        "|---|---:|---:|---:|---:|",
    ]
    for stance in ("vanguard", "steady", "watchful"):
        row = row_by_name(simulated, f"halvar_{stance}_vs_elite")
        lines.append(
            f"| Halvar {stance} vs Elite | {fmt_ci(row, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(row, 'p_hold_survival', 'p_hold_ci_low', 'p_hold_ci_high')} | "
            f"{float(row['mean_pc_stamina_lost']):.2f} ({float(row['se_pc_stamina_lost']):.02f}) | "
            f"{float(row['mean_rounds']):.2f} ({float(row['se_rounds']):.02f}) |"
        )
    lines += [
        "",
        "| Harder stance test: Halvar vs Monster | Win | Standing after 3 rounds | Mean Stamina lost (SE) |",
        "|---|---:|---:|---:|",
    ]
    for hope_label, hope in (("hope0", 0), ("hope12", 12)):
        for stance in ("vanguard", "steady", "watchful"):
            row = row_by_name(
                simulated, f"halvar_{stance}_vs_monster_{hope_label}"
            )
            lines.append(
                f"| {stance.title()}, Hope {hope} | "
                f"{fmt_ci(row, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
                f"{fmt_ci(row, 'p_hold_survival', 'p_hold_ci_low', 'p_hold_ci_high')} | "
                f"{float(row['mean_pc_stamina_lost']):.2f} ({float(row['se_pc_stamina_lost']):.02f}) |"
            )
    lines += [
        "",
        "| Twilight sample company | Win | At least one PC standing after 3 rounds | Mean PC survivors (SE) |",
        "|---|---:|---:|---:|",
    ]
    for stance in ("vanguard", "steady", "watchful"):
        row = row_by_name(
            simulated, f"twilight_pair_halvar_{stance}_vs_two_soldiers"
        )
        lines.append(
            f"| Halvar {stance}; Tolly screened/ranged | {fmt_ci(row, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{fmt_ci(row, 'p_hold_survival', 'p_hold_ci_low', 'p_hold_ci_high')} | "
            f"{float(row['mean_pc_survivors']):.2f} ({float(row['se_pc_survivors']):.02f}) |"
        )
    lines += [
        "",
        "Positions express different objectives: win probability, short-horizon survival, and company attrition need not rank them identically. Ranged has a real positional prerequisite in this model: melee foes must clear the living front line before engaging Tolly. This should not be interpreted as free Advantage in a duel or after the screen falls.",
        "",
        "## Injury and Hope sensitivity",
        "",
        "| Variant, balanced vs Elite | Win | Mean injured PCs | Mean injured NPCs | Mean Hope spent |",
        "|---|---:|---:|---:|---:|",
    ]
    for injury_rule in ("none", "natural1", "gritty"):
        row = row_by_name(simulated, f"balanced_vs_elite_injury_{injury_rule}")
        lines.append(
            f"| Injury: {injury_rule} | {fmt_ci(row, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{float(row['mean_pc_injured']):.3f} | {float(row['mean_npc_injured']):.3f} | "
            f"{float(row['mean_pc_luck_spent']):.2f} |"
        )
    for policy in ("none", "decisive"):
        row = row_by_name(simulated, f"balanced_vs_elite_luck_{policy}")
        lines.append(
            f"| Hope policy: {policy} | {fmt_ci(row, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
            f"{float(row['mean_pc_injured']):.3f} | {float(row['mean_npc_injured']):.3f} | "
            f"{float(row['mean_pc_luck_spent']):.2f} |"
        )

    legal_balanced_scope = row_by_name(simulated, "duel_balanced_dual_vs_nemesis")
    legal_extreme_scope = row_by_name(simulated, "duel_minmax_dual_vs_nemesis")
    own_balanced_scope = row_by_name(
        simulated, "hope_scope_balanced_dual_vs_nemesis_own_die"
    )
    own_extreme_scope = row_by_name(
        simulated, "hope_scope_minmax_dual_vs_nemesis_own_die"
    )
    legal_scope_gap = float(legal_extreme_scope["p_pc_win"]) - float(
        legal_balanced_scope["p_pc_win"]
    )
    own_scope_gap = float(own_extreme_scope["p_pc_win"]) - float(
        own_balanced_scope["p_pc_win"]
    )
    lines += [
        "",
        "| Hope scope, versus Nemesis | Balanced dual 12/12 | Extreme dual 16/16 | Extreme-minus-balanced gap |",
        "|---|---:|---:|---:|",
        f"| Legal either-die policy | {fmt_ci(legal_balanced_scope, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | {fmt_ci(legal_extreme_scope, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | {100 * legal_scope_gap:+.1f} pp |",
        f"| Own-die-only sensitivity | {fmt_ci(own_balanced_scope, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | {fmt_ci(own_extreme_scope, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | {100 * own_scope_gap:+.1f} pp |",
        "",
        "The full legal policy can nudge either opposed die. The own-die row is retained to show how a legal but restricted own-die heuristic changes the build contrast.",
        "",
        "| Opponent and per-decision Hope cap | Balanced dual 12/12 | Extreme dual 16/16 | Gap |",
        "|---|---:|---:|---:|",
    ]
    for tier in ("monster", "nemesis"):
        for cap in (0, 2, 4, 8):
            if cap == 2:
                balanced_cap = row_by_name(simulated, f"duel_balanced_dual_vs_{tier}")
                extreme_cap = row_by_name(simulated, f"duel_minmax_dual_vs_{tier}")
            else:
                balanced_cap = row_by_name(
                    simulated, f"hope_cap{cap}_balanced_dual_vs_{tier}"
                )
                extreme_cap = row_by_name(
                    simulated, f"hope_cap{cap}_minmax_dual_vs_{tier}"
                )
            cap_gap = float(extreme_cap["p_pc_win"]) - float(
                balanced_cap["p_pc_win"]
            )
            lines.append(
                f"| {tier.title()}, cap {cap} | "
                f"{fmt_ci(balanced_cap, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
                f"{fmt_ci(extreme_cap, 'p_pc_win', 'p_pc_win_ci_low', 'p_pc_win_ci_high')} | "
                f"{100 * cap_gap:+.1f} pp |"
            )
    lines += [
        "",
        "Cap 8 is effectively pool-bounded for these Hope-8 builds. The cap changes both absolute outcomes and the build gap, so the cap-2 headline estimates allocation under one explicit resource policy; they are not a ledger-only effect.",
    ]

    natural = row_by_name(simulated, "balanced_vs_elite_injury_natural1")
    gritty = row_by_name(simulated, "balanced_vs_elite_injury_gritty")
    balanced_nemesis = row_by_name(simulated, "duel_balanced_vs_nemesis")
    balanced_dual_nemesis = row_by_name(
        simulated, "duel_balanced_dual_vs_nemesis"
    )
    dual_nemesis = row_by_name(simulated, "duel_minmax_dual_vs_nemesis")
    split_nemesis = row_by_name(simulated, "duel_minmax_split_vs_nemesis")
    floor8_nemesis = row_by_name(simulated, "duel_floor8_dual_vs_nemesis")
    whole_extreme_gap = float(dual_nemesis["p_pc_win"]) - float(
        balanced_dual_nemesis["p_pc_win"]
    )
    balanced_reuse_gap = float(balanced_dual_nemesis["p_pc_win"]) - float(
        balanced_nemesis["p_pc_win"]
    )
    reuse_gap = float(dual_nemesis["p_pc_win"]) - float(
        split_nemesis["p_pc_win"]
    )
    stamina_gap = float(dual_nemesis["p_pc_win"]) - float(
        floor8_nemesis["p_pc_win"]
    )
    gritty_gap = float(gritty["p_pc_win"]) - float(natural["p_pc_win"])
    lines += [
        "",
        "## Decisive findings and recommendation",
        "",
        f"1. **The creation ledger is a major tested balance pressure whose effect interacts with Hope policy.** Under the cap-2 heuristic against a Nemesis, the full 16/16, Stamina-9 extreme gains {100 * whole_extreme_gap:+.1f} percentage points of win probability over the matched dual-use balanced 12/12 build under identical gear. Allowing score reuse adds {100 * balanced_reuse_gap:+.1f} points for the balanced build and {100 * reuse_gap:+.1f} points for the extreme relative to their split controls; retaining extreme dual use but reducing Stamina 9 to 6 under the floor-8/refund-cap-8 alternative removes {100 * stamina_gap:.1f} points. The cap-sensitivity table is the correct evidence for other resource policies; the cap-2 gap is not a ledger-only effect.",
        "2. **Initiative and focus fire materially alter outcomes.** The model implements the core's fair statless side initiative and separately forces each side first to quantify its effect. Encounter guidance and future analyses should also state target selection and report coupled win/survival probabilities. Expected damage or rounds alone cannot support encounter-balance claims.",
        "3. **Twilight stances are objective-dependent rather than one scalar ladder.** Treat Watchful as a hold/survival choice, Vanguard as an aggression choice, and Ranged as a formation benefit with a screen. The present experiment does not justify changing the stance text if those trade-offs appear in the table above; a numerical fix would erase intended fictional distinctions.",
        f"4. **The grittier Injury trigger is a consequential lethality dial.** Its balanced-vs-Elite win shift relative to natural-1-only is {100 * gritty_gap:+.1f} percentage points, with a larger change in injury incidence shown above. Keep effective-margin 8+ explicitly optional and do not mix its results with the core no-Injury baseline or natural-1 Twilight module.",
        "5. **Recommended minimal rule clarification:** require the declared defence attribute to follow the fiction and warn that repeatedly using one signature score for both attack and defence creates a large combat premium. If playtest intent is that a forceful parry is usually available, retain the rule and price encounters for it; if diverse defence modes are intended, state when a foe or attack forces dodge, cover, or resolve. The floor-8 counterfactual curbs the Stamina-9 component but leaves a strong score-16 advantage, so it is a partial fallback rather than a complete balance fix.",
        "",
        "No Twilight stance counterfactual is recommended from these data unless one stance dominates both win and survival objectives beyond Monte Carlo uncertainty. The baseline comparisons are therefore preserved without tuning. The more serious open design question is whether broad reuse of a score of 16 is intended; a future fix should be tested against the dual-use and split-role controls here.",
        "",
        "## Validation and residual risks",
        "",
    ]
    lines.extend(f"- {check}." for check in checks)
    lines += [
        "- Exact results test only an isolated action; simulation uncertainty brackets cover Monte Carlo error but not uncertainty about player tactics, encounter fiction, morale, or rule interpretation.",
        "- The Hope policy is deliberately finite and reproducible, but it is a stated heuristic rather than an optimal policy. For each flip it searches the cheapest legal split between improving the PC die and worsening the NPC die, never manufactures a natural 1/20, and avoids the unspecified two-sided counter-spending game. A player who spends more than two tokens or values later Hope tests differently can obtain different results.",
        "- Advantage and Disadvantage are treated as non-stacking and cancel when both apply. The core explains each state but does not explicitly state stacking/cancellation.",
        "- Sampling a fair side-order coin is distributionally identical to the core's one-d20-per-side initiative with tied rolls rerolled. Within-side order remains fixed in the model and can advantage the first listed actor; scenario order is held constant for comparison.",
        "- Twilight stances are held fixed for each simulated combat. Adaptive round-by-round stance choice, Companionship, morale or retreat, terrain, NPC hooks, and between-encounter attrition can change the objective trade-offs.",
        "- Exact coupled recursion validates the no-Hope/no-Injury duel only. Finite-Hope results use the stated heuristic rather than an exact dynamic programme over resource value.",
        "- `combat_results.csv` contains all exact distributions and scenario estimates for reanalysis.",
        "",
        "**Audit recommendation:** a Sol Max audit is justified before changing the creation economy or restricting attribute reuse, because that choice affects the core game's character concept freedom and every skin. It is not needed merely to retain the current Twilight stance table or natural-1 Injury default.",
        "",
    ]
    return "\n".join(lines)


def write_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260920)
    parser.add_argument(
        "--outdir", type=Path, default=Path("docs/independent_engine")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.reps < 100:
        raise SystemExit("--reps must be at least 100")
    checks = validation_checks()
    exact = exact_rows()
    coupled = exact_duel_rows()
    simulated = [
        run_scenario(scenario, args.reps, args.seed) for scenario in build_scenarios()
    ]
    checks.extend(validate_simulated_duel_control(simulated, coupled))
    args.outdir.mkdir(parents=True, exist_ok=True)
    write_csv(args.outdir / "combat_results.csv", [*exact, *coupled, *simulated])
    markdown = render_markdown(exact, coupled, simulated, checks, args.reps, args.seed)
    (args.outdir / "combat_analysis.md").write_text(markdown, encoding="utf-8")
    print(
        f"wrote {len(exact)} exact exchanges, {len(coupled)} exact duels, "
        f"and {len(simulated)} simulated scenarios "
        f"to {args.outdir}"
    )


if __name__ == "__main__":
    main()
