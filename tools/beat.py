#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml

import _dice
import _sslib
import recap
import session_log


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_kv(item: str) -> tuple[str, str]:
    if "=" not in item:
        raise ValueError(f"Expected key=value, got '{item}'")
    key, value = item.split("=", 1)
    return key.strip(), value.strip()


def parse_value(value: str):
    try:
        return yaml.safe_load(value)
    except Exception:
        return value


def format_check_log(label: str | None, check: dict[str, Any]) -> str:
    prefix = f"{label}: " if label else ""
    rolls = check.get("rolls")
    stat = check.get("stat")
    adv = check.get("adv")
    dis = check.get("dis")
    mode = "Adv" if adv else "Dis" if dis else "Straight"

    raw_result = check.get("raw_result", check.get("result"))
    result = check.get("result")
    nudge = check.get("nudge", 0)
    final_success = check.get("success", check.get("final_success"))
    final_margin = check.get("margin", check.get("final_margin"))

    base = f"{prefix}{mode} roll-under: stat={stat} rolls={rolls} -> {raw_result}"
    if nudge:
        base += f" nudge={nudge} -> {result}"

    base += f" => {'success' if final_success else 'fail'} (margin {final_margin})"
    return base


def resolve_roll(args, sheet: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if args.command == "check":
        if args.adv and args.dis:
            raise ValueError("choose only one of --adv or --dis")

        stat_value = args.stat
        if stat_value is None and args.stat_key:
            attrs = sheet.get("attributes")
            if not isinstance(attrs, dict) or args.stat_key not in attrs:
                raise ValueError(f"stat-key not found on sheet: {args.stat_key}")
            stat_value = int(attrs[args.stat_key])
        if stat_value is None:
            raise ValueError("provide --stat or --stat-key")

        check_roll = _dice.resolve_check(stat_value, adv=args.adv, dis=args.dis)
        if args.nudge:
            check_roll = _dice.apply_nudge_to_check(check_roll, args.nudge)
        check_roll["label"] = args.label
        check_roll["stat_key"] = args.stat_key
        return check_roll, bool(check_roll.get("success", check_roll.get("final_success")))

    if args.adv_attacker and args.dis_attacker:
        raise ValueError("choose only one of --adv-attacker or --dis-attacker")
    if args.adv_defender and args.dis_defender:
        raise ValueError("choose only one of --adv-defender or --dis-defender")

    attacker_value = args.attacker
    if attacker_value is None and args.attacker_key:
        attrs = sheet.get("attributes")
        if not isinstance(attrs, dict) or args.attacker_key not in attrs:
            raise ValueError(f"attacker-key not found on sheet: {args.attacker_key}")
        attacker_value = int(attrs[args.attacker_key])
    if attacker_value is None:
        raise ValueError("provide --attacker or --attacker-key")

    roll_payload = _dice.resolve_opposed(
        attacker_value,
        args.defender,
        adv_attacker=args.adv_attacker,
        dis_attacker=args.dis_attacker,
        adv_defender=args.adv_defender,
        dis_defender=args.dis_defender,
    )
    if args.nudge:
        target = args.nudge_target
        roll_payload[target] = _dice.apply_nudge_to_check(roll_payload[target], args.nudge)
    roll_payload["outcome"] = _dice.resolve_opposed_outcome(
        roll_payload["attacker"], roll_payload["defender"]
    )
    roll_payload["label"] = args.label
    roll_payload["attacker_key"] = args.attacker_key
    roll_payload["as"] = args.as_role
    return roll_payload, roll_payload["outcome"]["winner"] == args.as_role


def spend_luck(args, sheet: dict[str, Any], roll_payload: dict[str, Any]) -> None:
    if not args.nudge:
        return

    if args.nudge_spend == "none":
        spend_side = None
    elif args.nudge_spend == "as":
        spend_side = "attacker" if args.command == "check" else args.as_role
    else:
        spend_side = args.nudge_spend

    if args.command == "check" and spend_side == "defender":
        raise ValueError("--nudge-spend defender is invalid for check rolls")
    if spend_side is not None and args.command == "opposed" and spend_side != args.as_role:
        print(
            f"warning: nudge spend side '{spend_side}' does not match your role '{args.as_role}'; "
            "no luck spent",
            file=sys.stderr,
        )
        roll_payload["nudge_spend"] = spend_side
        return

    if spend_side is not None:
        luck_cost = abs(args.nudge)
        pools = sheet.get("pools")
        if not isinstance(pools, dict):
            raise KeyError("pools missing from sheet")
        luck = pools.get("luck")
        if not isinstance(luck, dict):
            raise KeyError("pools.luck missing from sheet")
        current_luck = luck.get("current")
        if not is_int(current_luck):
            raise TypeError("pools.luck.current is not int")
        if current_luck < luck_cost:
            raise ValueError(f"not enough luck tokens: need {luck_cost}, have {current_luck}")
        luck["current"] = current_luck - luck_cost
        roll_payload["luck_spent"] = luck_cost
    roll_payload["nudge_spend"] = spend_side or "none"


def parse_operations(items: list[str]) -> list[tuple[str, Any]]:
    operations = []
    for item in items:
        key, value = parse_kv(item)
        operations.append((key, parse_value(value)))
    return operations


def apply_state_changes(args, sheet: dict[str, Any], tracker: dict[str, Any], success: bool) -> tuple[list[str], list[str]]:
    if success:
        sheet_sets = parse_operations(args.success_sheet_set)
        sheet_incs = parse_operations(args.success_sheet_inc)
        tracker_sets = parse_operations(args.success_tracker_set)
        tracker_incs = parse_operations(args.success_tracker_inc)
    else:
        sheet_sets = parse_operations(args.failure_sheet_set)
        sheet_incs = parse_operations(args.failure_sheet_inc)
        tracker_sets = parse_operations(args.failure_tracker_set)
        tracker_incs = parse_operations(args.failure_tracker_inc)

    sheet_changed: list[str] = []
    tracker_changed: list[str] = []
    allow_new = bool(args.allow_new)
    for key, value in sheet_sets:
        _sslib.set_path(sheet, key, value, allow_new=allow_new, allow_clock=False)
        sheet_changed.append(key)
    for key, delta in sheet_incs:
        if not isinstance(delta, (int, float)):
            raise TypeError(f"delta for {key} is not numeric")
        _sslib.inc_path(sheet, key, int(delta), allow_new=allow_new, allow_clock=False)
        sheet_changed.append(key)

    for key, value in tracker_sets:
        _sslib.set_path(tracker, key, value, allow_new=allow_new, allow_clock=True)
        tracker_changed.append(key)
    for key, delta in tracker_incs:
        if not isinstance(delta, (int, float)):
            raise TypeError(f"delta for {key} is not numeric")
        _sslib.inc_path(tracker, key, int(delta), allow_new=allow_new, allow_clock=True)
        tracker_changed.append(key)

    if args.scene_inc:
        tracker["scene"] = int(tracker.get("scene", 0)) + args.scene_inc
        tracker_changed.append("scene")
    if args.pressure_inc:
        _sslib.inc_path(
            tracker,
            "clocks.pressure.current",
            int(args.pressure_inc),
            allow_new=False,
            allow_clock=True,
        )
        tracker_changed.append("clocks.pressure.current")
    for item in args.clock_inc:
        name, value = parse_kv(item)
        _sslib.inc_path(
            tracker,
            f"clocks.{name}.current",
            int(value),
            allow_new=False,
            allow_clock=True,
        )
        tracker_changed.append(f"clocks.{name}.current")

    _sslib.clamp_currents(sheet, sheet_changed)
    _sslib.clamp_currents(tracker, tracker_changed)
    return sheet_changed, tracker_changed


def main() -> int:
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    global_parser.add_argument("--character", help="Character slug or filename")
    global_parser.add_argument("--seed", type=int, help="Random seed")

    global_parser.add_argument("--label", help="Short label for this roll (logged)")
    global_parser.add_argument(
        "--nudge", type=int, default=0, help="Nudge the chosen die result by N (costs |N| luck tokens)"
    )
    global_parser.add_argument(
        "--nudge-target",
        choices=["attacker", "defender"],
        default="attacker",
        help="For opposed rolls, which side to nudge",
    )
    global_parser.add_argument(
        "--nudge-spend",
        choices=["as", "attacker", "defender", "none"],
        default="as",
        help="Which side pays luck for a nudge (default: as_role). Use 'none' to skip spending.",
    )

    global_parser.add_argument("--scene-inc", type=int, default=0, help="Increment tracker scene counter")
    global_parser.add_argument("--pressure-inc", type=int, default=0, help="Increment tracker pressure clock")
    global_parser.add_argument("--clock-inc", action="append", default=[], help="Increment clock: name=delta")

    global_parser.add_argument("--success-sheet-set", action="append", default=[])
    global_parser.add_argument("--success-sheet-inc", action="append", default=[])
    global_parser.add_argument("--failure-sheet-set", action="append", default=[])
    global_parser.add_argument("--failure-sheet-inc", action="append", default=[])

    global_parser.add_argument("--success-tracker-set", action="append", default=[])
    global_parser.add_argument("--success-tracker-inc", action="append", default=[])
    global_parser.add_argument("--failure-tracker-set", action="append", default=[])
    global_parser.add_argument("--failure-tracker-inc", action="append", default=[])

    global_parser.add_argument("--log", action="store_true", help="Append roll details to campaign session log")
    global_parser.add_argument("--log-role", default="System", help="Role label for log entries")
    global_parser.add_argument("--recap", action="append", default=[], help="Add a memory summary line (repeatable)")
    global_parser.add_argument("--thread", action="append", default=[])
    global_parser.add_argument("--npc", action="append", default=[])
    global_parser.add_argument("--secret", action="append", default=[])

    global_parser.add_argument("--out-roll", help="Write roll JSON to this file")
    global_parser.add_argument("--json", action="store_true", help="Print roll JSON")
    global_parser.add_argument("--allow-new", action="store_true", help="Allow creating new keys when updating state")
    global_parser.add_argument("--dry-run", action="store_true", help="Compute changes but do not write files")

    command_parser = argparse.ArgumentParser(description="One-command roll + state update + logging for a beat.")
    subparsers = command_parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Single roll-under check")
    check.add_argument("--stat", type=int, help="Stat value")
    check.add_argument("--stat-key", help="Stat key to read from sheet attributes")
    check.add_argument("--adv", action="store_true")
    check.add_argument("--dis", action="store_true")

    opposed = subparsers.add_parser("opposed", help="Opposed roll-under check")
    opposed.add_argument("--as", dest="as_role", choices=["attacker", "defender"], default="attacker")
    opposed.add_argument("--attacker", type=int, help="Attacker stat")
    opposed.add_argument("--attacker-key", help="Attacker stat key from sheet")
    opposed.add_argument("--defender", type=int, required=True, help="Defender stat")
    opposed.add_argument("--adv-attacker", action="store_true")
    opposed.add_argument("--dis-attacker", action="store_true")
    opposed.add_argument("--adv-defender", action="store_true")
    opposed.add_argument("--dis-defender", action="store_true")

    global_args, remaining = global_parser.parse_known_args()
    command_args = command_parser.parse_args(remaining)
    merged = vars(global_args).copy()
    merged.update(vars(command_args))
    args = argparse.Namespace(**merged)

    if not args.campaign:
        print("error: provide --campaign", file=sys.stderr)
        return 1

    if args.seed is not None:
        import random

        random.seed(args.seed)

    root = _sslib.repo_root()

    # Resolve campaign paths
    cfile = _sslib.campaign_file(args.campaign, root=root)
    if not cfile.exists():
        print(f"error: campaign not found: {cfile}", file=sys.stderr)
        return 1

    sheet_path = _sslib.resolve_character_file(
        _sslib.campaign_characters_dir(args.campaign, root=root),
        args.character,
    )
    tracker_path = _sslib.campaign_trackers_dir(args.campaign, root=root) / "session.yaml"

    sheet = _sslib.load_yaml(sheet_path)
    tracker = _sslib.load_yaml(tracker_path)

    try:
        roll_payload, success = resolve_roll(args, sheet)
        roll_payload["schema_version"] = 1
        roll_payload["tool_version"] = _sslib.repo_version(root)
        roll_payload["seed"] = args.seed
        spend_luck(args, sheet, roll_payload)
        sheet_changed, tracker_changed = apply_state_changes(args, sheet, tracker, success)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        _sslib.save_yaml(sheet_path, sheet)
        _sslib.save_yaml(tracker_path, tracker)

    # Logging / recap
    if args.log and not args.dry_run:
        logs_dir = _sslib.campaign_logs_dir(args.campaign, root=root)
        log_path = session_log.find_latest_log(logs_dir) or session_log.next_log_path(logs_dir)
        if args.command == "check":
            log_line = format_check_log(args.label, roll_payload)
        else:
            a_line = format_check_log("attacker", roll_payload["attacker"])
            d_line = format_check_log("defender", roll_payload["defender"])
            out = roll_payload.get("outcome", {})
            log_line = (args.label + ": " if args.label else "") + a_line + " | " + d_line
            log_line += f" | outcome={out.get('winner')} ({out.get('reason')})"
        session_log.append_log(log_path, args.log_role, log_line)

    if (args.recap or args.thread or args.npc or args.secret) and not args.dry_run:
        memory_dir = _sslib.campaign_memory_dir(args.campaign, root=root)
        memory_path = recap.find_latest_session(memory_dir) or recap.next_session_path(memory_dir)
        recap.append_recap(memory_path, args.recap, args.thread, args.npc, args.secret)

    # Output
    if args.out_roll and not args.dry_run:
        out_path = Path(args.out_roll)
        if not out_path.is_absolute():
            out_path = root / out_path
        out_path.write_text(json.dumps(roll_payload, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(roll_payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
