#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

import _sslib

def load_yaml(path: Path) -> dict:
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def save_yaml(path: Path, data: dict, stdout: bool) -> None:
    output = yaml.safe_dump(data, sort_keys=False)
    if stdout:
        print(output)
    else:
        path.write_text(output, encoding="utf-8")


def ensure_clock(data: dict, key: str, name: str, max_value: int) -> dict:
    clocks = data.setdefault("clocks", {})
    clock = clocks.get(key)
    if not isinstance(clock, dict):
        clock = {}
        clocks[key] = clock
    clock.setdefault("name", name)
    clock.setdefault("current", 0)
    clock.setdefault("max", max_value)
    return clock


def clamp_value(value: int, min_value: int, max_value: int) -> int:
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def command_scene(args) -> dict:
    data = load_yaml(args.file)
    scene = data.get("scene", 0)
    if not isinstance(scene, int):
        print("error: scene value is not an integer", file=sys.stderr)
        sys.exit(1)

    if args.set is not None and args.inc is not None:
        print("error: use only one of --set or --inc", file=sys.stderr)
        sys.exit(1)

    if args.set is not None:
        data["scene"] = args.set
    else:
        inc = args.inc if args.inc is not None else 1
        data["scene"] = scene + inc

    save_yaml(args.file, data, args.stdout)
    return data


def command_clock(args) -> dict:
    data = load_yaml(args.file)
    key = args.name

    if args.set is not None and args.inc is not None:
        print("error: use only one of --set or --inc", file=sys.stderr)
        sys.exit(1)

    clock = ensure_clock(
        data,
        key,
        args.label or key,
        args.max if args.max is not None else 5,
    )

    current = clock.get("current", 0)
    if not isinstance(current, int):
        print("error: clock current value is not an integer", file=sys.stderr)
        sys.exit(1)

    if args.set is not None:
        current = args.set
    else:
        inc = args.inc if args.inc is not None else 1
        current = current + inc

    if args.clamp:
        max_value = clock.get("max", 5)
        if not isinstance(max_value, int):
            print("error: clock max value is not an integer", file=sys.stderr)
            sys.exit(1)
        current = clamp_value(current, 0, max_value)

    clock["current"] = current
    save_yaml(args.file, data, args.stdout)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Update session trackers (scene counter, clocks).")
    parser.add_argument("--file", type=Path, help="Tracker YAML file")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/ (uses state/trackers/session.yaml)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing")

    subparsers = parser.add_subparsers(dest="command", required=True)

    scene = subparsers.add_parser("scene", help="Increment or set scene counter")
    scene.add_argument("--inc", type=int, help="Increment by N (default 1)")
    scene.add_argument("--set", type=int, help="Set scene counter to N")

    clock = subparsers.add_parser("clock", help="Increment or set a named clock")
    clock.add_argument("--name", required=True, help="Clock key under clocks")
    clock.add_argument("--inc", type=int, help="Increment by N (default 1)")
    clock.add_argument("--set", type=int, help="Set current to N")
    clock.add_argument("--max", type=int, help="Max value if clock is created")
    clock.add_argument("--label", help="Display name if clock is created")
    clock.add_argument("--clamp", action="store_true", help="Clamp current between 0 and max")

    pressure = subparsers.add_parser("pressure", help="Shortcut for clocks.pressure")
    pressure.add_argument("--inc", type=int, help="Increment by N (default 1)")
    pressure.add_argument("--set", type=int, help="Set current to N")
    pressure.add_argument("--max", type=int, help="Max value if clock is created")
    pressure.add_argument("--label", help="Display name if clock is created")
    pressure.add_argument("--clamp", action="store_true", help="Clamp current between 0 and max")

    args = parser.parse_args()

    root = _sslib.repo_root()
    if args.file:
        if not args.file.is_absolute():
            args.file = root / args.file
    elif args.campaign:
        args.file = _sslib.campaign_trackers_dir(args.campaign, root=root) / "session.yaml"
    else:
        print("error: provide --file or --campaign", file=sys.stderr)
        return 1

    if args.command == "scene":
        command_scene(args)
    elif args.command == "clock":
        command_clock(args)
    else:
        args.name = "pressure"
        command_clock(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
