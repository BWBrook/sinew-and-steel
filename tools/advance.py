#!/usr/bin/env python3
"""Award milestones and spend carried build points without repricing creation."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from uuid import uuid4

import yaml

import _characters
import _sslib
import _runtime
import validate_sheet


def campaign_sheet_target(path: Path) -> tuple[Path, str] | None:
    """Recognize a campaign character path, including aliases through symlinks.

    Check both the requested location and its resolved target: a linked sheet
    inside a campaign still belongs to that roster, and an outside alias must
    not bypass the real campaign's transaction boundary.
    """
    for candidate in (path.absolute(), path.resolve()):
        if candidate.parent.name == "characters" and candidate.parent.parent.name == "state":
            directory = candidate.parents[2]
            if (directory / "campaign.yaml").is_file():
                return directory.resolve(), candidate.name
    return None


def apply_operation(sheet: dict, skin: dict, args: argparse.Namespace, path: Path) -> tuple[dict, dict]:
    validation = validate_sheet.validate_sheet(sheet, {"skins": {sheet.get("skin"): skin}})
    if not validation.ok():
        raise ValueError("; ".join(validation.errors))
    before = _characters.replay_advancement(sheet, skin)
    if args.command == "award":
        sheet = _characters.award_milestone(sheet, skin, args.id, label=args.label, boon=args.boon)
    elif args.command == "raise":
        sheet = _characters.raise_stat(sheet, skin, args.stat, args.steps)
    elif args.command == "tag":
        sheet = _characters.buy_tag(sheet, skin, args.name)
    after = _characters.replay_advancement(sheet, skin)
    return sheet, {
        "ok": True, "file": str(path), "command": args.command,
        "dry_run": args.dry_run, "points_before": before["points_available"],
        **after, "sheet": sheet,
    }


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", help="Character sheet YAML file")
    common.add_argument("--campaign", help="Campaign slug under campaigns/")
    common.add_argument("--character", help="Character name or file within campaign state")
    common.add_argument("--dry-run", action="store_true", help="Validate and preview without writing")
    common.add_argument("--event-id", help="Stable campaign operation ID; retrying it returns the original receipt")
    common.add_argument("--json", action="store_true", help="Output a JSON receipt including the resulting sheet")
    parser = argparse.ArgumentParser(description=__doc__, parents=[common])
    commands = parser.add_subparsers(dest="command", required=True)
    award = commands.add_parser("award", help="Award two points, record the boon, and refill Luck")
    award.add_argument("--id", required=True, help="Unique milestone ID (prevents duplicate awards)")
    award.add_argument("--label", default="", help="Description of the milestone")
    award.add_argument("--boon", default="", help="Narrative boon agreed with the Custodian")
    raise_command = commands.add_parser("raise", help="Buy one or more +1 score increases")
    raise_command.add_argument("--stat", required=True, help="Skin attribute key, or STM for Stamina")
    raise_command.add_argument("--steps", type=int, default=1, help="Number of +1 purchases (default 1)")
    tag = commands.add_parser("tag", help="Buy a tag for two points")
    tag.add_argument("--name", required=True, help="Tag name and agreed scope")
    commands.add_parser("show", help="Validate and show available points without writing")
    global_args, remaining = common.parse_known_args()
    args = argparse.Namespace(**(vars(parser.parse_args(remaining)) | vars(global_args)))
    root = _sslib.repo_root()
    try:
        if args.file and args.campaign:
            raise ValueError("provide --file or --campaign, not both")
        if args.file:
            requested = Path(args.file)
            if not requested.is_absolute():
                requested = root / requested
            campaign_target = campaign_sheet_target(requested)
            if campaign_target:
                directory, filename = campaign_target
                args.campaign, args.character, args.file = str(directory), filename, None
        if args.campaign:
            directory = _sslib.campaign_dir(args.campaign, root=root)
            readonly = args.dry_run or args.command == "show"
            with _runtime.campaign_lock(directory, dry_run=readonly):
                request = vars(args).copy()
                event_id = args.event_id or str(uuid4())
                replayed = (_runtime.replay_receipt(directory, event_id, request)
                            if args.event_id and args.command != "show" else None)
                if replayed is not None:
                    receipt = replayed
                else:
                    campaign, skin, tracker, sheets = _runtime.load_campaign(directory, root)
                    if args.command != "show" and (tracker.get("pending_action") or tracker.get("session_closed")):
                        raise ValueError("settle the pending action or open the next session before advancing")
                    actor = _runtime.actor_key(args.character, sheets)
                    path = directory / "state/characters" / f"{actor}.yaml"
                    if not path.exists():
                        path = path.with_suffix(".yml")
                    initial_luck = {key: value["pools"]["luck"]["current"] for key, value in sheets.items()}
                    initial_pressure = deepcopy(tracker["pressure"])
                    old_sheet = sheets[actor]
                    if old_sheet.get("skin") != campaign["skin"]:
                        raise ValueError("character skin does not match its campaign")
                    luck_before = old_sheet["pools"]["luck"]["current"]
                    sheet, result = apply_operation(old_sheet, skin, args, path)
                    sheets[actor] = sheet
                    if args.command == "show":
                        receipt = result
                    else:
                        new_entries = sheet["advancement"]["entries"][len(old_sheet["advancement"]["entries"]):]
                        events = [{"type": "advancement", "actor": actor, "command": args.command,
                                   "entries": new_entries, "points_before": result["points_before"],
                                   "points_after": result["points_available"]}]
                        if args.command == "award":
                            luck_after = sheet["pools"]["luck"]["current"]
                            events.append({"type": "luck", "actor": actor, "source": f"milestone:{args.id}",
                                           "category": "recovery", "before": luck_before, "after": luck_after,
                                           "requested": luck_after - luck_before, "amount": luck_after - luck_before,
                                           "maximum": sheet["pools"]["luck"]["max"]})
                        receipt = _runtime.commit_campaign(
                            directory, campaign, tracker, sheets, events, result,
                            request=request, event_id=event_id, dry_run=args.dry_run,
                            initial_luck=initial_luck, initial_pressure=initial_pressure,
                        )
        elif args.file:
            path = Path(args.file)
            if not path.is_absolute():
                path = root / path
            sheet = _sslib.load_yaml(path)
            manifest = _sslib.load_manifest(root)
            skin = manifest["skins"].get(sheet.get("skin"))
            if skin is None:
                raise ValueError("unknown or missing sheet skin")
            sheet, receipt = apply_operation(sheet, skin, args, path)
            if not args.dry_run and args.command != "show":
                _runtime.atomic_text(path, yaml.safe_dump(sheet, sort_keys=False))
        else:
            raise ValueError("provide --file or --campaign")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        prefix = "preview" if args.dry_run else "verified" if args.command == "show" else "updated"
        result = receipt.get("result", receipt)
        print(f"{prefix} {result['file']}: {result['points_available']} build point(s) available; "
              f"{result['advancement_points_spent']} spent on advancement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
