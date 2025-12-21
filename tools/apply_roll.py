#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
import yaml

import _sslib


def load_roll(args):
    if args.roll:
        path = Path(args.roll)
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    if args.roll_json:
        return json.loads(args.roll_json)
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No roll data provided")
    return json.loads(raw)


def parse_kv(item: str):
    if "=" not in item:
        raise ValueError(f"Expected key=value, got '{item}'")
    key, value = item.split("=", 1)
    return key.strip(), value.strip()


def parse_value(value: str):
    try:
        return yaml.safe_load(value)
    except Exception:
        return value


def update_file(path: Path, sets, incs, clamp=False, allow_new=False, allow_clock=False):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    for key, value in sets:
        _sslib.set_path(data, key, value, allow_new=allow_new, allow_clock=allow_clock)
    for key, value in incs:
        _sslib.inc_path(data, key, value, allow_new=allow_new, allow_clock=allow_clock)
    if clamp:
        _sslib.clamp_currents(data, [k for k, _ in sets] + [k for k, _ in incs])
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply roll outcomes to sheets or trackers.")
    parser.add_argument("--roll", help="Path to roll JSON (from tools/roll.py)")
    parser.add_argument("--roll-json", help="Roll JSON string")
    parser.add_argument("--as", dest="as_role", choices=["attacker", "defender"], default="attacker")
    parser.add_argument("--clamp", action="store_true", help="Clamp .current values between 0 and .max")
    parser.add_argument("--allow-new", action="store_true", help="Allow creating new keys when updating state")

    parser.add_argument("--sheet", help="Sheet YAML file to update")
    parser.add_argument("--tracker", help="Tracker YAML file to update")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/ (defaults sheet/tracker paths)")
    parser.add_argument("--character", help="Character slug or filename under campaign state")

    parser.add_argument("--success-sheet-set", action="append", default=[])
    parser.add_argument("--success-sheet-inc", action="append", default=[])
    parser.add_argument("--failure-sheet-set", action="append", default=[])
    parser.add_argument("--failure-sheet-inc", action="append", default=[])

    parser.add_argument("--success-tracker-set", action="append", default=[])
    parser.add_argument("--success-tracker-inc", action="append", default=[])
    parser.add_argument("--failure-tracker-set", action="append", default=[])
    parser.add_argument("--failure-tracker-inc", action="append", default=[])

    args = parser.parse_args()

    try:
        roll = load_roll(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if "outcome" in roll:
        winner = roll.get("outcome", {}).get("winner")
        if winner not in ("attacker", "defender"):
            print("error: invalid outcome in roll JSON", file=sys.stderr)
            return 1
        success = winner == args.as_role
    else:
        if "success" not in roll and "final_success" not in roll:
            print("error: roll JSON missing success field", file=sys.stderr)
            return 1
        success = bool(roll.get("final_success", roll.get("success")))

    def parse_list(items):
        parsed = []
        for item in items:
            key, value = parse_kv(item)
            parsed.append((key, parse_value(value)))
        return parsed

    success_sheet_sets = parse_list(args.success_sheet_set)
    success_sheet_incs = parse_list(args.success_sheet_inc)
    failure_sheet_sets = parse_list(args.failure_sheet_set)
    failure_sheet_incs = parse_list(args.failure_sheet_inc)

    success_tracker_sets = parse_list(args.success_tracker_set)
    success_tracker_incs = parse_list(args.success_tracker_inc)
    failure_tracker_sets = parse_list(args.failure_tracker_set)
    failure_tracker_incs = parse_list(args.failure_tracker_inc)

    if success:
        sheet_sets = success_sheet_sets
        sheet_incs = success_sheet_incs
        tracker_sets = success_tracker_sets
        tracker_incs = success_tracker_incs
    else:
        sheet_sets = failure_sheet_sets
        sheet_incs = failure_sheet_incs
        tracker_sets = failure_tracker_sets
        tracker_incs = failure_tracker_incs

    root = _sslib.repo_root()
    sheet_path = None
    tracker_path = None

    need_sheet = bool(sheet_sets or sheet_incs)
    need_tracker = bool(tracker_sets or tracker_incs)

    if args.sheet:
        sheet_path = Path(args.sheet)
        if not sheet_path.is_absolute():
            sheet_path = root / sheet_path
    if args.tracker:
        tracker_path = Path(args.tracker)
        if not tracker_path.is_absolute():
            tracker_path = root / tracker_path

    if args.campaign:
        if sheet_path is None and need_sheet:
            chars_dir = _sslib.campaign_characters_dir(args.campaign, root=root)
            try:
                sheet_path = _sslib.resolve_character_file(chars_dir, args.character)
            except FileNotFoundError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1

        if tracker_path is None and need_tracker:
            tracker_path = _sslib.campaign_trackers_dir(args.campaign, root=root) / "session.yaml"

    if need_sheet:
        if not sheet_path or not sheet_path.exists():
            print(f"error: sheet not found: {sheet_path}", file=sys.stderr)
            return 1
        update_file(
            sheet_path,
            sheet_sets,
            sheet_incs,
            clamp=args.clamp,
            allow_new=args.allow_new,
            allow_clock=False,
        )

    if need_tracker:
        if not tracker_path or not tracker_path.exists():
            print(f"error: tracker not found: {tracker_path}", file=sys.stderr)
            return 1
        update_file(
            tracker_path,
            tracker_sets,
            tracker_incs,
            clamp=args.clamp,
            allow_new=args.allow_new,
            allow_clock=True,
        )

    print("applied" if success else "applied (failure)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
