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

    return {
        "attacker": attacker_roll,
        "defender": defender_roll,
        "outcome": resolve_opposed_outcome(attacker_roll, defender_roll),
    }


def resolve_opposed_outcome(attacker_roll: dict[str, Any], defender_roll: dict[str, Any]) -> dict[str, str]:
    """Resolve an opposed result from two already-finalised checks."""
    attacker_success = bool(attacker_roll.get("success", attacker_roll.get("final_success")))
    defender_success = bool(defender_roll.get("success", defender_roll.get("final_success")))
    attacker_margin = int(attacker_roll.get("margin", attacker_roll.get("final_margin", 0)))
    defender_margin = int(defender_roll.get("margin", defender_roll.get("final_margin", 0)))

    if attacker_success and not defender_success:
        return {"winner": "attacker", "reason": "attacker_success_only"}
    if defender_success and not attacker_success:
        return {"winner": "defender", "reason": "defender_success_only"}
    if attacker_success and defender_success:
        if attacker_margin > defender_margin:
            return {"winner": "attacker", "reason": "higher_margin"}
        if defender_margin > attacker_margin:
            return {"winner": "defender", "reason": "higher_margin"}
        return {"winner": "defender", "reason": "tie_margins_defender"}
    return {"winner": "defender", "reason": "both_failed_defender"}


def apply_nudge_to_check(check: dict[str, Any], nudge: int) -> dict[str, Any]:
    raw_result = check.get("result")
    raw_success = check.get("success")
    raw_margin = check.get("margin")
    raw_crit = check.get("crit")

    if not nudge:
        return {
            **check,
            "nudge": 0,
            "raw_result": raw_result,
            "raw_success": raw_success,
            "raw_margin": raw_margin,
            "raw_crit": raw_crit,
            "final_result": raw_result,
            "final_success": raw_success,
            "final_margin": raw_margin,
            "result": raw_result,
            "success": raw_success,
            "margin": raw_margin,
        }

    stat = check.get("stat")
    if raw_result in (1, 20):
        raise ValueError("cannot nudge a natural 1 or 20")

    if not isinstance(raw_result, int) or not isinstance(stat, int):
        raise ValueError("invalid check data")

    final_result = raw_result + nudge
    if final_result < 1:
        final_result = 1
    if final_result > 20:
        final_result = 20

    final_success = final_result <= stat
    final_margin = stat - final_result

    return {
        **check,
        "nudge": nudge,
        "raw_result": raw_result,
        "raw_success": raw_success,
        "raw_margin": raw_margin,
        "raw_crit": raw_crit,
        "final_result": final_result,
        "final_success": final_success,
        "final_margin": final_margin,
        "result": final_result,
        "success": final_success,
        "margin": final_margin,
    }
