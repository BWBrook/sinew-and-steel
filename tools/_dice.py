"""Random d20 draws around the pure mechanics in :mod:`_rules`."""
from __future__ import annotations

import random
from typing import Any

from _rules import apply_nudge_to_check, cancel_sources, damage_from_check, resolve_check_from_rolls, resolve_opposed_outcome


def roll_d20() -> int:
    return random.randint(1, 20)


def resolve_check(stat: int, adv: bool = False, dis: bool = False) -> dict[str, Any]:
    # Keep draw order stable for seeded callers and patched roll_d20 tests.
    adv, dis = cancel_sources(adv, dis)
    rolls = [roll_d20()]
    if adv or dis:
        rolls.append(roll_d20())
    return resolve_check_from_rolls(stat, rolls, adv, dis)


def resolve_opposed(
    attacker: int, defender: int, *,
    adv_attacker: bool = False, dis_attacker: bool = False,
    adv_defender: bool = False, dis_defender: bool = False,
) -> dict[str, Any]:
    attacker_roll = resolve_check(attacker, adv=adv_attacker, dis=dis_attacker)
    defender_roll = resolve_check(defender, adv=adv_defender, dis=dis_defender)
    return {
        "attacker": attacker_roll, "defender": defender_roll,
        "outcome": resolve_opposed_outcome(attacker_roll, defender_roll),
    }
