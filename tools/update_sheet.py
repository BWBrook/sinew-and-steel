#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

import _sslib


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Update a YAML character sheet or tracker file.")
    parser.add_argument("--file", help="YAML file to update")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename under campaign state")
    parser.add_argument("--set", action="append", default=[], help="Set key=value (repeatable)")
    parser.add_argument("--inc", action="append", default=[], help="Increment key=delta (repeatable)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing")
    parser.add_argument("--allow-new", action="store_true", help="Allow creating new keys when updating state")

    args = parser.parse_args()
    root = _sslib.repo_root()

    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = root / path
    elif args.campaign:
        chars_dir = _sslib.campaign_characters_dir(args.campaign, root=root)
        try:
            path = _sslib.resolve_character_file(chars_dir, args.character)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        print("error: provide --file or --campaign", file=sys.stderr)
        return 1

    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    allow_clock = isinstance(data.get("clocks"), dict)
    if data.get("clocks") is not None and not allow_clock:
        print("error: clocks is not a dict", file=sys.stderr)
        return 1

    try:
        for item in args.set:
            key, value = parse_kv(item)
            _sslib.set_path(
                data, key, parse_value(value), allow_new=args.allow_new, allow_clock=allow_clock
            )

        for item in args.inc:
            key, value = parse_kv(item)
            delta = parse_value(value)
            if not isinstance(delta, (int, float)):
                raise TypeError(f"Delta for '{key}' is not numeric")
            _sslib.inc_path(data, key, delta, allow_new=args.allow_new, allow_clock=allow_clock)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = yaml.safe_dump(data, sort_keys=False)

    if args.stdout:
        print(output)
    else:
        path.write_text(output, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
