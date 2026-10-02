#!/usr/bin/env python3
"""One-screen campaign status from the same privacy boundary as resume packs."""
import argparse
import json
import sys

import yaml

import _runtime
import _sslib
import resume_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact status summary for a campaign.")
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--character")
    parser.add_argument("--public", action="store_true", help="Omit all private tracking, notes, and paths")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        root = _sslib.repo_root()
        cdir = _sslib.campaign_dir(args.campaign, root=root)
        if not (cdir / "campaign.yaml").exists():
            raise ValueError("campaign not found")
        _runtime.ensure_recovered(cdir)
        pack = resume_pack.collect_resume(cdir, _sslib.load_manifest(root), character=args.character,
                                          public=args.public, summary_count=1, no_log=True, no_checkpoint=True)
        payload = {key: pack[key] for key in ("campaign", "characters", "character", "scene")}
        if not args.public:
            tracker = pack["tracker"]
            payload["tracker"] = {key: tracker.get(key) for key in ("scene", "session", "pressure", "resources", "clocks")}
            payload["memory"] = {key: pack["memory"].get(key) for key in ("summary", "threads")}
        if args.json:
            print(json.dumps(payload, indent=2, default=str))
            return 0
        campaign = payload["campaign"]
        print(f"Campaign: {campaign.get('title')} (skin: {campaign.get('skin')})")
        print(f"Scene: {payload.get('scene')}")
        for character in payload["characters"]:
            luck, stamina = character["luck"], character["stamina"]
            print(f"{character.get('name')}: {luck['name']} {luck.get('current')}/{luck.get('max')} | STM {stamina.get('current')}/{stamina.get('max')}")
        if not args.public:
            pressure = payload["tracker"].get("pressure") or {}
            tracks = pressure.get("tracks", {})
            if tracks:
                print(f"{pressure.get('name', 'Pressure')}: " + ", ".join(f"{key} {track.get('current')}/5" for key, track in tracks.items()))
                pending = sum(len(items) for track in tracks.values() for items in track.get("pending", {}).values())
                print(f"Pending step penalties: {pending}; outstanding effects: {sum(1 for e in pressure.get('effects', []) if e.get('active'))}")
            clocks = payload["tracker"].get("clocks") or {}
            if clocks:
                print("Clocks: " + ", ".join(f"{value.get('name', key)} {value.get('current')}/{value.get('max')}" for key, value in clocks.items()))
            summaries = payload["memory"].get("summary") or []
            if summaries:
                print(f"Last memory: {summaries[-1] if isinstance(summaries, list) else summaries}")
        return 0
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print("error: unable to read requested public summary" if args.public else f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
