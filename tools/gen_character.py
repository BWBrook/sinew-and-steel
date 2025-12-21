#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path
import random
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 10
MIN_STAT = 6
MAX_STAT = 16


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.yaml"
    if not manifest_path.exists():
        print(f"error: missing manifest: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def apply_double_debit_steps(keys, steps: int, primary: str | None = None) -> dict:
    stats = {key: BASELINE for key in keys}

    if primary and primary not in stats:
        raise ValueError(f"Unknown primary stat '{primary}'")

    for _ in range(steps):
        # Only increase stats at/above baseline so each step represents a real
        # \"above baseline\" increase that must be paid for.
        inc_candidates = [k for k in keys if BASELINE <= stats[k] < MAX_STAT]
        if not inc_candidates:
            break

        if primary and stats[primary] < MAX_STAT:
            weights = [6 if k == primary else 1 for k in inc_candidates]
            inc_key = random.choices(inc_candidates, weights=weights, k=1)[0]
        else:
            inc_key = random.choice(inc_candidates)

        # Only pay from stats that are not above baseline. This keeps generated
        # sheets tight: decreases == 2 * increases (no accidental overpay).
        dec_candidates = [k for k in keys if k != inc_key and MIN_STAT < stats[k] <= BASELINE]
        if not dec_candidates:
            break

        dec_1 = random.choice(dec_candidates)
        stats[dec_1] -= 1

        dec_candidates_2 = [k for k in keys if k != inc_key and MIN_STAT < stats[k] <= BASELINE]
        if not dec_candidates_2:
            stats[dec_1] += 1
            break

        dec_2 = random.choice(dec_candidates_2)
        stats[dec_2] -= 1

        stats[inc_key] += 1

    return stats


def sample_stats(keys, steps: int | None, min_steps: int, max_steps: int, primary: str | None) -> dict:
    if steps is None:
        if min_steps < 0 or max_steps < min_steps:
            raise ValueError("Invalid min/max steps")
        steps = random.randint(min_steps, max_steps)

    for _ in range(200):
        stats = apply_double_debit_steps(keys, steps=steps, primary=primary)
        if any(v > BASELINE for v in stats.values()):
            return stats

    raise RuntimeError("Failed to generate a specialized character after 200 attempts")


def build_sheet(skin_entry: dict, name: str, player: str):
    attrs = skin_entry.get("attributes", {})
    if len(attrs) != 5:
        print("error: skin attributes missing or incomplete", file=sys.stderr)
        sys.exit(1)

    keys = list(attrs.keys())
    gen = skin_entry.get("_gen", {}) if isinstance(skin_entry.get("_gen"), dict) else {}
    stats = sample_stats(
        keys,
        steps=gen.get("steps"),
        min_steps=int(gen.get("min_steps", 2)),
        max_steps=int(gen.get("max_steps", 6)),
        primary=gen.get("primary"),
    )

    luck_key = skin_entry.get("luck_key")
    if luck_key not in stats:
        print("error: luck_key not found in attributes", file=sys.stderr)
        sys.exit(1)

    luck_value = stats[luck_key]

    sheet = {
        "schema_version": 1,
        "name": name,
        "skin": skin_entry.get("slug", ""),
        "player": player,
        "created": date.today().isoformat(),
        "meta": {
            "generated": {
                "method": "double_debit",
                "steps": gen.get("steps"),
                "min_steps": gen.get("min_steps", 2),
                "max_steps": gen.get("max_steps", 6),
                "primary": gen.get("primary"),
            }
        },
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
    parser.add_argument("--steps", type=int, help="Number of double-debit steps to apply")
    parser.add_argument("--min-steps", type=int, default=2, help="Min steps when --steps not provided")
    parser.add_argument("--max-steps", type=int, default=6, help="Max steps when --steps not provided")
    parser.add_argument("--primary", help="Bias stat increases toward this stat key")

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

    try:
        sheet = build_sheet(
            {
                **skin_entry,
                "_gen": {
                    "steps": args.steps,
                    "min_steps": args.min_steps,
                    "max_steps": args.max_steps,
                    "primary": args.primary,
                },
            },
            args.name,
            args.player,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
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
