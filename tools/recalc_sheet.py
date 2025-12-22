#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import yaml

import _sslib


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute creation.build_points_used from a sheet.")
    parser.add_argument("--file", help="Character sheet YAML file")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename under campaign state")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing")
    parser.add_argument("--dry-run", action="store_true", help="Compute output but do not write files")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")

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

    attrs = data.get("attributes")
    if not isinstance(attrs, dict) or not attrs:
        print("error: sheet missing attributes", file=sys.stderr)
        return 1

    pools = data.get("pools")
    if not isinstance(pools, dict):
        print("error: sheet missing pools", file=sys.stderr)
        return 1

    stamina = pools.get("stamina")
    if not isinstance(stamina, dict):
        print("error: sheet missing pools.stamina", file=sys.stderr)
        return 1

    stamina_value = stamina.get("max")
    if not isinstance(stamina_value, int):
        stamina_value = stamina.get("current")
    if not isinstance(stamina_value, int):
        print("error: pools.stamina.max or current is not an int", file=sys.stderr)
        return 1

    values = {k: int(v) for k, v in attrs.items()}
    values["STA"] = int(stamina_value)
    baselines = {k: 10 for k in attrs.keys()}
    baselines["STA"] = 5

    try:
        needed, increases, decreases, required_decreases, slack = _sslib.build_points_needed_mixed(values, baselines)
    except Exception as exc:
        print(f"error: failed to compute build points: {exc}", file=sys.stderr)
        return 1

    creation = data.get("creation")
    if not isinstance(creation, dict):
        creation = {}
        data["creation"] = creation
    creation["build_points_used"] = int(needed)

    budget = creation.get("build_points_budget")
    if isinstance(budget, int) and needed > budget:
        print(
            f"warning: build points exceed budget (needed={needed} budget={budget})",
            file=sys.stderr,
        )

    output = yaml.safe_dump(data, sort_keys=False)
    payload = {
        "ok": True,
        "file": str(path),
        "build_points_used": int(needed),
        "budget": budget if isinstance(budget, int) else None,
        "details": {
            "increases": int(increases),
            "decreases": int(decreases),
            "required_decreases": int(required_decreases),
            "slack": int(slack),
        },
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        if args.json:
            import json

            print(json.dumps(payload, indent=2))
        else:
            print(output)
        return 0

    if not args.stdout:
        path.write_text(output, encoding="utf-8")

    if args.json:
        import json

        print(json.dumps(payload, indent=2))
        return 0

    if args.stdout:
        print(output)
    else:
        print(f"updated {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
