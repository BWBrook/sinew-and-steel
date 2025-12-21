#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

import _dice
import _sslib

SESSION_MD_RE = re.compile(r"session_(\d{3})\.md$")
SESSION_YAML_RE = re.compile(r"session_(\d{3})\.ya?ml$")


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


def ensure_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        if value.strip() == "":
            return []
        return [value]
    return [str(value)]


def latest_session_md(logs_dir: Path) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    latest = None
    latest_num = -1
    for p in logs_dir.glob("session_*.md"):
        match = SESSION_MD_RE.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    if latest:
        return latest
    return logs_dir / "session_001.md"


def latest_session_yaml(memory_dir: Path) -> Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    latest = None
    latest_num = -1
    for p in memory_dir.glob("session_*.yaml"):
        match = SESSION_YAML_RE.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    if latest:
        return latest
    return memory_dir / "session_001.yaml"


def append_log(log_path: Path, role: str | None, text: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    header_parts = [timestamp]
    if role:
        header_parts.append(role)
    header = " - ".join(header_parts)

    entry = text.rstrip() + "\n"
    block = f"## {header}\n\n{entry}\n"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(block)


def append_recap(memory_path: Path, summary_lines: list[str], threads: list[str], npcs: list[str], secrets: list[str]) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {}
    if memory_path.exists():
        data = yaml.safe_load(memory_path.read_text(encoding="utf-8")) or {}

    if "schema_version" not in data:
        data["schema_version"] = 1

    summaries = ensure_list(data.get("summary"))
    for line in summary_lines:
        summaries.append(f"[{timestamp}] {line}")

    data["summary"] = summaries
    data["threads"] = ensure_list(data.get("threads")) + threads
    data["npcs"] = ensure_list(data.get("npcs")) + npcs
    data["secrets"] = ensure_list(data.get("secrets")) + secrets

    _sslib.save_yaml(memory_path, data)


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


def opposed_outcome(attacker: dict[str, Any], defender: dict[str, Any]) -> dict[str, str]:
    def final(check):
        return {
            "success": bool(check.get("success", check.get("final_success"))),
            "margin": int(check.get("margin", check.get("final_margin"))),
        }

    a = final(attacker)
    d = final(defender)

    outcome = {"winner": None, "reason": None}

    if a["success"] and not d["success"]:
        outcome["winner"] = "attacker"
        outcome["reason"] = "attacker_success_only"
    elif d["success"] and not a["success"]:
        outcome["winner"] = "defender"
        outcome["reason"] = "defender_success_only"
    elif a["success"] and d["success"]:
        if a["margin"] > d["margin"]:
            outcome["winner"] = "attacker"
            outcome["reason"] = "higher_margin"
        elif d["margin"] > a["margin"]:
            outcome["winner"] = "defender"
            outcome["reason"] = "higher_margin"
        else:
            outcome["winner"] = "defender"
            outcome["reason"] = "tie_margins_defender"
    else:
        outcome["winner"] = "defender"
        outcome["reason"] = "both_failed_defender"

    return outcome


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

    # Roll
    roll_payload: dict[str, Any]

    if args.command == "check":
        if args.adv and args.dis:
            print("error: choose only one of --adv or --dis", file=sys.stderr)
            return 1

        stat_value = args.stat
        if stat_value is None and args.stat_key:
            attrs = sheet.get("attributes")
            if not isinstance(attrs, dict) or args.stat_key not in attrs:
                print(f"error: stat-key not found on sheet: {args.stat_key}", file=sys.stderr)
                return 1
            stat_value = int(attrs[args.stat_key])

        if stat_value is None:
            print("error: provide --stat or --stat-key", file=sys.stderr)
            return 1

        check_roll = _dice.resolve_check(stat_value, adv=args.adv, dis=args.dis)

        if args.nudge:
            try:
                check_roll = _dice.apply_nudge_to_check(check_roll, args.nudge)
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

        success = bool(check_roll.get("success", check_roll.get("final_success")))
        roll_payload = check_roll
        roll_payload["label"] = args.label
        roll_payload["stat_key"] = args.stat_key

    else:
        if args.adv_attacker and args.dis_attacker:
            print("error: choose only one of --adv-attacker or --dis-attacker", file=sys.stderr)
            return 1
        if args.adv_defender and args.dis_defender:
            print("error: choose only one of --adv-defender or --dis-defender", file=sys.stderr)
            return 1

        attacker_value = args.attacker
        if attacker_value is None and args.attacker_key:
            attrs = sheet.get("attributes")
            if not isinstance(attrs, dict) or args.attacker_key not in attrs:
                print(f"error: attacker-key not found on sheet: {args.attacker_key}", file=sys.stderr)
                return 1
            attacker_value = int(attrs[args.attacker_key])

        if attacker_value is None:
            print("error: provide --attacker or --attacker-key", file=sys.stderr)
            return 1

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
            try:
                roll_payload[target] = _dice.apply_nudge_to_check(roll_payload[target], args.nudge)
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

        roll_payload["outcome"] = opposed_outcome(roll_payload["attacker"], roll_payload["defender"])
        roll_payload["label"] = args.label
        roll_payload["attacker_key"] = args.attacker_key

        success = roll_payload["outcome"]["winner"] == args.as_role
        roll_payload["as"] = args.as_role

    roll_payload["schema_version"] = 1
    roll_payload["tool_version"] = _sslib.repo_version(root)

    # Spend luck for nudge
    if args.nudge:
        luck_cost = abs(args.nudge)
        try:
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
        except (KeyError, TypeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        roll_payload["luck_spent"] = luck_cost

    # Apply scripted ops
    def parse_list(items):
        out = []
        for item in items:
            key, value = parse_kv(item)
            out.append((key, parse_value(value)))
        return out

    if success:
        sheet_sets = parse_list(args.success_sheet_set)
        sheet_incs = parse_list(args.success_sheet_inc)
        tracker_sets = parse_list(args.success_tracker_set)
        tracker_incs = parse_list(args.success_tracker_inc)
    else:
        sheet_sets = parse_list(args.failure_sheet_set)
        sheet_incs = parse_list(args.failure_sheet_inc)
        tracker_sets = parse_list(args.failure_tracker_set)
        tracker_incs = parse_list(args.failure_tracker_inc)

    sheet_changed: list[str] = []
    tracker_changed: list[str] = []
    allow_new = bool(args.allow_new)
    try:
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

    except (KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Tracker increments
    if args.scene_inc:
        tracker["scene"] = int(tracker.get("scene", 0)) + args.scene_inc

    if args.pressure_inc:
        try:
            _sslib.inc_path(
                tracker,
                "clocks.pressure.current",
                int(args.pressure_inc),
                allow_new=False,
                allow_clock=True,
            )
            tracker_changed.append("clocks.pressure.current")
        except (KeyError, TypeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    for item in args.clock_inc:
        name, value = parse_kv(item)
        delta = int(value)
        try:
            _sslib.inc_path(
                tracker,
                f"clocks.{name}.current",
                delta,
                allow_new=False,
                allow_clock=True,
            )
            tracker_changed.append(f"clocks.{name}.current")
        except (KeyError, TypeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    _sslib.clamp_currents(sheet, sheet_changed)
    _sslib.clamp_currents(tracker, tracker_changed)

    _sslib.save_yaml(sheet_path, sheet)
    _sslib.save_yaml(tracker_path, tracker)

    # Logging / recap
    if args.log:
        log_path = latest_session_md(_sslib.campaign_logs_dir(args.campaign, root=root))
        if args.command == "check":
            log_line = format_check_log(args.label, roll_payload)
        else:
            a_line = format_check_log("attacker", roll_payload["attacker"])
            d_line = format_check_log("defender", roll_payload["defender"])
            out = roll_payload.get("outcome", {})
            log_line = (args.label + ": " if args.label else "") + a_line + " | " + d_line
            log_line += f" | outcome={out.get('winner')} ({out.get('reason')})"
        append_log(log_path, args.log_role, log_line)

    if args.recap or args.thread or args.npc or args.secret:
        memory_path = latest_session_yaml(_sslib.campaign_memory_dir(args.campaign, root=root))
        append_recap(memory_path, args.recap, args.thread, args.npc, args.secret)

    # Output
    if args.out_roll:
        out_path = Path(args.out_roll)
        if not out_path.is_absolute():
            out_path = root / out_path
        out_path.write_text(json.dumps(roll_payload, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(roll_payload, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
