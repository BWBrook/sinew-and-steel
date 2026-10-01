"""Pure Sinew & Steel mechanics shared by tools and validators.

No randomness, file access, or campaign state belongs here. Ceilings apply at
creation and throughout advancement (Manual sections 2.1 and 8).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

ATTRIBUTE_BASELINE = 10
STAMINA_BASELINE = 5
ATTRIBUTE_MIN = 6
ATTRIBUTE_MAX = 16
STAMINA_MIN = 3
STAMINA_MAX = 9
REFUND_CAP = 8
TAG_COST = 2
MILESTONE_POINTS = 2
TONE_BUDGETS = {"grim": 0, "standard": 6, "pulp": 12, "heroic": 16}


def integer(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    return value


def validate_scores(attributes: Mapping[str, int], stamina: int) -> None:
    if len(attributes) != 5:
        raise ValueError("characters require exactly five attributes")
    for key, value in attributes.items():
        integer(value, f"attribute {key}")
        if not ATTRIBUTE_MIN <= value <= ATTRIBUTE_MAX:
            raise ValueError(f"attribute {key} out of range ({ATTRIBUTE_MIN}-{ATTRIBUTE_MAX}): {value}")
    integer(stamina, "Stamina")
    if not STAMINA_MIN <= stamina <= STAMINA_MAX:
        raise ValueError(f"Stamina out of range ({STAMINA_MIN}-{STAMINA_MAX}): {stamina}")


def validate_double_debit_mixed(
    values: Mapping[str, Any], baselines: Mapping[str, int]
) -> tuple[int, int, int, int]:
    increases = decreases = 0
    for key, value in values.items():
        if key not in baselines:
            raise KeyError(f"missing baseline for '{key}'")
        baseline = integer(baselines[key], f"baseline {key}")
        integer(value, f"score {key}")
        increases += max(0, value - baseline)
        decreases += max(0, baseline - value)
    required = 2 * increases
    return increases, decreases, required, decreases - required


def build_points_needed_mixed(
    values: Mapping[str, Any], baselines: Mapping[str, int]
) -> tuple[int, int, int, int, int]:
    """Creation refunds pay only for raises, up to eight points total."""
    increases, decreases, required, slack = validate_double_debit_mixed(values, baselines)
    return max(0, required - min(decreases, REFUND_CAP)), increases, decreases, required, slack


def tag_cost(bought_tags: Sequence[Any] | None) -> int:
    """The caller must exclude free skin grants."""
    return TAG_COST * len(bought_tags or [])


def creation_price(attributes: Mapping[str, int], stamina: int, bought_tags: Sequence[str] = ()) -> int:
    values = {**attributes, "STM": stamina}
    baselines = {**{key: ATTRIBUTE_BASELINE for key in attributes}, "STM": STAMINA_BASELINE}
    needed, *_ = build_points_needed_mixed(values, baselines)
    # Clamp score spending before tags: spare refunds cannot purchase a tag.
    return needed + tag_cost(bought_tags)


def raise_cost(current: int, *, stamina: bool = False) -> int:
    """Price the next +1 from its actual starting score, without repricing creation."""
    integer(current, "current score")
    baseline = STAMINA_BASELINE if stamina else ATTRIBUTE_BASELINE
    low, high = (STAMINA_MIN, STAMINA_MAX) if stamina else (ATTRIBUTE_MIN, ATTRIBUTE_MAX)
    if not low <= current < high:
        raise ValueError(f"cannot raise score {current}; legal range is {low}-{high}")
    return 1 if current < baseline else 2


def cancel_sources(adv: bool = False, dis: bool = False) -> tuple[bool, bool]:
    return bool(adv and not dis), bool(dis and not adv)


def resolve_check_from_rolls(
    stat: int, rolls: Iterable[int], adv: bool = False, dis: bool = False
) -> dict[str, Any]:
    integer(stat, "target")  # Luck may be zero; NPCs may exceed the PC ceiling.
    adv, dis = cancel_sources(adv, dis)
    faces = list(rolls)
    expected = 2 if adv or dis else 1
    if len(faces) != expected:
        raise ValueError(f"expected {expected} d20 face(s) after Advantage/Disadvantage cancellation")
    for face in faces:
        integer(face, "d20 face")
        if not 1 <= face <= 20:
            raise ValueError("d20 faces must be between 1 and 20")
    chosen = min(faces) if adv else max(faces) if dis else faces[0]
    return {
        "stat": stat, "rolls": faces, "result": chosen,
        "success": chosen == 1 or (chosen != 20 and chosen <= stat),
        "margin": stat - chosen,
        "crit": "nat1" if chosen == 1 else "nat20" if chosen == 20 else None,
        "adv": adv, "dis": dis,
    }


def resolve_opposed_outcome(
    attacker_roll: Mapping[str, Any], defender_roll: Mapping[str, Any]
) -> dict[str, str]:
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


def apply_nudge_to_check(check: Mapping[str, Any], nudge: int) -> dict[str, Any]:
    """Adjust the kept die, retaining original natural status and target."""
    integer(nudge, "nudge")
    raw_result = check.get("raw_result", check.get("result"))
    raw_success = check.get("raw_success", check.get("success"))
    raw_margin = check.get("raw_margin", check.get("margin"))
    raw_crit = check.get("raw_crit", check.get("crit"))
    stat = integer(check.get("stat"), "target")
    current_result = integer(check.get("result"), "die result")
    integer(raw_result, "raw die result")
    if nudge and raw_result in (1, 20):
        raise ValueError("cannot nudge a natural 1 or 20")
    final_result = current_result + nudge
    if not 1 <= final_result <= 20:
        raise ValueError("nudge must leave the die result between 1 and 20")
    final_success = bool(raw_success) if raw_result in (1, 20) else final_result <= stat
    return {
        **check,
        "nudge": integer(check.get("nudge", 0), "previous nudge") + nudge,
        "raw_result": raw_result, "raw_success": raw_success,
        "raw_margin": raw_margin, "raw_crit": raw_crit,
        "final_result": final_result, "final_success": final_success,
        "final_margin": stat - final_result,
        "result": final_result, "success": final_success,
        "margin": stat - final_result, "crit": raw_crit,
    }


def damage_from_check(check: Mapping[str, Any], edge: int = 0, soak: int = 0) -> int:
    """Damage for a winning attack. Call only after resolving any opposition."""
    integer(edge, "weapon edge")
    integer(soak, "soak")
    if soak < 0:
        raise ValueError("soak must be nonnegative")
    if not check.get("success", check.get("final_success")):
        return 0
    margin = integer(check.get("margin", check.get("final_margin")), "margin")
    natural_one = check.get("raw_crit", check.get("crit")) == "nat1"
    return max(1, 1 + edge + max(0, margin) // 5 + int(natural_one) - (0 if natural_one else soak))
