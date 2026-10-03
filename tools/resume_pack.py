#!/usr/bin/env python3
"""Resume from authoritative state. Public exports use an explicit field allowlist."""
import argparse
import json
from pathlib import Path
import re
import sys

import yaml

import _runtime
import _sslib

SESSION_MD_RE = re.compile(r"session_(\d+)\.md$")
SESSION_YAML_RE = re.compile(r"session_(\d+)\.ya?ml$")


def load_yaml_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping in {path.name}")
    return data


def latest_session_file(directory: Path, pattern: re.Pattern, suffixes: tuple[str, ...]) -> Path | None:
    found = [(int(match.group(1)), path) for suffix in suffixes
             for path in directory.glob(f"session_*.{suffix}")
             if (match := pattern.fullmatch(path.name))]
    return max(found, default=(0, None), key=lambda pair: (pair[0], str(pair[1])))[1]


def read_last_log_entry(path: Path, max_lines: int) -> str:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    index = text.rfind("\n## ")
    if index >= 0:
        return text[index + 1:].strip()
    if text.startswith("## "):
        return text.strip()
    return "\n".join(text.splitlines()[-max(0, max_lines):]).strip() if max_lines else ""


def public_character(sheet: dict, skin: dict) -> dict:
    attributes = sheet.get("attributes", {})
    pools = sheet.get("pools", {})
    inventory = sheet.get("inventory", {})
    inventory = inventory if isinstance(inventory, dict) else {}
    def strings(value):
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
    def pool(key):
        data = pools.get(key, {}) if isinstance(pools, dict) else {}
        data = data if isinstance(data, dict) else {}
        return {field: data.get(field) for field in ("current", "max") if type(data.get(field)) is int}
    return {"name": sheet.get("name"),
            "stats": {key: attributes[key] for key in skin.get("attributes", {})
                      if isinstance(attributes, dict) and type(attributes.get(key)) is int},
            "luck": {"name": skin.get("luck_name", "Luck"), **pool("luck")},
            "stamina": pool("stamina"),
            "tags": strings(sheet.get("tags")),
            "inventory": {key: strings(inventory.get(key)) for key in ("big_items", "small_items")}}


def collect_resume(campaign_dir: Path, manifest: dict, *, character: str | None = None,
                   public: bool = False, summary_count: int = 3, log_lines: int = 80,
                   no_log: bool = False, no_memory: bool = False, no_checkpoint: bool = False) -> dict:
    campaign = load_yaml_optional(campaign_dir / "campaign.yaml")
    skin = manifest.get("skins", {}).get(campaign.get("skin"), {})
    chars_dir = campaign_dir / "state/characters"
    sheet_paths = ([_sslib.resolve_character_file(chars_dir, character)] if character else
                   sorted([*chars_dir.glob("*.yaml"), *chars_dir.glob("*.yml")]))
    sheets = {path.stem: load_yaml_optional(path) for path in sheet_paths}
    tracker = load_yaml_optional(campaign_dir / "state/trackers/session.yaml")
    checkpoint_path = campaign_dir / "state/checkpoints/last.md"
    checkpoint = checkpoint_path.read_text(encoding="utf-8") if checkpoint_path.exists() and not no_checkpoint else ""
    basic_campaign = {key: campaign.get(key) for key in ("slug", "title", "skin", "build_points_budget")}
    characters = [public_character(sheet, skin) for sheet in sheets.values()]
    payload = {"campaign": basic_campaign, "characters": characters,
               "character": characters[0] if len(characters) == 1 else {},
               "scene": tracker.get("scene") if type(tracker.get("scene")) is int else None,
               "checkpoint": {"text": checkpoint}}
    if public:
        # Do not add paths, raw clocks, memory, logs, checkpoint metadata, or arbitrary sheet fields here.
        return payload

    memory_path = latest_session_file(campaign_dir / "state/memory", SESSION_YAML_RE, ("yaml", "yml"))
    memory = load_yaml_optional(memory_path) if memory_path and not no_memory else {}
    summaries = memory.get("summary", [])
    summaries = [summaries] if isinstance(summaries, str) else summaries
    if isinstance(summaries, list):
        memory["summary"] = summaries[-max(0, summary_count):] if summary_count > 0 else []
    log_path = latest_session_file(campaign_dir / "state/logs", SESSION_MD_RE, ("md",))
    payload.update({"tracker": tracker, "sheets": sheets, "memory": memory,
                    "log": {"last_entry": read_last_log_entry(log_path, log_lines) if log_path and not no_log else ""}})
    payload["paths"] = {"campaign": str(campaign_dir / "campaign.yaml"),
                        "characters": [str(path) for path in sheet_paths],
                        "tracker": str(campaign_dir / "state/trackers/session.yaml"),
                        "memory": str(memory_path) if memory_path and not no_memory else None,
                        "log": str(log_path) if log_path and not no_log else None}
    return payload


def print_pack(payload: dict, *, public: bool = False) -> None:
    campaign = payload["campaign"]
    print(f"Campaign: {campaign.get('title')} (skin: {campaign.get('skin')})")
    if payload.get("scene") is not None:
        print(f"Scene: {payload['scene']}")
    for character in payload["characters"]:
        stats = " ".join(f"{key} {value}" for key, value in character["stats"].items())
        luck, stamina = character["luck"], character["stamina"]
        print(f"\nCharacter: {character.get('name')}\n{stats}")
        print(f"{luck['name']} {luck.get('current')}/{luck.get('max')} | Stamina {stamina.get('current')}/{stamina.get('max')}")
    if not public:
        print("\nPrivate state:")
        print(yaml.safe_dump({key: payload[key] for key in ("tracker", "memory", "log")}, sort_keys=False, allow_unicode=True).rstrip())
    checkpoint = payload["checkpoint"]["text"]
    if checkpoint:
        print("\nLast public GM text:")
        sys.stdout.write(checkpoint)
        if not checkpoint.endswith("\n"):
            print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a campaign resume pack; public mode exports approved fields only.")
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--character")
    parser.add_argument("--summary-count", type=int, default=3)
    parser.add_argument("--log-lines", type=int, default=80)
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--no-memory", action="store_true")
    parser.add_argument("--no-checkpoint", action="store_true")
    parser.add_argument("--public", action="store_true", help="Characters and exact public checkpoint; omit all private state and paths")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--yaml", action="store_true")
    args = parser.parse_args()
    try:
        root = _sslib.repo_root()
        campaign_dir = _sslib.campaign_dir(args.campaign, root=root)
        if not (campaign_dir / "campaign.yaml").exists():
            raise ValueError("campaign not found")
        with _runtime.campaign_snapshot(campaign_dir):
            payload = collect_resume(campaign_dir, _sslib.load_manifest(root), character=args.character,
                                     public=args.public, summary_count=args.summary_count, log_lines=args.log_lines,
                                     no_log=args.no_log, no_memory=args.no_memory, no_checkpoint=args.no_checkpoint)
        if args.json:
            print(json.dumps(payload, indent=2, default=str))
        elif args.yaml:
            print(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
        else:
            print_pack(payload, public=args.public)
        return 0
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print("error: unable to read requested public resume" if args.public else f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
