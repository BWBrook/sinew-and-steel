#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path
import random
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def sample_stats(keys):
    # Rejection sample for sum 50 within [6,16]
    for _ in range(10000):
        values = [random.randint(6, 16) for _ in keys]
        if sum(values) == 50:
            return dict(zip(keys, values))
    raise RuntimeError("Failed to sample stats after 10,000 attempts")


def build_sheet(skin_entry: dict, name: str, player: str):
    attrs = skin_entry.get("attributes", {})
    if len(attrs) != 5:
        print("error: skin attributes missing or incomplete", file=sys.stderr)
        sys.exit(1)

    keys = list(attrs.keys())
    stats = sample_stats(keys)

    luck_key = skin_entry.get("luck_key")
    if luck_key not in stats:
        print("error: luck_key not found in attributes", file=sys.stderr)
        sys.exit(1)

    luck_value = stats[luck_key]

    sheet = {
        "name": name,
        "skin": skin_entry.get("slug", ""),
        "player": player,
        "created": date.today().isoformat(),
        "attributes": stats,
        "pools": {
            "luck": {
                "name": skin_entry.get("luck_name", luck_key),
                "current": luck_value,
                "max": luck_value,
            },
            "stamina": {
                "current": 5,
                "max": 5,
            },
        },
        "tracks": {
            "pressure": {
                "name": skin_entry.get("pressure_track", "Pressure"),
                "current": 0,
                "max": 5,
            }
        },
        "inventory": {
            "big_items": [],
            "small_items": [],
        },
        "notes": [],
    }
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a random character sheet for a skin.")
    parser.add_argument("--skin", required=True, help="Skin slug from manifest.yaml")
    parser.add_argument("--name", default="Unnamed", help="Character name")
    parser.add_argument("--player", default="", help="Player name")
    parser.add_argument("--out", help="Output file (default: stdout)")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    manifest = load_manifest()
    skins = manifest.get("skins", {})
    if args.skin not in skins:
        print(f"error: unknown skin '{args.skin}'", file=sys.stderr)
        return 1

    skin_entry = skins[args.skin]
    skin_entry = {**skin_entry, "slug": args.skin}

    sheet = build_sheet(skin_entry, args.name, args.player)
    output = yaml.safe_dump(sheet, sort_keys=False)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
