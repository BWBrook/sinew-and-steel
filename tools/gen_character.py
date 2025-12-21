#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path
import random
import sys
import yaml

import _sslib

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 10
STAMINA_BASELINE = 5
MIN_STAT = 6
MAX_STAT = 16
MIN_STAMINA = 3
MAX_STAMINA = 9


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


def apply_double_debit_steps(keys, steps: int, primary: str | None = None) -> dict:
    baselines = {key: BASELINE for key in keys}
    mins = {key: MIN_STAT for key in keys}
    maxs = {key: MAX_STAT for key in keys}
    if "STA" in keys:
        baselines["STA"] = STAMINA_BASELINE
        mins["STA"] = MIN_STAMINA
        maxs["STA"] = MAX_STAMINA

    stats = {key: baselines[key] for key in keys}

    if primary and primary not in stats:
        raise ValueError(f"Unknown primary stat '{primary}'")

    for _ in range(steps):
        # Only increase stats at/above baseline so each step represents a real
        # \"above baseline\" increase that must be paid for.
        inc_candidates = [k for k in keys if baselines[k] <= stats[k] < maxs[k]]
        if not inc_candidates:
            break

        if primary and stats[primary] < maxs[primary]:
            weights = [6 if k == primary else (0.5 if k == "STA" else 1.0) for k in inc_candidates]
            inc_key = random.choices(inc_candidates, weights=weights, k=1)[0]
        else:
            weights = [0.5 if k == "STA" else 1.0 for k in inc_candidates]
            inc_key = random.choices(inc_candidates, weights=weights, k=1)[0]

        # Only pay from stats that are not above baseline. This keeps generated
        # sheets tight: decreases == 2 * increases (no accidental overpay).
        dec_candidates = [k for k in keys if k != inc_key and mins[k] < stats[k] <= baselines[k]]
        if not dec_candidates:
            break

        dec_weights = [0.3 if k == "STA" else 1.0 for k in dec_candidates]
        dec_1 = random.choices(dec_candidates, weights=dec_weights, k=1)[0]
        stats[dec_1] -= 1

        dec_candidates_2 = [k for k in keys if k != inc_key and mins[k] < stats[k] <= baselines[k]]
        if not dec_candidates_2:
            stats[dec_1] += 1
            break

        dec_weights_2 = [0.3 if k == "STA" else 1.0 for k in dec_candidates_2]
        dec_2 = random.choices(dec_candidates_2, weights=dec_weights_2, k=1)[0]
        stats[dec_2] -= 1

        stats[inc_key] += 1

    return stats


def spend_build_points(
    stats: dict[str, int],
    baselines: dict[str, int],
    maxs: dict[str, int],
    points: int,
    primary: str | None,
) -> int:
    """
    Spend build points by increasing stats while respecting per-stat caps.

    Cost model:
      - If the stat is currently below baseline: +1 costs 1 point.
      - If the stat is at/above baseline: +1 costs 2 points.
    """
    remaining = int(points)
    if remaining <= 0:
        return 0

    for _ in range(10_000):
        if remaining <= 0:
            break

        candidates = [k for k, v in stats.items() if int(v) < int(maxs[k])]
        if not candidates:
            break

        affordable: list[str] = []
        weights: list[float] = []
        for key in candidates:
            cost = 1 if int(stats[key]) < int(baselines[key]) else 2
            if remaining < cost:
                continue
            affordable.append(key)

            weight = 1.0
            if primary and key == primary:
                weight *= 4.0
            if int(stats[key]) < int(baselines[key]):
                weight *= 3.0
            if key == "STA":
                weight *= 0.7
            weights.append(weight)

        if not affordable:
            break

        chosen = random.choices(affordable, weights=weights, k=1)[0]
        cost = 1 if int(stats[chosen]) < int(baselines[chosen]) else 2
        if remaining < cost:
            break
        stats[chosen] += 1
        remaining -= cost

    return remaining


def sample_stats(keys, steps: int | None, min_steps: int, max_steps: int, primary: str | None) -> dict:
    if steps is None:
        if min_steps < 0 or max_steps < min_steps:
            raise ValueError("Invalid min/max steps")
        steps = random.randint(min_steps, max_steps)

    baselines = {key: BASELINE for key in keys}
    if "STA" in keys:
        baselines["STA"] = STAMINA_BASELINE

    for _ in range(200):
        stats = apply_double_debit_steps(keys, steps=steps, primary=primary)
        if any(int(stats[k]) > baselines[k] for k in stats.keys()):
            return stats

    raise RuntimeError("Failed to generate a specialized character after 200 attempts")


def build_sheet(skin_entry: dict, name: str, player: str):
    attrs = skin_entry.get("attributes", {})
    if len(attrs) != 5:
        print("error: skin attributes missing or incomplete", file=sys.stderr)
        sys.exit(1)

    keys = list(attrs.keys()) + ["STA"]
    gen = skin_entry.get("_gen", {}) if isinstance(skin_entry.get("_gen"), dict) else {}
    stats = sample_stats(
        keys,
        steps=gen.get("steps"),
        min_steps=int(gen.get("min_steps", 2)),
        max_steps=int(gen.get("max_steps", 6)),
        primary=gen.get("primary"),
    )

    baselines = {key: BASELINE for key in keys}
    maxs = {key: MAX_STAT for key in keys}
    baselines["STA"] = STAMINA_BASELINE
    maxs["STA"] = MAX_STAMINA

    build_points_budget = int(gen.get("build_points_budget", 6))
    remaining = spend_build_points(
        stats,
        baselines,
        maxs,
        points=build_points_budget,
        primary=gen.get("primary"),
    )

    stamina_value = int(stats.get("STA", STAMINA_BASELINE))
    stats = {k: stats[k] for k in attrs.keys()}

    needed, _, _, _, slack = _sslib.build_points_needed_mixed(
        {**stats, "STA": stamina_value},
        {**{k: BASELINE for k in attrs.keys()}, "STA": STAMINA_BASELINE},
    )
    if needed > build_points_budget:
        raise RuntimeError(
            f"internal error: generated build exceeds budget (needed={needed} budget={build_points_budget})"
        )
    if slack > 0:
        raise RuntimeError(f"internal error: generated build has extra decreases (slack={slack})")

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
        "creation": {
            "build_points_budget": build_points_budget,
            "build_points_used": needed,
        },
        "meta": {
            "generated": {
                "method": "double_debit",
                "steps": gen.get("steps"),
                "min_steps": gen.get("min_steps", 2),
                "max_steps": gen.get("max_steps", 6),
                "primary": gen.get("primary"),
                "build_points_budget": build_points_budget,
                "build_points_unspent": int(remaining),
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
                "current": stamina_value,
                "max": stamina_value,
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
    parser.add_argument("--skin", help="Skin slug from manifest.yaml")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/ (reads skin + build point budget)")
    parser.add_argument("--name", default="Unnamed", help="Character name")
    parser.add_argument("--player", default="", help="Player name")
    parser.add_argument("--out", help="Output file (default: stdout)")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--steps", type=int, help="Number of double-debit steps to apply")
    parser.add_argument("--min-steps", type=int, default=2, help="Min steps when --steps not provided")
    parser.add_argument("--max-steps", type=int, default=6, help="Max steps when --steps not provided")
    parser.add_argument("--primary", help="Bias stat increases toward this stat key")
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

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if not args.skin and not args.campaign:
        print("error: provide --skin or --campaign", file=sys.stderr)
        return 1

    if args.tone and args.build_points is not None:
        print("error: provide only one of --tone or --build-points", file=sys.stderr)
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

    if not skin_slug or skin_slug not in skins:
        print(f"error: unknown skin '{skin_slug}'", file=sys.stderr)
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

    skin_entry = skins[skin_slug]
    skin_entry = {**skin_entry, "slug": skin_slug}

    try:
        sheet = build_sheet(
            {
                **skin_entry,
                "_gen": {
                    "steps": args.steps,
                    "min_steps": args.min_steps,
                    "max_steps": args.max_steps,
                    "primary": args.primary,
                    "build_points_budget": build_points_budget,
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
