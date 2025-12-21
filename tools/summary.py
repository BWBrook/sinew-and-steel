#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys

import yaml

import _sslib

SESSION_RE = re.compile(r"session_(\d{3})\.(md|ya?ml)$")


def load_yaml_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def latest_session_file(directory: Path, suffixes: tuple[str, ...]) -> Path | None:
    latest = None
    latest_num = -1
    for p in directory.iterdir() if directory.exists() else []:
        if not p.is_file() or p.suffix not in suffixes:
            continue
        match = SESSION_RE.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    return latest


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        if value.strip() == "":
            return []
        return [value]
    return [str(value)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a one-screen status summary for a campaign.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    root = _sslib.repo_root()
    manifest = _sslib.load_manifest(root)

    cfile = _sslib.campaign_file(args.campaign, root=root)
    if not cfile.exists():
        print(f"error: campaign not found: {cfile}", file=sys.stderr)
        return 1

    campaign = load_yaml_optional(cfile)
    skin_slug = campaign.get("skin")
    skins = manifest.get("skins", {})
    skin = skins.get(skin_slug, {})

    tracker_path = _sslib.campaign_trackers_dir(args.campaign, root=root) / "session.yaml"
    tracker = load_yaml_optional(tracker_path)

    chars_dir = _sslib.campaign_characters_dir(args.campaign, root=root)
    try:
        sheet_path = _sslib.resolve_character_file(chars_dir, args.character)
        sheet = load_yaml_optional(sheet_path)
    except FileNotFoundError:
        sheet_path = None
        sheet = {}

    memory_dir = _sslib.campaign_memory_dir(args.campaign, root=root)
    memory_path = latest_session_file(memory_dir, (".yaml", ".yml"))
    memory = load_yaml_optional(memory_path) if memory_path else {}

    logs_dir = _sslib.campaign_logs_dir(args.campaign, root=root)
    log_path = latest_session_file(logs_dir, (".md",))

    # Clocks summary
    clocks = tracker.get("clocks", {}) if isinstance(tracker.get("clocks"), dict) else {}
    clocks_out = {}
    for key, value in clocks.items():
        if not isinstance(value, dict):
            continue
        clocks_out[key] = {
            "name": value.get("name", key),
            "current": value.get("current"),
            "max": value.get("max"),
        }

    # Character summary
    stats = sheet.get("attributes") if isinstance(sheet.get("attributes"), dict) else {}
    pools = sheet.get("pools") if isinstance(sheet.get("pools"), dict) else {}
    luck = pools.get("luck") if isinstance(pools.get("luck"), dict) else {}
    stamina = pools.get("stamina") if isinstance(pools.get("stamina"), dict) else {}

    memory_summary = normalize_list(memory.get("summary"))
    last_summary = memory_summary[-1] if memory_summary else ""

    payload = {
        "campaign": {
            "slug": args.campaign,
            "skin": skin_slug,
            "created": campaign.get("created"),
        },
        "tracker": {
            "scene": tracker.get("scene"),
            "clocks": clocks_out,
        },
        "character": {
            "file": str(sheet_path) if sheet_path else None,
            "name": sheet.get("name"),
            "stats": stats,
            "luck": {
                "name": luck.get("name", skin.get("luck_name")),
                "current": luck.get("current"),
                "max": luck.get("max"),
            },
            "stamina": {
                "current": stamina.get("current"),
                "max": stamina.get("max"),
            },
        },
        "memory": {
            "file": str(memory_path) if memory_path else None,
            "last_summary": last_summary,
            "threads": normalize_list(memory.get("threads")),
        },
        "log": {
            "file": str(log_path) if log_path else None,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    skin_name = skin.get("name", skin_slug)
    print(f"Campaign: {args.campaign} (skin: {skin_name})")
    scene = tracker.get("scene")
    if scene is not None:
        print(f"Scene: {scene}")

    if clocks_out:
        pieces = []
        for key, value in clocks_out.items():
            n = value.get("name", key)
            pieces.append(f"{n} {value.get('current')}/{value.get('max')}")
        print("Clocks: " + ", ".join(pieces))

    if sheet_path:
        print(f"Character: {payload['character']['name']} ({Path(sheet_path).name})")
        if stats:
            stat_str = " ".join(f"{k} {v}" for k, v in stats.items())
            print(f"Stats: {stat_str}")
        print(
            f"Pools: {payload['character']['luck']['name']} {payload['character']['luck']['current']}/{payload['character']['luck']['max']}"
            f" | STM {payload['character']['stamina']['current']}/{payload['character']['stamina']['max']}"
        )
    else:
        print("Character: (none)")

    if last_summary:
        print(f"Last memory: {last_summary}")
    threads = payload["memory"]["threads"]
    if threads:
        print(f"Threads: {len(threads)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
