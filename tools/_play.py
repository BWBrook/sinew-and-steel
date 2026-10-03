"""Campaign operations. The CLI supplies adjudicated intent, context and stakes."""
from __future__ import annotations

from copy import deepcopy
import random

import _dice
import _pressure
import _resources
import _rules
import _runtime


def entity(key: str, sheets: dict, tracker: dict) -> dict:
    if key in sheets:
        return sheets[key]
    if key.startswith("npc:") and key[4:] in tracker.get("npcs", {}):
        return tracker["npcs"][key[4:]]
    raise ValueError(f"unknown combatant: {key}")


def ensure_ready(tracker: dict, *, allow_crisis: bool = False) -> None:
    if tracker.get("pending_action"):
        raise ValueError("settle the pending action before starting another operation")
    if not allow_crisis and any(t["crisis_pending"] for t in tracker["pressure"]["tracks"].values()):
        raise ValueError("record the pending crisis before the next action")


def _stat(sheet: dict, skin: dict, attribute: str) -> int:
    return _runtime.sheet_stat(sheet, skin, attribute)


def pay_costs(actor: str, sheet: dict, tracker: dict, skin: dict, sheets: dict,
              modifiers: dict, *, toll: str | None, luck: int = 0,
              pressure: int = 0, source: str, use_resource: str | None = None) -> list[dict]:
    if luck < 0 or pressure < 0:
        raise ValueError("action costs must be nonnegative")
    events = []
    if use_resource:
        tracker["resources"], event = _resources.use_resource(
            tracker["resources"], skin, use_resource, actor)
        events.append({"type": "resource", **event, "source": source})
        pressure += event.get("pressure_gain", 0)
    for cost in modifiers.get("costs", []):
        amount = cost.get("amount", 1)
        if cost["kind"] == "toll":
            if toll not in {"luck", "pressure"}:
                raise ValueError(f"choose --toll luck|pressure for {actor}: {cost['source']}")
            if toll == "luck":
                events.append(_runtime.luck_change(sheet, -amount, actor=actor,
                              source=cost["source"], category="action_cost"))
            else:
                events.extend(_pressure.change(tracker["pressure"], skin, list(sheets),
                              amount=amount, source=cost["source"], category="action_cost", actor=actor))
        elif cost["kind"] == "luck_cost":
            events.append(_runtime.luck_change(sheet, -amount, actor=actor,
                          source=cost["source"], category="action_cost"))
        elif cost["kind"] == "pressure_cost":
            events.extend(_pressure.change(tracker["pressure"], skin, list(sheets),
                          amount=amount, source=cost["source"], category="action_cost", actor=actor))
    if luck:
        events.append(_runtime.luck_change(sheet, -luck, actor=actor, source=source, category="action_cost"))
    if pressure:
        if actor not in sheets:
            raise ValueError("only party characters pay the campaign's Pressure costs")
        events.extend(_pressure.change(tracker["pressure"], skin, list(sheets),
                      amount=pressure, source=source, category="action_cost", actor=actor))
    return events


def combat_preflight(tracker: dict, sheets: dict, actor: str) -> None:
    """Refuse an action from a combatant who may not act now."""
    combat = tracker.get("combat", {})
    if not combat.get("active") or actor not in combat["positions"]:
        raise ValueError(f"{actor} is not in an active combat")
    if actor in combat["acted"]:
        raise ValueError("this combatant has already acted this round")
    if entity(actor, sheets, tracker)["pools"]["stamina"]["current"] <= 0:
        raise ValueError("a combatant at zero Stamina cannot act")
    # Lower-priority sides wait for every able member of earlier sides.
    side = next(s for s, members in combat["sides"].items() if actor in members)
    for earlier in combat["order"][:combat["order"].index(side)]:
        waiting = [member for member in combat["sides"][earlier]
                   if member not in combat["acted"] and entity(member, sheets, tracker)["pools"]["stamina"]["current"] > 0]
        if waiting:
            raise ValueError(f"earlier side still has actions: {', '.join(waiting)}")


def uses_turn(combat: dict, kind: str, actor: str, combat_action: bool = False) -> bool:
    # An attack, an opposed test a combatant starts (intimidate, disarm, shove), or a
    # check declared as the combatant's action is that combatant's action for the round.
    return bool(combat.get("active")) and (kind == "attack" or combat_action or (
        kind == "opposed" and actor in combat["positions"]))


def _stance_sources(tracker: dict, actor: str, sheet: dict, role: str,
                    contexts: list[str]) -> tuple[list[str], list[str]]:
    adv, dis = [], []
    if not tracker.get("combat", {}).get("active"):
        return adv, dis
    stance = tracker.get("combat", {}).get("positions", {}).get(actor, "steady")
    if stance == "vanguard":
        (adv if role == "attacker" else dis).append("position:vanguard")
    elif stance == "watchful":
        (dis if role == "attacker" else adv).append("position:watchful")
    elif stance == "ranged":
        if role == "attacker":
            if "missile" not in contexts:
                raise ValueError("Ranged position permits missile attacks only")
            adv.append("position:ranged")
        elif "melee" in contexts and "screened" not in contexts:
            dis.append("position:ranged_exposed")
    return adv, dis


def prepare_action(tracker: dict, sheets: dict, skin: dict, *, kind: str,
                   actor: str, attribute: str, method: str, stakes: str,
                   opponent: str | None = None, defender_attribute: str | None = None,
                   contexts: list[str] | None = None, defender_contexts: list[str] | None = None,
                   adv_sources: list[str] | None = None, dis_sources: list[str] | None = None,
                   defender_adv_sources: list[str] | None = None,
                   defender_dis_sources: list[str] | None = None,
                   toll: str | None = None,
                   luck_cost: int = 0, pressure_cost: int = 0,
                   failure_pressure: int = 0, use_resource: str | None = None,
                   edge: int = 0, soak: int = 0, injury: bool = False,
                   gritty: bool = False, undefended: bool = False,
                   no_nudge: bool = False, crisis_test: bool = False,
                   combat_action: bool = False, success_luck_cost: int = 0) -> tuple[dict, list[dict]]:
    ensure_ready(tracker, allow_crisis=crisis_test)
    if kind not in {"check", "opposed", "attack"} or not method.strip() or not stakes.strip():
        raise ValueError("tests require their method and declared stakes")
    if failure_pressure < 0:
        raise ValueError("failure Pressure must be nonnegative")
    if type(success_luck_cost) is not int or success_luck_cost < 0:
        raise ValueError("a success-only Luck cost must be a nonnegative integer")
    if crisis_test:
        # A test the crisis itself demands (Service Duct Blues' nanite alarm) is not
        # a chosen attempt: it pays no toll or cost, though step penalties apply.
        if kind != "check":
            raise ValueError("a crisis test is a single check")
        if not any(track["crisis_pending"] for track in tracker["pressure"]["tracks"].values()):
            raise ValueError("--crisis-test needs a pending crisis")
        if toll or luck_cost or pressure_cost or failure_pressure or use_resource or success_luck_cost:
            raise ValueError("a crisis test pays no costs")
    if combat_action:
        if kind != "check":
            raise ValueError("attacks and opposed tests already use the combatant's action")
        if not tracker.get("combat", {}).get("active"):
            raise ValueError("--combat-action needs an active combat")
    if injury and skin.get("luck_key") != "HOP":
        raise ValueError("the optional Injury module belongs to Twilight")
    # Edge may exceed +2 (a boon or stunt on a brutal weapon); skins that cap it say so.
    if type(edge) is not int or edge < 0 or type(soak) is not int or soak < 0:
        raise ValueError("weapon edge and soak must be nonnegative integers")
    if gritty and not injury:
        raise ValueError("--gritty requires the optional Injury module")
    if undefended and kind != "attack":
        raise ValueError("only an attack may skip an impossible defence")
    a_sheet = entity(actor, sheets, tracker)
    if failure_pressure and actor not in sheets:
        raise ValueError("failure Pressure must name an affected party character")
    d_sheet = entity(opponent, sheets, tracker) if opponent else None
    if kind in {"opposed", "attack"} and (not opponent or (not defender_attribute and not undefended)):
        raise ValueError("opposed tests need an opponent and defence attribute")
    if actor == opponent:
        raise ValueError("a character cannot oppose itself")
    contexts = list(dict.fromkeys([*(contexts or []), "risky"]))
    d_contexts = list(dict.fromkeys([*(defender_contexts or []), "risky"]))
    sides = [("attacker", actor, a_sheet, attribute, contexts, toll,
              list(adv_sources or []), list(dis_sources or []))]
    if d_sheet and not undefended:
        sides.append(("defender", opponent, d_sheet, defender_attribute, d_contexts, None,
                      list(defender_adv_sources or []), list(defender_dis_sources or [])))
    snapshots = {}
    for role, who, sheet, key, context, _, adv, dis in sides:
        if who in sheets:
            mods = _pressure.modifiers(tracker["pressure"], skin, who, key, context, consume=False)
        else:
            mods = {"level": None, "disadvantage_sources": [], "incoming_advantage_sources": [],
                    "costs": [], "pending_consumed": [], "custodian_levers": []}
        dis += mods["disadvantage_sources"]
        if sheet.get("conditions", {}).get("injured") and key in {"STR", "NIM"}:
            dis.append("condition:injured")
        if kind == "attack":
            sa, sd = _stance_sources(tracker, who, sheet, role, context)
            adv += sa
            dis += sd
        snapshots[role] = {"modifiers": mods, "advantage_sources": adv, "disadvantage_sources": dis}
    if kind == "attack" and opponent in sheets:
        target_mods = _pressure.modifiers(tracker["pressure"], skin, opponent, defender_attribute,
                                          d_contexts, consume=False)
        snapshots["attacker"]["advantage_sources"] += target_mods["incoming_advantage_sources"]
    if uses_turn(tracker.get("combat", {}), kind, actor, combat_action):
        combat_preflight(tracker, sheets, actor)
    pressure_snapshot = deepcopy(tracker["pressure"])
    events = []
    # Take all modifiers at action start, before anyone pays an upfront cost.
    for role, who, sheet, key, context, toll_choice, _, _ in sides:
        if who in sheets:
            _pressure.modifiers(tracker["pressure"], skin, who, key, context, consume=True)
    # Only the side attempting the test pays; defence never pays tolls or step costs.
    charged = {**snapshots["attacker"]["modifiers"], "costs": []} if crisis_test else snapshots["attacker"]["modifiers"]
    events += pay_costs(actor, a_sheet, tracker, skin, sheets, charged,
                        toll=toll, luck=luck_cost, pressure=pressure_cost,
                        source=method, use_resource=use_resource)
    if success_luck_cost > a_sheet["pools"]["luck"]["current"]:
        raise ValueError("not enough Luck to set aside the success-only cost")
    targets = {role: _stat(sheet, skin, key) for role, _, sheet, key, _, _, _, _ in sides}
    checks = {}
    for role, who, sheet, key, context, _, _, _ in sides:
        snapshot = snapshots[role]
        checks[role] = _dice.resolve_check(targets[role],
                                          adv=bool(snapshot["advantage_sources"]),
                                          dis=bool(snapshot["disadvantage_sources"]))
        snapshot.update(actor=who, attribute=key, contexts=context)
    action = {"kind": kind, "actor": actor, "opponent": opponent, "method": method,
              "stakes": stakes, "checks": checks, "sides": snapshots,
              "failure_pressure": failure_pressure, "edge": edge, "soak": soak,
              "injury": injury, "gritty": gritty, "undefended": undefended, "no_nudge": no_nudge,
              "crisis_test": crisis_test, "combat_action": combat_action,
              "reserved_luck": success_luck_cost, "pressure_snapshot": pressure_snapshot}
    tracker["pending_action"] = deepcopy(action)
    return action, events


def _fund_nudge(tracker: dict, sheets: dict, skin: dict, fund: str, payer: str,
                amount: int, source: str) -> list[dict]:
    """Pay a nudge from a pool the skin reserves for nudges (Companionship, Beast Bond)."""
    definition = skin.get("resources", {}).get(fund, {})
    if definition.get("kind") != "pool" or definition.get("purpose") != "nudge":
        raise ValueError(f"{fund} cannot pay for a nudge")
    if payer not in sheets:
        raise ValueError(f"{fund} pays only for a character's nudge")
    tracker["resources"], event = _resources.use_resource(
        tracker["resources"], skin, fund, payer, amount, purpose="nudge")
    events = [{"type": "resource", **event, "source": source}]
    if event.get("pressure_gain"):
        events += _pressure.change(tracker["pressure"], skin, list(sheets),
                  amount=event["pressure_gain"], source=event["pressure_source"],
                  category="action_cost", actor=payer)
    return events


def finish_action(tracker: dict, sheets: dict, skin: dict, *, nudge: int = 0,
                  nudge_target: str = "attacker", payer: str | None = None,
                  fund: str | None = None, deflection_nudge: int = 0,
                  seed: int | None = None,
                  adjustments: list[tuple[str, str, int]] | None = None) -> tuple[dict, list[dict]]:
    stored = tracker.get("pending_action")
    if not stored:
        raise ValueError("no pending action to settle")
    if stored.get("phase") == "deflection":
        if adjustments or nudge or (payer and payer != stored["target"]):
            raise ValueError("settle Deflection with --deflection-nudge; its defender pays")
        return finish_deflection(tracker, sheets, skin, nudge=deflection_nudge, fund=fund)
    if deflection_nudge:
        raise ValueError("read the persisted Deflection dice before choosing --deflection-nudge")
    action = deepcopy(stored)
    checks = action["checks"]
    events = []
    luck_spent: dict[str, int] = {}
    nudges = [(who, side, delta, False) for who, side, delta in (adjustments or [])]
    if fund:
        fund = _resources.resolve_id(skin, fund)
    if nudge:
        payer = payer or action["actor"]
        nudges.append((payer, nudge_target, nudge, fund))
    elif fund:
        raise ValueError("--fund pays for the --nudge")
    deltas: dict[str, int] = {}
    for who, side, delta, funded in nudges:
        # Unnudgeable magic: no one moves the caster's die, and the caster may not
        # spend on the opposing die either; a resister may still nudge their own.
        if action.get("no_nudge") and (side == "attacker" or who == action["actor"]):
            raise ValueError("this roll was declared --no-nudge (top-tier magic): no one may nudge the caster's die, and the caster may not nudge either die")
        if side not in checks:
            raise ValueError("cannot nudge a side that did not roll")
        if who not in {action["actor"], action["opponent"]}:
            raise ValueError("nudge payer must participate in this opposed test")
        # Validate each entry against the persisted die, including natural locks
        # even when opposing adjustments would add to zero.
        _dice.apply_nudge_to_check(checks[side], delta)
        deltas[side] = deltas.get(side, 0) + delta
        if not funded:
            luck_spent[who] = luck_spent.get(who, 0) + abs(delta)
    for side, delta in deltas.items():
        checks[side] = _dice.apply_nudge_to_check(checks[side], delta)
    # Validate each payer's complete cost and the optional token before changing
    # any pool. Each entry costs its absolute delta; opposing spends do not net.
    reserved = action.get("reserved_luck", 0)
    if reserved and luck_spent.get(action["actor"], 0) > entity(action["actor"], sheets, tracker)["pools"]["luck"]["current"] - reserved:
        raise ValueError(f"{reserved} Luck is set aside for the success-only cost and cannot fund a nudge")
    payments = [_runtime.luck_change(deepcopy(entity(who, sheets, tracker)), -amount,
                actor=who, source="nudge", category="nudge")
                for who, amount in luck_spent.items() if amount]
    if fund:
        events += _fund_nudge(tracker, sheets, skin, fund, payer, abs(nudge), "nudge")
    for event in payments:
        entity(event["actor"], sheets, tracker)["pools"]["luck"]["current"] = event["after"]
        events.append(event)
    if "defender" in checks:
        outcome = _dice.resolve_opposed_outcome(checks["attacker"], checks["defender"])
        success = outcome["winner"] == "attacker"
    else:
        success = checks["attacker"]["success"]
        outcome = {"winner": "attacker" if success else "defender", "reason": "single_check"}
    if success and reserved:
        events.append(_runtime.luck_change(entity(action["actor"], sheets, tracker), -reserved,
                      actor=action["actor"], source=f"{action['method']} (success cost)", category="action_cost"))
    for role, check in checks.items():
        side = action["sides"][role]
        who = side["actor"]
        # A defender's die records what it resisted, not the attacker's method as its own.
        events.append({"type": "roll", "actor": who, "role": role,
                       "attribute": side["attribute"],
                       "method": action["method"] if role == "attacker" else None,
                       "against": action["method"] if role == "defender" else None,
                       "crisis_test": action.get("crisis_test", False),
                       "reserved_luck": reserved if role == "attacker" else 0,
                       "stakes": action["stakes"], "target": check["stat"],
                       "advantage_sources": side["advantage_sources"],
                       "disadvantage_sources": side["disadvantage_sources"],
                       "contexts": side["contexts"], "pressure_at_start": side["modifiers"]["level"],
                       "pending_consumed": side["modifiers"]["pending_consumed"],
                       "nudges": [{"payer": payer_key, "delta": delta, "funding": funded or "luck"}
                                  for payer_key, target_side, delta, funded in nudges if target_side == role],
                       "luck_spent": luck_spent.get(who, 0),
                       "luck_current": entity(who, sheets, tracker)["pools"]["luck"]["current"],
                       "check": check, "outcome": outcome, "seed": action.get("seed")})
    result = {**action, "checks": checks, "outcome": outcome, "success": success}
    if action["kind"] == "attack" and success:
        target = entity(action["opponent"], sheets, tracker)
        damage = _rules.damage_from_check(checks["attacker"], edge=action["edge"], soak=action["soak"])
        pool = target["pools"]["stamina"]
        before = pool["current"]
        pool["current"] = max(0, before - damage)
        events.append({"type": "damage", "actor": action["actor"], "target": action["opponent"],
                       "damage": damage, "edge": action["edge"], "soak": action["soak"],
                       "before": before, "after": pool["current"]})
        result["damage"] = damage
        effective = checks["attacker"]["margin"]
        if checks.get("defender", {}).get("success"):
            effective -= checks["defender"]["margin"]
        injurious = checks["attacker"].get("crit") == "nat1" or (action["gritty"] and effective >= 8)
        if action["injury"] and injurious:
            who = action["opponent"]
            # Deflection is an involuntary reaction: its penalties apply, but it pays no toll.
            def_mods = (_pressure.modifiers(action["pressure_snapshot"], skin, who,
                        "Deflection", ["risky"], consume=False) if who in sheets else
                        {"level": None, "costs": [], "disadvantage_sources": []})
            deflection = _dice.resolve_check(10 + action["soak"] * 2,
                                            dis=bool(def_mods["disadvantage_sources"]))
            result.update(pending=True, phase="deflection", deflection=deflection)
            tracker["pending_action"] = {"phase": "deflection", "target": who,
                                         "check": deflection, "modifiers": def_mods,
                                         "result": deepcopy(result), "seed": seed}
            events.append({"type": "raw_roll", "role": "deflection", "actor": who,
                           "check": deflection, "seed": seed})
    if not success and action["failure_pressure"]:
        events += _pressure.change(tracker["pressure"], skin, list(sheets),
                  amount=action["failure_pressure"], source=action["method"], category="failure", actor=action["actor"])
    combat = tracker.get("combat", {})
    if uses_turn(combat, action["kind"], action["actor"], action.get("combat_action", False)):
        combat["acted"].append(action["actor"])
    if not result.get("pending"):
        tracker["pending_action"] = None
    return result, events


def finish_deflection(tracker: dict, sheets: dict, skin: dict, *, nudge: int = 0,
                      fund: str | None = None) -> tuple[dict, list[dict]]:
    """Settle already-persisted Deflection dice; this operation never rolls."""
    stored = tracker["pending_action"]
    actor = stored["target"]
    target = entity(actor, sheets, tracker)
    check = _dice.apply_nudge_to_check(stored["check"], nudge)
    events = []
    if fund:
        if not nudge:
            raise ValueError("--fund pays for the --deflection-nudge")
        events += _fund_nudge(tracker, sheets, skin, _resources.resolve_id(skin, fund), actor,
                              abs(nudge), "deflection_nudge")
    elif nudge:
        events.append(_runtime.luck_change(target, -abs(nudge), actor=actor,
                      source="deflection_nudge", category="nudge"))
    if not check["success"]:
        conditions = target.setdefault("conditions", {})
        if conditions.get("injured"):
            target["pools"]["stamina"]["current"] = 0
        conditions["injured"] = True
    mods = stored["modifiers"]
    events.append({"type": "roll", "actor": actor, "role": "deflection", "attribute": "Deflection",
                   "method": "deflect injurious blow", "target": check["stat"], "check": check,
                   "advantage_sources": [], "disadvantage_sources": mods["disadvantage_sources"],
                   "pressure_at_start": mods["level"], "seed": stored.get("seed"),
                   "luck_spent": abs(nudge) if not fund else 0,
                   "luck_current": target["pools"]["luck"]["current"]})
    result = {**stored["result"], "pending": False, "deflection": check,
              "injured": bool(target.get("conditions", {}).get("injured")),
              "stamina": target["pools"]["stamina"]["current"]}
    tracker["pending_action"] = None
    return result, events


def start_combat(tracker: dict, sheets: dict, sides: dict[str, list[str]], order: list[str] | None = None) -> dict:
    ensure_ready(tracker)
    if tracker.get("combat", {}).get("active"):
        raise ValueError("combat already active; initiative holds until combat ends")
    members = [m for group in sides.values() for m in group]
    if len(sides) < 2 or not members or len(set(members)) != len(members) or any(not g for g in sides.values()):
        raise ValueError("give at least two nonempty, disjoint combat sides")
    for member in members:
        entity(member, sheets, tracker)
    rolls = []
    if order:
        if set(order) != set(sides) or len(order) != len(sides):
            raise ValueError("fictional initiative order must name every side once")
    else:
        # Re-roll tied groups only; preserve the order already established.
        groups = [list(sides)]
        while any(len(group) > 1 for group in groups):
            expanded = []
            for group in groups:
                if len(group) == 1:
                    expanded.append(group)
                    continue
                draw = {side: random.randint(1, 20) for side in group}
                rolls.append(draw)
                expanded.extend([[s for s in group if draw[s] == score] for score in sorted(set(draw.values()), reverse=True)])
            groups = expanded
        order = [group[0] for group in groups]
    tracker["combat"] = {"active": True, "round": 1, "sides": sides, "order": order,
                         "initiative_rolls": rolls, "acted": [],
                         "positions": {member: "steady" for member in members}}
    return {"type": "combat_start", **deepcopy(tracker["combat"])}


def set_positions(tracker: dict, sheets: dict, positions: dict[str, str], *, next_round: bool = False) -> dict:
    ensure_ready(tracker)
    combat = tracker.get("combat", {})
    if not combat.get("active"):
        raise ValueError("no active combat")
    if next_round:
        waiting = [m for group in combat["sides"].values() for m in group
                   if m not in combat["acted"] and entity(m, sheets, tracker)["pools"]["stamina"]["current"] > 0]
        if waiting:
            raise ValueError("record each remaining action or use pass before the next round")
        combat["round"] += 1
        combat["acted"] = []
        combat["positions"] = {member: "steady" for member in combat["positions"]}
    elif combat["acted"]:
        raise ValueError("positions are held for the whole round")
    for actor, stance in positions.items():
        if actor not in combat["positions"] or stance not in {"steady", "vanguard", "watchful", "ranged"}:
            raise ValueError("invalid actor or position")
        if stance == "vanguard" and entity(actor, sheets, tracker).get("conditions", {}).get("injured"):
            raise ValueError("an Injured character cannot use Vanguard")
        combat["positions"][actor] = stance
    return {"type": "combat_round", "round": combat["round"], "order": combat["order"],
            "positions": deepcopy(combat["positions"])}
