from __future__ import annotations

import random
from typing import Any


def roll_d20() -> int:
    return random.randint(1, 20)


def resolve_check(stat: int, adv: bool = False, dis: bool = False) -> dict[str, Any]:
    rolls = [roll_d20()]
    if adv or dis:
        rolls.append(roll_d20())

    if adv:
        chosen = min(rolls)
    elif dis:
        chosen = max(rolls)
    else:
        chosen = rolls[0]

    success = chosen <= stat
    margin = stat - chosen
    crit = None
    if chosen == 1:
        crit = "nat1"
    elif chosen == 20:
        crit = "nat20"

    return {
        "stat": stat,
        "rolls": rolls,
        "result": chosen,
        "success": success,
        "margin": margin,
        "crit": crit,
        "adv": bool(adv),
        "dis": bool(dis),
    }


def resolve_opposed(
    attacker: int,
    defender: int,
    *,
    adv_attacker: bool = False,
    dis_attacker: bool = False,
    adv_defender: bool = False,
    dis_defender: bool = False,
) -> dict[str, Any]:
    attacker_roll = resolve_check(attacker, adv=adv_attacker, dis=dis_attacker)
    defender_roll = resolve_check(defender, adv=adv_defender, dis=dis_defender)

    outcome = {
        "winner": None,
        "reason": None,
    }

    if attacker_roll["success"] and not defender_roll["success"]:
        outcome["winner"] = "attacker"
        outcome["reason"] = "attacker_success_only"
    elif defender_roll["success"] and not attacker_roll["success"]:
        outcome["winner"] = "defender"
        outcome["reason"] = "defender_success_only"
    elif attacker_roll["success"] and defender_roll["success"]:
        if attacker_roll["margin"] > defender_roll["margin"]:
            outcome["winner"] = "attacker"
            outcome["reason"] = "higher_margin"
        elif defender_roll["margin"] > attacker_roll["margin"]:
            outcome["winner"] = "defender"
            outcome["reason"] = "higher_margin"
        else:
            outcome["winner"] = "defender"
            outcome["reason"] = "tie_margins_defender"
    else:
        outcome["winner"] = "defender"
        outcome["reason"] = "both_failed_defender"

    return {
        "attacker": attacker_roll,
        "defender": defender_roll,
        "outcome": outcome,
    }


def apply_nudge_to_check(check: dict[str, Any], nudge: int) -> dict[str, Any]:
    if not nudge:
        return {**check, "nudge": 0, "final_result": check.get("result"), "final_success": check.get("success")}

    result = check.get("result")
    stat = check.get("stat")
    if result in (1, 20):
        raise ValueError("cannot nudge a natural 1 or 20")

    if not isinstance(result, int) or not isinstance(stat, int):
        raise ValueError("invalid check data")

    final_result = result + nudge
    if final_result < 1:
        final_result = 1
    if final_result > 20:
        final_result = 20

    final_success = final_result <= stat
    final_margin = stat - final_result

    return {
        **check,
        "nudge": nudge,
        "final_result": final_result,
        "final_success": final_success,
        "final_margin": final_margin,
    }
