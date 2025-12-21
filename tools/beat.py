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


def ensure_path(data: dict, path: str) -> tuple[dict, str]:
    keys = path.split(".")
    cur = data
    for key in keys[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    return cur, keys[-1]


def set_path(data: dict, path: str, value) -> None:
    parent, key = ensure_path(data, path)
    parent[key] = value


def inc_path(data: dict, path: str, delta: int) -> None:
    parent, key = ensure_path(data, path)
    if key not in parent:
        raise KeyError(f"Missing key '{path}'")
    if not isinstance(parent[key], (int, float)):
        raise TypeError(f"Value at '{path}' is not numeric")
    parent[key] += delta


def clamp_currents(data: dict, paths: list[str]) -> None:
    for path in paths:
        if not path.endswith(".current"):
            continue
        parent_path = path.rsplit(".", 1)[0]
        parent, _ = ensure_path(data, parent_path)
        if not isinstance(parent, dict):
            continue
        if "current" not in parent or "max" not in parent:
            continue
        cur = parent.get("current")
        max_value = parent.get("max")
        if not is_int(cur) or not is_int(max_value):
            continue
        if cur < 0:
            parent["current"] = 0
        elif cur > max_value:
            parent["current"] = max_value


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

    result = check.get("result")
    nudge = check.get("nudge", 0)
    final_result = check.get("final_result", result)
    final_success = check.get("final_success", check.get("success"))
    final_margin = check.get("final_margin", check.get("margin"))

    base = f"{prefix}{mode} roll-under: stat={stat} rolls={rolls} -> {result}"
    if nudge:
        base += f" nudge={nudge} -> {final_result}"

    base += f" => {'success' if final_success else 'fail'} (margin {final_margin})"
    return base


def opposed_outcome(attacker: dict[str, Any], defender: dict[str, Any]) -> dict[str, str]:
    def final(check):
        return {
            "success": bool(check.get("final_success", check.get("success"))),
            "margin": int(check.get("final_margin", check.get("margin"))),
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
    parser = argparse.ArgumentParser(description="One-command roll + state update + logging for a beat.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename")
    parser.add_argument("--seed", type=int, help="Random seed")

    parser.add_argument("--label", help="Short label for this roll (logged)")
    parser.add_argument("--nudge", type=int, default=0, help="Nudge the chosen die result by N (costs |N| luck tokens)")
    parser.add_argument(
        "--nudge-target",
        choices=["attacker", "defender"],
        default="attacker",
        help="For opposed rolls, which side to nudge",
    )

    parser.add_argument("--scene-inc", type=int, default=0, help="Increment tracker scene counter")
    parser.add_argument("--pressure-inc", type=int, default=0, help="Increment tracker pressure clock")
    parser.add_argument("--clock-inc", action="append", default=[], help="Increment clock: name=delta")

    parser.add_argument("--success-sheet-set", action="append", default=[])
    parser.add_argument("--success-sheet-inc", action="append", default=[])
    parser.add_argument("--failure-sheet-set", action="append", default=[])
    parser.add_argument("--failure-sheet-inc", action="append", default=[])

    parser.add_argument("--success-tracker-set", action="append", default=[])
    parser.add_argument("--success-tracker-inc", action="append", default=[])
    parser.add_argument("--failure-tracker-set", action="append", default=[])
    parser.add_argument("--failure-tracker-inc", action="append", default=[])

    parser.add_argument("--log", action="store_true", help="Append roll details to campaign session log")
    parser.add_argument("--log-role", default="System", help="Role label for log entries")
    parser.add_argument("--recap", action="append", default=[], help="Add a memory summary line (repeatable)")
    parser.add_argument("--thread", action="append", default=[])
    parser.add_argument("--npc", action="append", default=[])
    parser.add_argument("--secret", action="append", default=[])

    parser.add_argument("--out-roll", help="Write roll JSON to this file")
    parser.add_argument("--json", action="store_true", help="Print roll JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

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

    args = parser.parse_args()

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

        success = bool(check_roll.get("final_success", check_roll.get("success")))
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

    # Spend luck for nudge
    if args.nudge:
        luck_cost = abs(args.nudge)
        luck_path = "pools.luck.current"
        try:
            parent, key = ensure_path(sheet, luck_path)
            current_luck = parent.get(key)
            if not is_int(current_luck):
                raise TypeError("pools.luck.current is not int")
            if current_luck < luck_cost:
                raise ValueError(f"not enough luck tokens: need {luck_cost}, have {current_luck}")
            parent[key] = current_luck - luck_cost
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

    changed_paths: list[str] = []
    try:
        for key, value in sheet_sets:
            set_path(sheet, key, value)
            changed_paths.append(key)
        for key, delta in sheet_incs:
            if not isinstance(delta, (int, float)):
                raise TypeError(f"delta for {key} is not numeric")
            inc_path(sheet, key, int(delta))
            changed_paths.append(key)

        for key, value in tracker_sets:
            set_path(tracker, key, value)
            changed_paths.append(key)
        for key, delta in tracker_incs:
            if not isinstance(delta, (int, float)):
                raise TypeError(f"delta for {key} is not numeric")
            inc_path(tracker, key, int(delta))
            changed_paths.append(key)

    except (KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Tracker increments
    if args.scene_inc:
        tracker["scene"] = int(tracker.get("scene", 0)) + args.scene_inc

    if args.pressure_inc:
        clocks = tracker.setdefault("clocks", {})
        pressure = clocks.setdefault("pressure", {})
        pressure.setdefault("name", "pressure")
        pressure.setdefault("current", 0)
        pressure.setdefault("max", 5)
        pressure["current"] = int(pressure.get("current", 0)) + args.pressure_inc

    for item in args.clock_inc:
        name, value = parse_kv(item)
        delta = int(value)
        clocks = tracker.setdefault("clocks", {})
        clock = clocks.setdefault(name, {})
        clock.setdefault("name", name)
        clock.setdefault("current", 0)
        clock.setdefault("max", 5)
        clock["current"] = int(clock.get("current", 0)) + delta

    clamp_currents(sheet, changed_paths)
    clamp_currents(tracker, changed_paths)

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
