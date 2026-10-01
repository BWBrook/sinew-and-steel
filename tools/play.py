#!/usr/bin/env python3
"""Headless campaign actions, with atomic state and telemetry receipts."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import sys
import uuid

import _play
import _pressure
import _resources
import _runtime
import _sslib


def pairs(items: list[str]) -> dict[str, str]:
    result = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"expected KEY=VALUE: {item}")
        key, value = item.split("=", 1)
        if not key or key in result:
            raise ValueError(f"empty or repeated key: {key}")
        result[key] = value
    return result


def parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--campaign", help="Campaign slug or absolute directory")
    global_parser.add_argument("--character", help="Character sheet filename stem")
    global_parser.add_argument("--seed", type=int)
    global_parser.add_argument("--event-id", help="Stable ID for safe retries; reuse only for the same request")
    global_parser.add_argument("--dry-run", action="store_true")
    global_parser.add_argument("--json", action="store_true")
    commands = argparse.ArgumentParser(description=__doc__, parents=[global_parser])
    sub = commands.add_subparsers(dest="command", required=True)

    def nudge_options(p):
        p.add_argument("--nudge", type=int, default=0, help="Signed change to a kept die; pay abs(N) Luck")
        p.add_argument("--nudge-target", choices=["attacker", "defender"], default="attacker")
        p.add_argument("--payer", help="Actor paying for the nudge (defaults to attacker)")
        p.add_argument("--companionship", action="store_true", help="Use one Companionship token for a one-point nudge")
        p.add_argument("--deflection-nudge", type=int, default=0)
        p.add_argument("--deflection-toll", choices=["luck", "pressure"], help="Choose a separate toll for a forthcoming Deflection test")

    def action_costs(p):
        p.add_argument("--luck-cost", type=int, default=0, help="Declared base cost, excluding automatic Pressure tolls")
        p.add_argument("--pressure-cost", type=int, default=0, help="Declared base cost, excluding automatic Pressure tolls")
        p.add_argument("--toll", choices=["luck", "pressure"], help="Choice for an active risky-test toll")
        p.add_argument("--use-resource", help="Record an eligible limited ability in the same action")

    for name in ("check", "opposed", "attack"):
        p = sub.add_parser(name, help=f"Resolve a {name} with current state")
        p.add_argument("--actor", help="Override --character; NPC IDs use npc:NAME")
        p.add_argument("--attribute", required=True)
        p.add_argument("--method", required=True)
        p.add_argument("--stakes", required=True)
        p.add_argument("--context", action="append", default=[], help="Fictional context; risky is always included")
        p.add_argument("--adv-source", action="append", default=[])
        p.add_argument("--dis-source", action="append", default=[])
        p.add_argument("--failure-pressure", type=int, default=0)
        p.add_argument("--defer", action="store_true", help="Persist raw dice, then use settle after reading them")
        action_costs(p)
        if name != "check":
            p.add_argument("--opponent", required=True, help="Sheet stem or npc:NAME")
            p.add_argument("--defender-attribute")
            p.add_argument("--defender-context", action="append", default=[])
            p.add_argument("--defender-adv-source", action="append", default=[])
            p.add_argument("--defender-dis-source", action="append", default=[])
            p.add_argument("--defender-toll", choices=["luck", "pressure"])
        if name == "attack":
            p.add_argument("--edge", type=int, default=0)
            p.add_argument("--soak", type=int, default=0)
            p.add_argument("--injury", action="store_true", help="Twilight optional Injury module")
            p.add_argument("--gritty", action="store_true", help="Also check Injury at effective margin 8")
            p.add_argument("--undefended", action="store_true", help="The declared fiction makes defence impossible")
    p = sub.add_parser("settle", help="Finish a persisted raw roll after choosing any nudge")
    nudge_options(p)
    p.add_argument("--adjust", action="append", default=[], metavar="PAYER=SIDE:DELTA",
                   help="Repeatable Luck adjustment; SIDE is attacker or defender, each entry costs abs(DELTA)")

    p = sub.add_parser("pressure", help="Gain, purge, or record and reset a crisis")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--gain", type=int)
    group.add_argument("--purge", type=int)
    group.add_argument("--crisis", action="store_true")
    p.add_argument("--source", required=True, help="Cause, or the adjudicated crisis consequence")
    p.add_argument("--category", choices=["action_cost", "failure", "ambient"], default="ambient")
    p.add_argument("--target", help="Crisis target, required when no individual tipped the track")
    p.add_argument("--table-result", type=int, action="append", help="Chosen/rolled d6 outcome (repeatable)")
    p.add_argument("--effect", action="append", default=[], help="Lasting crisis effect DESCRIPTION=DURATION")

    p = sub.add_parser("effect-end", help="Record expiry of a crisis-created effect")
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p = sub.add_parser("beat", help="Record one narrative beat; a beat is not an individual roll")
    p.add_argument("--perilous", action="store_true")
    p.add_argument("--label", required=True)
    p = sub.add_parser("scene", help="Begin a scene and reset its limited uses")
    p.add_argument("--label", required=True)
    p = sub.add_parser("session", help="Begin a session; preserve Pressure and reset session use limits")
    p.add_argument("--label", default="New session")
    p = sub.add_parser("session-close", help="Mark a completed session for playtest metrics")
    p.add_argument("--label", required=True)
    p = sub.add_parser("boundary", help="Reset port/camp limited uses when the fiction permits")
    p.add_argument("--kind", choices=["port", "camp"], required=True)
    p.add_argument("--reason", required=True)

    p = sub.add_parser("luck", help="Record Luck spent/recovered outside a roll")
    p.add_argument("--amount", type=int, required=True)
    p.add_argument("--source", required=True)
    p = sub.add_parser("stamina", help="Record adjudicated harm/healing outside an attack")
    p.add_argument("--amount", type=int, required=True)
    p.add_argument("--source", required=True)
    p = sub.add_parser("condition", help="Record or clear a fictional condition")
    p.add_argument("--name", required=True)
    p.add_argument("--clear", action="store_true")
    p.add_argument("--source", required=True)
    p = sub.add_parser("resource", help="Use or restore an adjudicated skin resource")
    p.add_argument("--name", required=True)
    p.add_argument("--amount", type=int, default=1)
    p.add_argument("--recover", action="store_true")
    p.add_argument("--purpose")
    p.add_argument("--source", required=True)
    action_costs(p)
    p = sub.add_parser("clock", help="Change a non-Pressure clock")
    p.add_argument("--name", required=True)
    p.add_argument("--amount", type=int, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--max", type=int, help="Required to create a new clock")

    p = sub.add_parser("npc", help="Add an NPC statline for repeatable conflict resolution")
    p.add_argument("--id", required=True)
    p.add_argument("--name")
    p.add_argument("--stat", action="append", required=True, help="ATTRIBUTE=N (repeatable)")
    p.add_argument("--stamina", type=int, required=True)
    p.add_argument("--luck", type=int, default=0)
    p = sub.add_parser("combat-start", help="Set the fight's side order once")
    p.add_argument("--side", action="append", required=True, help="SIDE=actor,actor")
    p.add_argument("--order", help="Comma-separated side order already established by the fiction")
    p = sub.add_parser("positions", help="Declare Twilight positions before anyone acts")
    p.add_argument("--position", action="append", required=True, help="ACTOR=steady|vanguard|watchful|ranged")
    p = sub.add_parser("round", help="Begin the next round, keeping initiative")
    p.add_argument("--position", action="append", default=[])
    p = sub.add_parser("pass", help="Record a turn used for a non-attack action")
    p.add_argument("--actor", help="Sheet stem or npc:NAME")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("combat-end", help="Close a combat")
    p.add_argument("--reason", required=True)
    sub.add_parser("status", help="Private structured campaign state (read only)")
    return global_parser, commands


def dispatch(args, campaign: dict, skin: dict, tracker: dict, sheets: dict) -> tuple[dict, list[dict]]:
    actors = list(sheets)
    command = args.command
    if command == "status":
        return {"campaign": campaign, "tracker": tracker, "characters": sheets}, []
    if tracker.get("session_closed") and command != "session":
        raise ValueError("session is closed; begin a new session before changing state")
    if command in {"check", "opposed", "attack"}:
        actor = args.actor or _runtime.actor_key(args.character, sheets)
        keys = {"attribute", "method", "stakes", "opponent", "defender_attribute", "toll", "defender_toll",
                "luck_cost", "pressure_cost", "failure_pressure", "use_resource", "edge", "soak", "injury", "gritty", "undefended"}
        options = {key: getattr(args, key) for key in keys if hasattr(args, key)}
        options.update(contexts=args.context, adv_sources=args.adv_source, dis_sources=args.dis_source,
                       defender_contexts=getattr(args, "defender_context", []),
                       defender_adv_sources=getattr(args, "defender_adv_source", []),
                       defender_dis_sources=getattr(args, "defender_dis_source", []))
        action, events = _play.prepare_action(tracker, sheets, skin, kind=command, actor=actor, **options)
        tracker["pending_action"]["seed"] = args.seed
        if args.defer:
            return {"pending": True, "action": tracker["pending_action"]}, events + [{"type": "raw_roll", "action": action}]
        # A failed settlement must not erase a roll that has already happened.
        # Keep the raw action (and its paid upfront costs) for a corrected settle.
        next_tracker, next_sheets = deepcopy(tracker), deepcopy(sheets)
        try:
            result, final_events = _play.finish_action(next_tracker, next_sheets, skin, seed=args.seed)
        except (ValueError, KeyError, TypeError) as exc:
            return {"pending": True, "action": tracker["pending_action"], "settlement_error": str(exc)}, events + [{"type": "raw_roll", "action": action}]
        tracker.clear()
        tracker.update(next_tracker)
        sheets.clear()
        sheets.update(next_sheets)
        return result, events + final_events
    if command == "settle":
        adjustments = []
        for item in args.adjust:
            who, separator, change = item.partition("=")
            side, colon, delta = change.partition(":")
            if not who or not separator or not colon or side not in {"attacker", "defender"}:
                raise ValueError(f"expected PAYER=attacker|defender:DELTA for --adjust: {item}")
            try:
                amount = int(delta)
            except ValueError as exc:
                raise ValueError(f"--adjust DELTA must be an integer: {item}") from exc
            adjustments.append((who, side, amount))
        return _play.finish_action(tracker, sheets, skin, nudge=args.nudge,
            nudge_target=args.nudge_target, payer=args.payer, companionship=args.companionship,
            deflection_nudge=args.deflection_nudge, seed=args.seed, deflection_toll=args.deflection_toll,
            adjustments=adjustments)
    _play.ensure_ready(tracker, allow_crisis=command in {"pressure", "effect-end", "luck", "stamina", "condition", "resource", "clock"})
    actor = _runtime.actor_key(args.character, sheets) if args.character else None
    if command == "pressure":
        if skin.get("pressure_scope") == "character" and actor is None:
            actor = _runtime.actor_key(None, sheets)
        if args.crisis:
            _, track = _pressure.track_for(tracker["pressure"], actor)
            target = args.target or track["tipper"]
            if not target:
                raise ValueError("a shared hazard needs an explicit --target for its crisis")
            # The Custodian supplies table outcomes so recursive 'roll twice'
            # consequences can be adjudicated before committing the reset.
            if not args.table_result:
                raise ValueError("supply --table-result and the adjudicated --source before resetting")
            effects = [{"description": key, "duration": value} for key, value in pairs(args.effect).items()]
            events = _pressure.crisis(tracker["pressure"], skin, actors, target=target,
                table_result=args.table_result, description=args.source, effects=effects, actor=actor)
        else:
            amount = args.gain if args.gain is not None else args.purge
            if amount is None or amount < 0:
                raise ValueError("gain/purge amount must be nonnegative")
            events = _pressure.change(tracker["pressure"], skin, actors,
                amount=amount if args.gain is not None else -amount,
                source=args.source, category=args.category if args.gain is not None else "purge", actor=actor)
        return {"pressure": tracker["pressure"]}, events
    if command == "effect-end":
        event = _pressure.clear_effect(tracker["pressure"], args.id, args.reason)
        return event, [event]
    if command == "session-close":
        tracker["session_closed"] = True
        event = {"type": "session_end", "label": args.label,
                 "luck": {k: v["pools"]["luck"]["current"] for k, v in sheets.items()}}
        return event, [event]
    if command in {"beat", "scene", "session", "boundary"}:
        if command == "beat":
            tracker["beat"] = tracker.get("beat", 0) + 1
            event = {"type": "beat", "perilous": args.perilous, "label": args.label,
                     "luck": {k: v["pools"]["luck"]["current"] for k, v in sheets.items()}}
        else:
            boundary = args.kind if command == "boundary" else command
            tracker["resources"] = _resources.reset_resources(tracker["resources"], boundary)
            if command == "session":
                if not tracker.get("session_closed"):
                    raise ValueError("close the current session before beginning another")
                tracker["session"] = tracker.get("session", 1) + 1
                tracker["beat"] = 0
                tracker["session_closed"] = False
                tracker["telemetry_partial"] = False
            if command in {"scene", "session"}:
                tracker["scene"] = tracker.get("scene", 0) + 1
            event = {"type": command, "label": getattr(args, "label", None), "boundary": boundary}
        return event, [event]
    if command == "luck":
        actor = actor or _runtime.actor_key(None, sheets)
        event = _runtime.luck_change(sheets[actor], args.amount, actor=actor,
            source=args.source, category="recovery" if args.amount >= 0 else "spend")
        return event, [event]
    if command == "stamina":
        actor = actor or _runtime.actor_key(None, sheets)
        pool = sheets[actor]["pools"]["stamina"]
        before = pool["current"]
        pool["current"] = min(pool["max"], max(0, before + args.amount))
        event = {"type": "stamina", "actor": actor, "source": args.source,
                 "before": before, "after": pool["current"]}
        return event, [event]
    if command == "condition":
        actor = actor or _runtime.actor_key(None, sheets)
        sheets[actor].setdefault("conditions", {})[args.name] = not args.clear
        event = {"type": "condition", "actor": actor, "condition": args.name,
                 "active": not args.clear, "source": args.source}
        return event, [event]
    if command == "resource":
        if args.luck_cost < 0 or args.pressure_cost < 0:
            raise ValueError("resource costs must be nonnegative")
        if args.use_resource:
            raise ValueError("resource uses --name; --use-resource belongs to roll actions")
        definition = skin.get("resources", {}).get(args.name, {})
        if (definition.get("scope") == "character" or args.luck_cost or args.pressure_cost) and actor is None:
            actor = _runtime.actor_key(None, sheets)
        if args.recover:
            tracker["resources"], event = _resources.recover_resource(tracker["resources"], skin, args.name, actor, args.amount)
        else:
            tracker["resources"], event = _resources.use_resource(tracker["resources"], skin, args.name, actor, args.amount, purpose=args.purpose)
        events = [{"type": "resource", **event, "source": args.source}]
        pressure = args.pressure_cost + event.get("pressure_gain", 0)
        if pressure:
            events += _pressure.change(tracker["pressure"], skin, actors,
                amount=pressure, source=args.source, category="action_cost", actor=actor)
        if args.luck_cost:
            events.append(_runtime.luck_change(sheets[actor], -args.luck_cost, actor=actor,
                source=args.source, category="action_cost"))
        return event, events
    if command == "clock":
        if args.name == "pressure":
            raise ValueError("Pressure is structured state; use the pressure command")
        clocks = tracker.setdefault("clocks", {})
        if args.name not in clocks:
            if args.max is None or args.max < 1:
                raise ValueError("a new clock needs a positive --max")
            clocks[args.name] = {"name": args.name, "current": 0, "max": args.max}
        clock = clocks[args.name]
        before = clock["current"]
        clock["current"] = min(clock["max"], max(0, before + args.amount))
        event = {"type": "clock", "clock": args.name, "source": args.source,
                 "before": before, "after": clock["current"], "maximum": clock["max"]}
        return event, [event]
    if command == "npc":
        if args.id in tracker.get("npcs", {}) or args.id in sheets or args.stamina < 1 or args.luck < 0:
            raise ValueError("NPC needs a new ID and valid Stamina/Luck")
        if not args.id or ":" in args.id or "/" in args.id:
            raise ValueError("invalid NPC ID")
        attributes = {key: int(value) for key, value in pairs(args.stat).items()}
        npc = {"name": args.name or args.id, "attributes": attributes,
               "pools": {"stamina": {"current": args.stamina, "max": args.stamina},
                         "luck": {"current": args.luck, "max": args.luck}}, "conditions": {}}
        tracker.setdefault("npcs", {})[args.id] = npc
        return {"npc": f"npc:{args.id}", "sheet": npc}, [{"type": "npc_added", "npc": args.id}]
    if command == "combat-start":
        sides = {key: value.split(",") for key, value in pairs(args.side).items()}
        event = _play.start_combat(tracker, sheets, sides, args.order.split(",") if args.order else None)
    elif command in {"positions", "round"}:
        if args.position and campaign["skin"] != "twilight_of_the_northlands":
            raise ValueError("combat positions are the optional Twilight module")
        event = _play.set_positions(tracker, sheets, pairs(args.position), next_round=command == "round")
    elif command == "pass":
        who = args.actor or actor or _runtime.actor_key(None, sheets)
        combat = tracker.get("combat", {})
        if not combat.get("active") or who not in combat["positions"] or who in combat["acted"]:
            raise ValueError("combatant has no unused action in an active combat")
        combat["acted"].append(who)
        event = {"type": "combat_action", "actor": who, "reason": args.reason}
    elif command == "combat-end":
        if not tracker.get("combat", {}).get("active"):
            raise ValueError("no active combat")
        tracker["combat"]["active"] = False
        event = {"type": "combat_end", "reason": args.reason}
    else:
        raise ValueError(f"unknown command: {command}")
    return event, [event]


def main(argv: list[str] | None = None) -> int:
    globals_parser, commands = parser()
    args_list = sys.argv[1:] if argv is None else argv
    global_args, remaining = globals_parser.parse_known_args(args_list)
    command_args = commands.parse_args(remaining)
    args = argparse.Namespace(**(vars(command_args) | vars(global_args)))
    if not args.campaign:
        commands.error("--campaign is required")
    root = _sslib.repo_root()
    directory = _sslib.campaign_dir(args.campaign, root=root)
    request = vars(args).copy()
    try:
        with _runtime.campaign_lock(directory, dry_run=args.dry_run or args.command == "status"):
            if args.event_id and args.command != "status":
                receipt = _runtime.replay_receipt(directory, args.event_id, request)
                if receipt:
                    print(json.dumps(receipt, indent=2))
                    return 0
            campaign, skin, tracker, sheets = _runtime.load_campaign(directory, root)
            before_luck = {key: value["pools"]["luck"]["current"] for key, value in sheets.items()}
            before_pressure = deepcopy(tracker["pressure"])
            errors = _pressure.validate_pressure(tracker["pressure"], skin, list(sheets))
            errors += _resources.validate_resources(tracker.get("resources"), skin, list(sheets))
            if errors:
                raise ValueError("; ".join(errors))
            if args.seed is not None:
                random.seed(args.seed)
            result, events = dispatch(args, campaign, skin, tracker, sheets)
            if args.command == "status":
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 0
            errors = _pressure.validate_pressure(tracker["pressure"], skin, list(sheets))
            errors += _resources.validate_resources(tracker["resources"], skin, list(sheets))
            if errors:
                raise ValueError("; ".join(errors))
            receipt = _runtime.commit_campaign(directory, campaign, tracker, sheets, events, result,
                request=request, event_id=args.event_id or uuid.uuid4().hex, dry_run=args.dry_run,
                initial_luck=before_luck, initial_pressure=before_pressure)
            print(json.dumps(receipt, indent=2, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
