"""Pure bookkeeping for skin resources; eligibility and consequences stay with the Custodian."""
from __future__ import annotations

from copy import deepcopy


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _definitions(skin: dict) -> dict:
    return skin.get("resources", {})


def resolve_id(skin: dict, name: str) -> str:
    """Accept a manifest id (totem_mark) or its display name ("Totem Mark")."""
    definitions = _definitions(skin)
    if name in definitions:
        return name
    wanted = name.strip().casefold().replace("-", " ").replace("_", " ")
    matches = [key for key, d in definitions.items()
               if wanted in {key.replace("_", " "), str(d.get("name", "")).casefold()}]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"unknown skin resource: {name}")


def new_resources(skin: dict, actors: list[str]) -> dict:
    """Seed counters, without granting the abilities whose uses they record."""
    actors = sorted(set(actors))
    result = {"party": {}, "characters": {actor: {} for actor in actors}}
    for key, definition in _definitions(skin).items():
        state = {"name": definition["name"], "kind": definition["kind"]}
        if definition["kind"] == "uses":
            state.update(used=0, limit=definition.get("limit", 1), reset=definition["reset"])
        else:
            maximum = len(actors) if definition.get("per_character") else definition.get("max")
            initial = len(actors) if definition.get("per_character") else definition.get("initial", 0)
            state.update(current=initial, max=maximum)
        if definition["scope"] == "party":
            result["party"][key] = state
        else:
            for actor in actors:
                result["characters"][actor][key] = deepcopy(state)
    return result


def validate_resources(resources: dict, skin: dict, actors: list[str]) -> list[str]:
    errors = []
    if not isinstance(resources, dict):
        return ["resources must be a mapping"]
    expected = new_resources(skin, actors)
    if set(resources) != {"party", "characters"}:
        errors.append("resources must contain only party and characters")
    for scope in ("party", "characters"):
        if not isinstance(resources.get(scope), dict):
            errors.append(f"resources.{scope} must be a mapping")
    if errors:
        return errors
    if set(resources["characters"]) != set(actors):
        errors.append("resources.characters must match the character sheet stems")

    def check_bucket(actual, wanted, path):
        if not isinstance(actual, dict):
            errors.append(f"{path} must be a mapping")
            return
        if set(actual) != set(wanted):
            errors.append(f"{path} resource names do not match the skin")
        for key, seed in wanted.items():
            value = actual.get(key)
            label = f"{path}.{key}"
            if not isinstance(value, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for field in ("name", "kind"):
                if value.get(field) != seed[field]:
                    errors.append(f"{label}.{field} does not match the skin")
            if seed["kind"] == "uses":
                used = value.get("used")
                if not _is_int(value.get("limit")) or value.get("limit") != seed["limit"] or value.get("reset") != seed["reset"]:
                    errors.append(f"{label} limit/reset does not match the skin")
                if not _is_int(used) or not 0 <= used <= seed["limit"]:
                    errors.append(f"{label}.used must be between 0 and {seed['limit']}")
            else:
                current, maximum = value.get("current"), value.get("max")
                if maximum != seed["max"] or (maximum is not None and not _is_int(maximum)):
                    errors.append(f"{label}.max does not match the skin/party size")
                if not _is_int(current) or current < 0 or (seed["max"] is not None and current > seed["max"]):
                    errors.append(f"{label}.current is out of range")

    check_bucket(resources["party"], expected["party"], "resources.party")
    for actor in sorted(set(actors)):
        check_bucket(resources["characters"].get(actor), expected["characters"][actor], f"resources.characters.{actor}")
    return errors


def reset_resources(resources: dict, boundary: str) -> dict:
    """Reset matching use limits, never refill pools; a session also starts a scene."""
    if boundary not in {"scene", "session", "port", "camp"}:
        raise ValueError("resource reset boundary must be scene, session, port, or camp")
    result = deepcopy(resources)
    boundaries = {boundary, "scene"} if boundary == "session" else {boundary}
    for bucket in [result["party"], *result["characters"].values()]:
        for state in bucket.values():
            if state["kind"] == "uses" and state["reset"] in boundaries:
                state["used"] = 0
    return result


def _state(resources: dict, definition: dict, key: str, actor: str | None) -> dict:
    if definition["scope"] == "party":
        return resources["party"][key]
    if not actor or actor not in resources["characters"]:
        raise ValueError(f"{key} requires a known character")
    return resources["characters"][actor][key]


def use_resource(resources: dict, skin: dict, resource_id: str, actor: str | None = None,
                 amount: int = 1, *, purpose: str | None = None) -> tuple[dict, dict]:
    """Record an adjudicated use. Returns a new state and unapplied consequence data."""
    if not _is_int(amount) or amount < 1:
        raise ValueError("resource amount must be a positive integer")
    resource_id = resolve_id(skin, resource_id)
    definition = _definitions(skin)[resource_id]
    if definition.get("purpose") and purpose != definition["purpose"]:
        raise ValueError(f"{resource_id} may only be used for {definition['purpose']}")
    result = deepcopy(resources)
    state = _state(result, definition, resource_id, actor)
    counter = "used" if state["kind"] == "uses" else "current"
    before = state[counter]
    after = before + amount if counter == "used" else before - amount
    if (counter == "used" and after > state["limit"]) or after < 0:
        raise ValueError(f"{resource_id} has insufficient remaining uses/tokens")
    linked = definition.get("per_actor_use")
    if linked:
        if amount != 1:
            raise ValueError(f"{resource_id} permits one token per character per scene")
        result, _ = use_resource(result, skin, linked, actor, amount)
        state = _state(result, definition, resource_id, actor)
    state[counter] = after
    pressure_gain = definition.get("zero_pressure", 0) if counter == "current" and before > 0 and after == 0 else 0
    return result, {"resource": resource_id, "actor": actor, "amount": amount, "before": before,
                    "after": after, "pressure_gain": pressure_gain, "pressure_source": f"{resource_id}_empty"}


def recover_resource(resources: dict, skin: dict, resource_id: str, actor: str | None = None,
                     amount: int = 1) -> tuple[dict, dict]:
    """Restore pool tokens after the fiction permits it; uses reset at their boundary."""
    if not _is_int(amount) or amount < 1:
        raise ValueError("resource amount must be a positive integer")
    resource_id = resolve_id(skin, resource_id)
    definition = _definitions(skin)[resource_id]
    if definition["kind"] != "pool":
        raise ValueError("only a known pool can recover tokens")
    result = deepcopy(resources)
    state = _state(result, definition, resource_id, actor)
    before = state["current"]
    state["current"] = before + amount if state["max"] is None else min(state["max"], before + amount)
    return result, {"resource": resource_id, "actor": actor, "recovered": state["current"] - before,
                    "before": before, "after": state["current"]}
