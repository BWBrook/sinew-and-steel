#!/usr/bin/env python3
import argparse
from datetime import date
import json
from pathlib import Path
import sys
import yaml

import _sslib
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a character sheet with point-buy validation.")
    parser.add_argument("--skin", help="Skin slug from manifest.yaml")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--name", required=True, help="Character name")
    parser.add_argument("--player", default="", help="Player name")
    parser.add_argument("--out", help="Output file (default: stdout or campaign path)")
    parser.add_argument("--dry-run", action="store_true", help="Compute output but do not write files")
    parser.add_argument("--json", action="store_true", help="Output JSON (includes sheet data)")
    parser.add_argument("--set", action="append", default=[], help="Set stat (STAT=VALUE)")
    parser.add_argument("--delta", action="append", default=[], help="Adjust stat by delta (STAT=+2)")
    parser.add_argument(
        "--stamina",
        type=int,
        default=5,
        help="Stamina score (default 5; participates in point-buy). Prefer --set STM=... for clarity (STA also accepted).",
    )
    parser.add_argument(
        "--build-points",
        type=int,
        help="Build points budget at creation (default: campaign.yaml build_points_budget or 6).",
    )
    parser.add_argument(
        "--tone",
        choices=["grim", "standard", "pulp", "heroic"],
        help="Shortcut for build-point budgets: grim=0, standard=6, pulp=12, heroic=16.",
    )
    parser.add_argument("--note", action="append", default=[], help="Add note to sheet")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Disallow extra decreases beyond what is needed (no voluntary weakness below baseline).",
    )

    args = parser.parse_args()

    if not args.skin and not args.campaign:
        print("error: provide --skin or --campaign", file=sys.stderr)
        return 1

    manifest = load_manifest()
    skins = manifest.get("skins", {})

    skin_slug = args.skin
    campaign = None
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

    if args.tone and args.build_points is not None:
        print("error: provide only one of --tone or --build-points", file=sys.stderr)
        return 1

    tone_map = {"grim": 0, "standard": 6, "pulp": 12, "heroic": 16}
    if args.tone:
        build_points_budget = tone_map[args.tone]
    elif args.build_points is not None:
        build_points_budget = int(args.build_points)
    elif campaign and isinstance(campaign.get("build_points_budget"), int):
        build_points_budget = int(campaign["build_points_budget"])
    else:
        build_points_budget = 6

    if build_points_budget < 0:
        print("error: --build-points must be >= 0", file=sys.stderr)
        return 1

    # Build stats from baseline 10 (Stamina baseline is 5 and participates in the ledger)
    stats = {key: 10 for key in attrs.keys()}
    stamina_value = int(args.stamina)

    try:
        for item in args.delta:
            key, value = parse_kv(item)
            if key in ("STM", "STA"):
                stamina_value += int(value)
                continue
            if key not in stats:
                raise ValueError(f"Unknown stat '{key}' (use skin stats or STM for stamina)")
            delta = int(value)
            stats[key] += delta

        for item in args.set:
            key, value = parse_kv(item)
            if key in ("STM", "STA"):
                stamina_value = int(value)
                continue
            if key not in stats:
                raise ValueError(f"Unknown stat '{key}' (use skin stats or STM for stamina)")
            stats[key] = int(value)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Validate point-buy rules (attributes baseline 10; stamina baseline 5) with build points.
    errors = []
    baselines = {key: 10 for key in stats.keys()}
    baselines["STM"] = 5
    values = dict(stats)
    values["STM"] = stamina_value

    try:
        needed, increases, decreases, required_decreases, slack = _sslib.build_points_needed_mixed(values, baselines)
    except Exception as exc:
        errors.append(f"failed to compute point-buy validation: {exc}")
        needed = increases = decreases = required_decreases = slack = 0

    if needed > build_points_budget:
        errors.append(
            "build points exceeded: "
            f"needed={needed} budget={build_points_budget} "
            f"(increases={increases} decreases={decreases})"
        )

    for key, value in stats.items():
        if value < 6 or value > 16:
            errors.append(f"{key} out of range (6-16): {value}")

    if stamina_value < 3 or stamina_value > 9:
        errors.append(f"stamina out of range (3-9): {stamina_value}")

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    if args.strict and slack > 0:
        print(f"error: strict mode forbids extra decreases (slack={slack})", file=sys.stderr)
        return 1
    if slack > 0:
        print(f"warning: build leaves {slack} point(s) of extra decreases below baseline", file=sys.stderr)

    luck_key = skin.get("luck_key")
    if luck_key not in stats:
        print("error: luck_key not found in attributes", file=sys.stderr)
        return 1

    luck_value = stats[luck_key]

    sheet = {
        "schema_version": 1,
        "name": args.name,
        "skin": skin_slug,
        "player": args.player,
        "created": date.today().isoformat(),
        "creation": {
            "build_points_budget": build_points_budget,
            "build_points_used": needed,
        },
        "attributes": stats,
        "pools": {
            "luck": {
                "name": skin.get("luck_name", luck_key),
                "current": luck_value,
                "max": luck_value,
            },
            "stamina": {
                "current": stamina_value,
                "max": stamina_value,
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

    out_path = None
    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
    elif args.campaign:
        char_slug = _sslib.slugify(args.name, fallback="character")
        out_path = ROOT / "campaigns" / args.campaign / "state" / "characters" / f"{char_slug}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "ok": True,
        "path": str(out_path) if out_path else None,
        "sheet": sheet,
    }

    if args.dry_run:
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(output)
        return 0

    if out_path:
        out_path.write_text(output, encoding="utf-8")
        if args.json:
            print(json.dumps(payload, indent=2))
            return 0
        if args.campaign and not args.out:
            print(f"written {out_path}")
    else:
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
