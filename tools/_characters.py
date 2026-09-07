from __future__ import annotations

from datetime import date
from typing import Any


def build_sheet(
    *,
    skin_slug: str,
    skin: dict[str, Any],
    name: str,
    player: str = "",
    attributes: dict[str, int],
    stamina: int,
    build_points_budget: int,
    build_points_used: int,
    tags: list[str] | None = None,
    notes: list[str] | None = None,
    generated: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the one canonical character-sheet shape."""
    if len(attributes) != 5:
        raise ValueError("skin attributes missing or incomplete")

    luck_key = skin.get("luck_key")
    if luck_key not in attributes:
        raise ValueError("luck_key not found in attributes")

    sheet: dict[str, Any] = {
        "schema_version": 1,
        "name": name,
        "skin": skin_slug,
        "player": player,
        "created": date.today().isoformat(),
        "creation": {
            "build_points_budget": int(build_points_budget),
            "build_points_used": int(build_points_used),
        },
        "attributes": dict(attributes),
        "pools": {
            "luck": {
                "name": skin.get("luck_name", luck_key),
                "current": int(attributes[luck_key]),
                "max": int(attributes[luck_key]),
            },
            "stamina": {
                "current": int(stamina),
                "max": int(stamina),
            },
        },
        "inventory": {
            "big_items": [],
            "small_items": [],
        },
        "tags": list(tags or []),
        "notes": list(notes or []),
    }
    if generated is not None:
        sheet["meta"] = {"generated": generated}
    return sheet
