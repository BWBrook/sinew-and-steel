"""Pressure bookkeeping. Fictional applicability is supplied as explicit contexts.

All mutation happens in memory; the campaign transaction commits it with its
receipt. A gain leaves a crisis pending until its consequence is recorded.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def new_track() -> dict:
    return {"current": 0, "cycle": 0, "fired_steps": [], "pending": {},
            "crisis_pending": False, "tipper": None}


def new_pressure(skin: dict, actors: list[str]) -> dict:
    scope = skin.get("pressure_scope", "party")
    keys = ["party"] if scope == "party" else actors
    return {"name": skin.get("pressure_track", "Pressure"), "scope": scope,
            "tracks": {key: new_track() for key in keys}, "effects": [], "crises": []}


def sync_actors(pressure: dict, actors: list[str]) -> None:
    if pressure["scope"] == "character":
        for actor in actors:
            pressure["tracks"].setdefault(actor, new_track())


def track_for(pressure: dict, actor: str | None = None) -> tuple[str, dict]:
    key = "party" if pressure["scope"] == "party" else actor
    if key not in pressure["tracks"]:
        raise ValueError("personal Pressure requires a known --character")
    return key, pressure["tracks"][key]


def validate_pressure(pressure: Any, skin: dict, actors: list[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(pressure, dict):
        return ["structured Pressure is missing; adopt legacy state explicitly"]
    scope = skin.get("pressure_scope", "party")
    if pressure.get("scope") != scope:
        errors.append(f"Pressure scope must be {scope}")
    tracks = pressure.get("tracks")
    if not isinstance(tracks, dict):
        return errors + ["Pressure tracks must be a mapping"]
    expected = {"party"} if scope == "party" else set(actors)
    if set(tracks) != expected:
        errors.append("Pressure track keys do not match the campaign roster/scope")
    definitions = {r["step"] for r in skin.get("pressure_steps", [])
                   if r.get("kind") == "next_disadvantage"}
    for key, track in tracks.items():
        if not isinstance(track, dict):
            errors.append(f"Pressure {key} is not a mapping")
            continue
        current = track.get("current")
        if type(current) is not int or not 0 <= current <= 5:
            errors.append(f"Pressure {key} must be 0..5")
            continue
        if type(track.get("cycle")) is not int or track["cycle"] < 0:
            errors.append(f"Pressure {key} has invalid cycle")
        if track.get("crisis_pending") != (current == 5):
            errors.append(f"Pressure {key} crisis_pending must match step 5")
        fired = track.get("fired_steps", [])
        if not isinstance(fired, list) or any(type(s) is not int or s not in definitions for s in fired):
            errors.append(f"Pressure {key} has invalid fired steps")
            fired = []
        elif len(fired) != len(set(fired)):
            errors.append(f"Pressure {key} repeats a fired step")
        pending = track.get("pending", {})
        if not isinstance(pending, dict):
            errors.append(f"Pressure {key} pending must be a mapping")
            continue
        for actor, penalties in pending.items():
            if actor not in actors or (scope == "character" and actor != key):
                errors.append(f"Pressure {key} penalty belongs to an unknown/other actor")
            if not isinstance(penalties, list):
                errors.append(f"Pressure {key} penalties must be a list")
                continue
            for penalty in penalties:
                if not isinstance(penalty, dict) or penalty.get("step") not in fired or penalty.get("step", 6) > current:
                    errors.append(f"Pressure {key} has an unfired or discarded penalty")
    for field in ("effects", "crises"):
        if not isinstance(pressure.get(field), list):
            errors.append(f"Pressure {field} must be a list")
    return errors


def change(pressure: dict, skin: dict, actors: list[str], *, amount: int,
           source: str, category: str, actor: str | None = None) -> list[dict]:
    if type(amount) is not int or not source.strip():
        raise ValueError("Pressure requires an integer amount and a source")
    if category not in {"action_cost", "failure", "ambient", "purge"}:
        raise ValueError("invalid Pressure source category")
    if (amount < 0) != (category == "purge") and amount != 0:
        raise ValueError("only a purge can reduce Pressure")
    if actor is not None and actor not in actors:
        raise ValueError(f"unknown Pressure actor: {actor}")
    key, track = track_for(pressure, actor)
    if track["crisis_pending"] and amount < 0:
        raise ValueError("record the pending crisis before purging Pressure")
    before = track["current"]
    after = min(5, max(0, before + amount))
    fired = []
    discarded = []
    affected = actors if pressure["scope"] == "party" else [key]
    for rule in skin.get("pressure_steps", []):
        step = rule["step"]
        if rule.get("kind") != "next_disadvantage":
            continue
        if before < step <= after and step not in track["fired_steps"]:
            track["fired_steps"].append(step)
            fired.append(step)
            for who in affected:
                track["pending"].setdefault(who, []).append({
                    "step": step, "label": rule["label"],
                    "attributes": rule.get("attributes", []),
                    "contexts": rule.get("contexts", [])})
    for who, penalties in track["pending"].items():
        discarded.extend({"actor": who, **p} for p in penalties if p["step"] > after)
        track["pending"][who] = [p for p in penalties if p["step"] <= after]
    track["current"] = after
    if after == 5 and not track["crisis_pending"]:
        track["crisis_pending"] = True
        track["tipper"] = actor
    return [{"type": "pressure", "track": key, "actor": actor, "source": source,
             "category": category, "amount": amount, "before": before, "after": after,
             "cycle": track["cycle"], "fired_steps": fired, "discarded": discarded,
             "crisis_pending": track["crisis_pending"]}]


def _applies(rule: dict, attribute: str | None, contexts: list[str]) -> bool:
    return ((not rule.get("attributes") or attribute in rule["attributes"])
            and (not rule.get("contexts") or bool(set(contexts) & set(rule["contexts"]))))


def modifiers(pressure: dict, skin: dict, actor: str, attribute: str | None,
              contexts: list[str], consume: bool = False) -> dict:
    key, track = track_for(pressure, actor)
    result = {"track": key, "level": track["current"],
              "active_steps": list(range(1, min(4, track["current"]) + 1)),
              "disadvantage_sources": [], "incoming_advantage_sources": [],
              "costs": [], "pending_consumed": [], "custodian_levers": []}
    pending = track["pending"].get(actor, [])
    matched = [p for p in pending if _applies(p, attribute, contexts)]
    for p in matched:
        result["disadvantage_sources"].append(f"pressure:{key}:step{p['step']}:{p['label']}")
    result["pending_consumed"] = deepcopy(matched)
    if consume:
        track["pending"][actor] = [p for p in pending if p not in matched]
    for rule in skin.get("pressure_steps", []):
        if rule["step"] > track["current"] or not _applies(rule, attribute, contexts):
            continue
        label = f"pressure:{key}:step{rule['step']}:{rule['label']}"
        if rule["kind"] == "custodian":
            result["custodian_levers"].append(label)
        elif rule["kind"] == "disadvantage":
            result["disadvantage_sources"].append(label)
        elif rule["kind"] == "incoming_advantage":
            result["incoming_advantage_sources"].append(label)
        elif rule["kind"] in {"toll", "pressure_cost", "luck_cost"}:
            result["costs"].append({**rule, "source": label})
    return result


def crisis(pressure: dict, skin: dict, actors: list[str], *, target: str,
           table_result: list[int], description: str, effects: list[dict] | None = None,
           actor: str | None = None) -> list[dict]:
    key, track = track_for(pressure, actor)
    if not track["crisis_pending"]:
        raise ValueError("this track has no pending crisis")
    if target not in actors or (pressure["scope"] == "character" and target != key):
        raise ValueError("crisis target must be an affected campaign character")
    if not description.strip():
        raise ValueError("record the crisis consequence before resetting")
    if not table_result or any(type(r) is not int or not 1 <= r <= 6 for r in table_result):
        raise ValueError("crisis table results must be d6 faces")
    effects = deepcopy(effects or [])
    index = len(pressure["crises"]) + 1
    for i, effect in enumerate(effects):
        if not effect.get("description") or not effect.get("duration"):
            raise ValueError("each crisis effect needs description and duration")
        effect.setdefault("target", target)
        if effect["target"] not in actors and effect["target"] != "party":
            raise ValueError("unknown crisis effect target")
        effect.update(id=f"crisis-{index}-{i + 1}", crisis=index, active=True)
    record = {"type": "crisis", "id": index, "track": key, "cycle": track["cycle"],
              "target": target, "tipper": track["tipper"], "table_result": table_result,
              "description": description, "effects": deepcopy(effects)}
    pressure["crises"].append(deepcopy(record))
    pressure["effects"].extend(effects)
    reset = {"type": "pressure", "track": key, "actor": target,
             "source": f"crisis:{index}", "category": "crisis_reset",
             "amount": -track["current"], "before": track["current"], "after": 0,
             "cycle": track["cycle"]}
    cycle = track["cycle"] + 1
    track.clear()
    track.update(new_track(), cycle=cycle)
    return [record, reset]


def clear_effect(pressure: dict, effect_id: str, reason: str) -> dict:
    if not reason.strip():
        raise ValueError("give the reason/duration boundary that ended the effect")
    for effect in pressure["effects"]:
        if effect["id"] == effect_id and effect["active"]:
            effect.update(active=False, ended_by=reason)
            return {"type": "effect_ended", "effect_id": effect_id, "reason": reason}
    raise ValueError("unknown or already ended crisis effect")
