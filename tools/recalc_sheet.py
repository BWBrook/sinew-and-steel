#!/usr/bin/env python3
"""Verify the creation/advancement ledger and refresh derived pool metadata."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys
import yaml

import _characters
import _sslib
import _runtime
from advance import campaign_sheet_target
import validate_sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="Character sheet YAML file")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename under campaign state")
    parser.add_argument("--stdout", action="store_true", help="Print the resulting sheet without writing")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    parser.add_argument("--adopt-creation", action="store_true",
                        help="Explicitly assert a schema-1 sheet has never advanced; record it as creation (all existing tags bought)")
    args = parser.parse_args()
    root = _sslib.repo_root()
    try:
        if args.file and args.campaign:
            raise ValueError("provide --file or --campaign, not both")
        if args.file:
            path = Path(args.file)
            if not path.is_absolute():
                path = root / path
        elif args.campaign:
            path = _sslib.resolve_character_file(_sslib.campaign_characters_dir(args.campaign, root=root), args.character)
        else:
            raise ValueError("provide --file or --campaign")
        campaign_target = campaign_sheet_target(path)
        directory = _sslib.campaign_dir(args.campaign, root=root).resolve() if args.campaign else None
        if directory:
            if not campaign_target or campaign_target[0] != directory:
                raise ValueError("selected sheet is outside this campaign; use its own --campaign or --file")
        elif campaign_target:
            directory, filename = campaign_target
            path = directory / "state/characters" / filename
        lock = (_runtime.campaign_lock(directory, dry_run=args.dry_run or args.stdout)
                if directory else nullcontext())
        with lock:
            data = _sslib.load_yaml(path)
            manifest = _sslib.load_manifest(root)
            skin = manifest["skins"].get(data.get("skin"))
            if not skin:
                raise ValueError("unknown or missing sheet skin")
            if data.get("schema_version") == 1:
                if not args.adopt_creation:
                    raise ValueError("legacy advancement history is ambiguous; use --adopt-creation only if this sheet has never advanced, otherwise reconstruct its real history manually")
                data = _characters.adopt_legacy_creation(data, skin)
            elif args.adopt_creation:
                raise ValueError("creation snapshot already exists; it cannot be adopted or repriced again")
            summary = _characters.replay_advancement(data, skin)
            # Refresh derived metadata only. Preserve the snapshot, creation spend,
            # every advancement entry, and all current pool values.
            luck = data["pools"]["luck"]
            luck["max"] = data["attributes"][skin["luck_key"]]
            luck["name"] = skin.get("luck_name", skin["luck_key"])
            validation = validate_sheet.validate_sheet(data, manifest)
            if not validation.ok():
                raise ValueError("; ".join(validation.errors))
            payload = {
                "ok": True, "file": str(path), "build_points_used": summary["creation_points_used"],
                "budget": data["creation"]["build_points_budget"], "details": summary,
                "dry_run": args.dry_run, "adopted_creation": args.adopt_creation,
            }
            if not args.dry_run and not args.stdout:
                output = yaml.safe_dump(data, sort_keys=False)
                if directory:
                    _runtime.commit_files(directory / "state", {path: output})
                else:
                    _runtime.atomic_text(path, output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2))
    elif args.stdout or args.dry_run:
        print(yaml.safe_dump(data, sort_keys=False))
    else:
        print(f"verified {path}: {summary['points_available']} build point(s) available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
