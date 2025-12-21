#!/usr/bin/env python3
import argparse
from datetime import date
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


def write_yaml(path: Path, data: dict):
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a campaign folder with state scaffolding.")
    parser.add_argument("--name", help="Campaign slug (folder name) (deprecated; use --slug/--title)")
    parser.add_argument("--slug", help="Campaign slug (folder name)")
    parser.add_argument("--title", help="Campaign title (used to derive slug if --slug not provided)")
    parser.add_argument("--skin", required=True, help="Skin slug from manifest.yaml")
    parser.add_argument("--base-dir", default="campaigns", help="Base campaigns directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--random-character", help="Optional character name to generate")

    args = parser.parse_args()

    manifest = load_manifest()
    skins = manifest.get("skins", {})
    if args.skin not in skins:
        print(f"error: unknown skin '{args.skin}'", file=sys.stderr)
        return 1

    if not args.slug and not args.name and not args.title:
        print("error: provide --slug or --title (or legacy --name)", file=sys.stderr)
        return 1

    slug = args.slug or args.name or _sslib.slugify(args.title, fallback="campaign")
    title = args.title or slug

    base_dir = Path(args.base_dir)
    if not base_dir.is_absolute():
        base_dir = ROOT / base_dir
    campaign_dir = base_dir / slug

    # Scaffold directories
    state_dir = campaign_dir / "state"
    chars_dir = state_dir / "characters"
    trackers_dir = state_dir / "trackers"
    memory_dir = state_dir / "memory"
    logs_dir = state_dir / "logs"
    checkpoints_dir = state_dir / "checkpoints"

    for d in (campaign_dir, state_dir, chars_dir, trackers_dir, memory_dir, logs_dir, checkpoints_dir):
        d.mkdir(parents=True, exist_ok=True)

    # campaign.yaml
    campaign_file = campaign_dir / "campaign.yaml"
    if campaign_file.exists() and not args.force:
        print(f"error: campaign already exists: {campaign_file}", file=sys.stderr)
        return 1

    campaign_data = {
        "schema_version": 1,
        "slug": slug,
        "title": title,
        "skin": args.skin,
        "created": date.today().isoformat(),
        "notes": "",
    }
    write_yaml(campaign_file, campaign_data)

    # tracker seed
    tracker_template = ROOT / manifest.get("templates", {}).get("tracker", "templates/tracker.yaml")
    tracker_data = yaml.safe_load(tracker_template.read_text(encoding="utf-8"))
    tracker_data = tracker_data or {}
    pressure_name = skins[args.skin].get("pressure_track", "Pressure")
    clocks = tracker_data.setdefault("clocks", {})
    pressure = clocks.setdefault("pressure", {})
    pressure["name"] = pressure_name
    pressure.setdefault("current", 0)
    pressure.setdefault("max", 5)
    tracker_out = trackers_dir / "session.yaml"
    if tracker_out.exists() and not args.force:
        pass
    else:
        write_yaml(tracker_out, tracker_data)

    # memory seed
    memory_template = ROOT / "state" / "memory" / "seed_memory.yaml"
    if memory_template.exists():
        memory_data = yaml.safe_load(memory_template.read_text(encoding="utf-8"))
        memory_out = memory_dir / "session_001.yaml"
        if not memory_out.exists() or args.force:
            write_yaml(memory_out, memory_data)

    # optional character
    if args.random_character:
        from subprocess import run
        char_path = chars_dir / f"{_sslib.slugify(args.random_character, fallback='character')}.yaml"
        if char_path.exists() and not args.force:
            print(f"warning: character already exists: {char_path}", file=sys.stderr)
        else:
            cmd = [
                sys.executable,
                str(ROOT / "tools" / "gen_character.py"),
                "--skin",
                args.skin,
                "--name",
                args.random_character,
                "--out",
                str(char_path),
            ]
            result = run(cmd)
            if result.returncode != 0:
                return result.returncode

    print(f"initialized {campaign_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
