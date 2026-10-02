"""Canonical sheets and an auditable, replayable advancement ledger."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import _rules

SHEET_SCHEMA_VERSION = 2


def _tags(value: Any, label: str = "tags") -> list[str]:
    if not isinstance(value, list) or any(not isinstance(t, str) or not t.strip() for t in value):
        raise ValueError(f"{label} must be a list of nonempty strings")
    if len({t.strip().casefold() for t in value}) != len(value):
        raise ValueError(f"{label} contains duplicate tags")
    return list(value)


def parse_free_tag(value: str) -> dict[str, str]:
    if "=" not in value:
        raise ValueError("free tags use GRANT=NAME, for example knack=Night Eyes")
    grant, name = (part.strip() for part in value.split("=", 1))
    if not grant or not name:
        raise ValueError("free tags require a grant type and a name")
    return {"name": name, "grant": grant.lower()}


def validate_free_tags(free_tags: Any, skin: dict[str, Any]) -> list[dict[str, str]]:
    if not isinstance(free_tags, list):
        raise ValueError("creation free_tags must be a list")
    allowances = skin.get("creation_free_tags", {})
    used: dict[str, int] = {}
    result = []
    for entry in free_tags:
        if not isinstance(entry, dict) or set(entry) != {"name", "grant"}:
            raise ValueError("each free tag requires exactly name and grant")
        name, grant = entry["name"], entry["grant"]
        if not isinstance(name, str) or not name.strip() or not isinstance(grant, str):
            raise ValueError("free tag name and grant must be nonempty strings")
        allowance = allowances.get(grant, 0)
        used[grant] = used.get(grant, 0) + 1
        if used[grant] > allowance:
            raise ValueError(f"skin grants only {allowance} free {grant} tag(s) at creation")
        result.append({"name": name, "grant": grant})
    _tags([entry["name"] for entry in result], "free tags")
    return result


def build_sheet(
    *, skin_slug: str, skin: dict[str, Any], name: str, player: str = "",
    attributes: dict[str, int], stamina: int, build_points_budget: int,
    build_points_used: int, tags: list[str] | None = None,
    free_tags: list[dict[str, str]] | None = None,
    notes: list[str] | None = None, generated: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical shape; validate_sheet checks budget and provenance."""
    if len(attributes) != 5 or set(attributes) != set(skin.get("attributes", {})):
        raise ValueError("skin attributes missing or incomplete")
    luck_key = skin.get("luck_key")
    if luck_key not in attributes:
        raise ValueError("luck_key not found in attributes")
    bought_tags = _tags(tags if tags is not None else [], "bought tags")
    grants = validate_free_tags(list(free_tags or []), skin)
    all_tags = _tags(bought_tags + [entry["name"] for entry in grants])
    sheet: dict[str, Any] = {
        "schema_version": SHEET_SCHEMA_VERSION,
        "name": name, "skin": skin_slug, "player": player,
        "created": date.today().isoformat(),
        "creation": {
            "build_points_budget": build_points_budget,
            "build_points_used": build_points_used,
            "snapshot": {
                "attributes": dict(attributes), "stamina": stamina,
                "bought_tags": bought_tags, "free_tags": grants,
            },
        },
        "advancement": {"entries": []},
        "attributes": dict(attributes),
        "pools": {
            "luck": {"name": skin.get("luck_name", luck_key),
                     "current": attributes[luck_key], "max": attributes[luck_key]},
            "stamina": {"current": stamina, "max": stamina},
        },
        "inventory": {"big_items": [], "small_items": []},
        "tags": all_tags, "notes": list(notes or []),
    }
    if generated is not None:
        sheet["meta"] = {"generated": deepcopy(generated)}
    return sheet


def replay_advancement(
    sheet: dict[str, Any], skin: dict[str, Any], *, check_current: bool = True
) -> dict[str, Any]:
    """Verify historical prices and replay every entry from the creation snapshot.

    The current sheet's creation price is deliberately never used to infer how
    many advancement points were spent. Creation refunds can hide later raises.
    """
    if sheet.get("schema_version") != SHEET_SCHEMA_VERSION:
        raise ValueError("advancement needs a schema-2 creation snapshot; explicitly adopt an unadvanced legacy sheet first")
    creation = sheet.get("creation")
    if not isinstance(creation, dict) or not isinstance(creation.get("snapshot"), dict):
        raise ValueError("missing immutable creation.snapshot")
    budget = _rules.integer(creation.get("build_points_budget"), "creation build_points_budget")
    used = _rules.integer(creation.get("build_points_used"), "creation build_points_used")
    if budget < 0 or used < 0:
        raise ValueError("creation build points must be nonnegative")
    snapshot = creation["snapshot"]
    attrs = snapshot.get("attributes")
    if not isinstance(attrs, dict) or set(attrs) != set(skin.get("attributes", {})):
        raise ValueError("creation snapshot attributes do not match the skin")
    attrs = dict(attrs)
    stamina = snapshot.get("stamina")
    _rules.validate_scores(attrs, stamina)
    bought_tags = _tags(snapshot.get("bought_tags"), "creation bought_tags")
    free_tags = validate_free_tags(snapshot.get("free_tags"), skin)
    tags = _tags(bought_tags + [entry["name"] for entry in free_tags])
    price = _rules.creation_price(attrs, stamina, bought_tags)
    if used != price:
        raise ValueError(f"creation build_points_used ({used}) != snapshot price ({price}); do not reprice advancement as creation")
    if used > budget:
        raise ValueError(f"build points exceeded at creation: needed={used} budget={budget}")
    advancement = sheet.get("advancement")
    if not isinstance(advancement, dict) or not isinstance(advancement.get("entries"), list):
        raise ValueError("advancement.entries must be an ordered list")
    available, awarded, spent = budget - used, 0, 0
    milestone_ids: list[str] = []
    for index, entry in enumerate(advancement["entries"], 1):
        prefix = f"advancement entry {index}"
        if not isinstance(entry, dict):
            raise ValueError(f"{prefix} must be a mapping")
        kind = entry.get("type")
        if kind == "milestone":
            event_id = entry.get("id")
            if not isinstance(event_id, str) or not event_id.strip():
                raise ValueError(f"{prefix} milestone needs a nonempty id")
            if event_id in milestone_ids:
                raise ValueError(f"duplicate milestone id: {event_id}")
            if _rules.integer(entry.get("points"), f"{prefix} points") != _rules.MILESTONE_POINTS:
                raise ValueError(f"{prefix} milestones award exactly {_rules.MILESTONE_POINTS} points")
            milestone_ids.append(event_id)
            awarded += _rules.MILESTONE_POINTS
            available += _rules.MILESTONE_POINTS
            continue
        if kind == "raise":
            key = entry.get("stat")
            if key != "STM" and key not in attrs:
                raise ValueError(f"{prefix} unknown stat: {key}")
            current = stamina if key == "STM" else attrs[key]
            before = _rules.integer(entry.get("from"), f"{prefix} from")
            after = _rules.integer(entry.get("to"), f"{prefix} to")
            if before != current or after != current + 1:
                raise ValueError(f"{prefix} must raise {key} from its replayed {current} to {current + 1}")
            cost = _rules.raise_cost(current, stamina=key == "STM")
            if key == "STM":
                stamina = after
            else:
                attrs[key] = after
        elif kind == "tag":
            name = entry.get("name")
            tags = _tags(tags + [name])
            cost = _rules.TAG_COST
        else:
            raise ValueError(f"{prefix} has unknown type: {kind}")
        declared_cost = _rules.integer(entry.get("cost"), f"{prefix} cost")
        if declared_cost != cost:
            raise ValueError(f"{prefix} costs {cost}, not declared {declared_cost}")
        if cost > available:
            raise ValueError(f"{prefix} overspends: cost={cost} available={available}")
        spent += cost
        available -= cost
    if check_current:
        if sheet.get("attributes") != attrs:
            raise ValueError("current attributes do not match creation plus advancement replay")
        if sheet.get("pools", {}).get("stamina", {}).get("max") != stamina:
            raise ValueError("current Stamina max does not match creation plus advancement replay")
        current_tags = _tags(sheet.get("tags"))
        if set(current_tags) != set(tags):
            raise ValueError("current tags do not match creation grants and recorded purchases")
    return {
        "creation_points_used": used, "creation_points_unspent": budget - used,
        "points_awarded": awarded, "advancement_points_spent": spent,
        "points_available": available, "milestones": milestone_ids,
        "attributes": attrs, "stamina": stamina, "tags": tags,
    }


def _editable_sheet(sheet: dict[str, Any], skin: dict[str, Any]) -> tuple[dict, dict]:
    summary = replay_advancement(sheet, skin)
    result = deepcopy(sheet)
    luck = result.get("pools", {}).get("luck", {})
    if luck.get("max") != summary["attributes"].get(skin.get("luck_key")):
        raise ValueError("Luck max does not match its attribute; run recalc_sheet first")
    return result, summary


def award_milestone(
    sheet: dict[str, Any], skin: dict[str, Any], event_id: str, *, label: str = "", boon: str = ""
) -> dict[str, Any]:
    result, _ = _editable_sheet(sheet, skin)
    entry = {"type": "milestone", "id": event_id, "label": label,
             "points": _rules.MILESTONE_POINTS, "boon": boon}
    result["advancement"]["entries"].append(entry)
    replay_advancement(result, skin)
    result["pools"]["luck"]["current"] = result["pools"]["luck"]["max"]
    return result


def raise_stat(sheet: dict[str, Any], skin: dict[str, Any], key: str, steps: int = 1) -> dict[str, Any]:
    _rules.integer(steps, "steps")
    if steps < 1:
        raise ValueError("steps must be positive")
    result, summary = _editable_sheet(sheet, skin)
    if key != "STM" and key not in summary["attributes"]:
        raise ValueError(f"unknown stat '{key}' (use a skin attribute or STM)")
    for _ in range(steps):
        current = result["pools"]["stamina"]["max"] if key == "STM" else result["attributes"][key]
        cost = _rules.raise_cost(current, stamina=key == "STM")
        result["advancement"]["entries"].append(
            {"type": "raise", "stat": key, "from": current, "to": current + 1, "cost": cost}
        )
        if key == "STM":
            result["pools"]["stamina"]["max"] += 1
        else:
            result["attributes"][key] += 1
            if key == skin.get("luck_key"):
                result["pools"]["luck"]["max"] += 1
                result["pools"]["luck"]["current"] += 1
    replay_advancement(result, skin)
    return result


def buy_tag(sheet: dict[str, Any], skin: dict[str, Any], name: str) -> dict[str, Any]:
    result, _ = _editable_sheet(sheet, skin)
    result["advancement"]["entries"].append({"type": "tag", "name": name, "cost": _rules.TAG_COST})
    result["tags"].append(name)
    replay_advancement(result, skin)
    return result


def adopt_legacy_creation(sheet: dict[str, Any], skin: dict[str, Any]) -> dict[str, Any]:
    """Only after an explicit assertion that this sheet has never advanced.

    Existing flat tags are bought tags. No advancement or free-grant history is
    invented; sheets whose declared spending disagrees need manual reconciliation.
    """
    if sheet.get("schema_version") != 1:
        raise ValueError("only schema-1 sheets need creation adoption")
    for container in (sheet, sheet.get("creation", {}), sheet.get("meta", {})):
        if not isinstance(container, dict):
            continue
        for key in ("advancement", "milestones", "points_awarded", "advancement_points", "xp"):
            if container.get(key):
                raise ValueError(f"legacy {key} is ambiguous; reconstruct its real advancement history manually")
    creation = sheet.get("creation")
    if not isinstance(creation, dict) or "snapshot" in creation:
        raise ValueError("legacy creation spending is missing or ambiguous")
    attrs = sheet.get("attributes")
    stamina = sheet.get("pools", {}).get("stamina", {}).get("max")
    if not isinstance(attrs, dict):
        raise ValueError("legacy attributes missing")
    tags = _tags(sheet.get("tags", []))
    used = creation.get("build_points_used")
    if used != _rules.creation_price(attrs, stamina, tags):
        raise ValueError("legacy spending differs from the current creation price; advancement history is ambiguous")
    result = deepcopy(sheet)
    for field in ("tracks", "pools"):
        container = result.get(field)
        if isinstance(container, dict) and "pressure" in container:
            legacy = container["pressure"]
            if not isinstance(legacy, dict) or type(legacy.get("current")) is not int or legacy["current"] != 0:
                raise ValueError(f"nonzero or ambiguous legacy {field}.pressure requires explicit campaign history migration")
            del container["pressure"]
            if field == "tracks" and not container:
                del result[field]
    result["schema_version"] = SHEET_SCHEMA_VERSION
    result["tags"] = tags
    result["creation"]["snapshot"] = {
        "attributes": dict(attrs), "stamina": stamina, "bought_tags": list(tags), "free_tags": [],
    }
    result["advancement"] = {"entries": []}
    replay_advancement(result, skin)
    return result
