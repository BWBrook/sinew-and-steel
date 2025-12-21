#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def load_campaign(campaign_slug: str) -> dict:
    campaign_path = ROOT / "campaigns" / campaign_slug / "campaign.yaml"
    if not campaign_path.exists():
        print(f"error: campaign not found: {campaign_path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(campaign_path.read_text(encoding="utf-8")) or {}


def parse_kv(item: str):
    if "=" not in item:
        raise ValueError(f"Expected key=value, got '{item}'")
    key, value = item.split("=", 1)
    return key.strip(), value.strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return slug or "character"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a character sheet with point-buy validation.")
    parser.add_argument("--skin", help="Skin slug from manifest.yaml")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--name", required=True, help="Character name")
    parser.add_argument("--player", default="", help="Player name")
    parser.add_argument("--out", help="Output file (default: stdout or campaign path)")
    parser.add_argument("--set", action="append", default=[], help="Set stat (STAT=VALUE)")
    parser.add_argument("--delta", action="append", default=[], help="Adjust stat by delta (STAT=+2)")
    parser.add_argument("--stamina", type=int, default=5, help="Starting stamina (default 5)")
    parser.add_argument("--note", action="append", default=[], help="Add note to sheet")
    parser.add_argument("--strict", action="store_true", help="Require exact double-debit payment (no extra decreases)")

    args = parser.parse_args()

    if not args.skin and not args.campaign:
        print("error: provide --skin or --campaign", file=sys.stderr)
        return 1

    manifest = load_manifest()
    skins = manifest.get("skins", {})

    skin_slug = args.skin
    if args.campaign:
        campaign = load_campaign(args.campaign)
        campaign_skin = campaign.get("skin")
        if not campaign_skin:
            print("error: campaign.yaml missing skin", file=sys.stderr)
            return 1
        if skin_slug and skin_slug != campaign_skin:
            print("error: --skin does not match campaign.yaml", file=sys.stderr)
            return 1
        skin_slug = campaign_skin

    if skin_slug not in skins:
        print(f"error: unknown skin '{skin_slug}'", file=sys.stderr)
        return 1

    skin = skins[skin_slug]
    attrs = skin.get("attributes", {})
    if len(attrs) != 5:
        print("error: skin attributes missing or incomplete", file=sys.stderr)
        return 1

    # Build stats from baseline 10
    stats = {key: 10 for key in attrs.keys()}

    try:
        for item in args.delta:
            key, value = parse_kv(item)
            if key not in stats:
                raise ValueError(f"Unknown stat '{key}'")
            delta = int(value)
            stats[key] += delta

        for item in args.set:
            key, value = parse_kv(item)
            if key not in stats:
                raise ValueError(f"Unknown stat '{key}'")
            stats[key] = int(value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Validate point-buy rules
    errors = []
    baseline = 10
    increases = sum(max(0, v - baseline) for v in stats.values())
    decreases = sum(max(0, baseline - v) for v in stats.values())
    required_decreases = 2 * increases

    if decreases < required_decreases:
        errors.append(
            f"double-debit not paid: increases={increases} decreases={decreases} (need >= {required_decreases})"
        )

    for key, value in stats.items():
        if value < 6 or value > 16:
            errors.append(f"{key} out of range (6-16): {value}")

    if args.stamina < 3 or args.stamina > 9:
        errors.append(f"stamina out of range (3-9): {args.stamina}")

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    slack = decreases - required_decreases
    if args.strict and slack != 0:
        print(f"error: strict mode requires slack=0 (got slack={slack})", file=sys.stderr)
        return 1
    if slack > 0 and increases > 0:
        print(f"warning: build overpays by {slack} point(s) (decreases beyond required)", file=sys.stderr)

    luck_key = skin.get("luck_key")
    if luck_key not in stats:
        print("error: luck_key not found in attributes", file=sys.stderr)
        return 1

    luck_value = stats[luck_key]

    sheet = {
        "name": args.name,
        "skin": skin_slug,
        "player": args.player,
        "created": date.today().isoformat(),
        "attributes": stats,
        "pools": {
            "luck": {
                "name": skin.get("luck_name", luck_key),
                "current": luck_value,
                "max": luck_value,
            },
            "stamina": {
                "current": args.stamina,
                "max": args.stamina,
            },
        },
        "tracks": {
            "pressure": {
                "name": skin.get("pressure_track", "Pressure"),
                "current": 0,
                "max": 5,
            }
        },
        "inventory": {
            "big_items": [],
            "small_items": [],
        },
        "notes": args.note,
    }

    output = yaml.safe_dump(sheet, sort_keys=False)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.write_text(output, encoding="utf-8")
    elif args.campaign:
        char_slug = slugify(args.name)
        out_path = ROOT / "campaigns" / args.campaign / "state" / "characters" / f"{char_slug}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"written {out_path}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
