#!/usr/bin/env python3
import argparse
from pathlib import Path
import json
import re
import sys
import yaml

import _sslib

ROOT = Path(__file__).resolve().parents[1]
SESSION_MD_RE = re.compile(r"session_(\d{3})\.md$")
SESSION_YAML_RE = re.compile(r"session_(\d{3})\.ya?ml$")


def load_yaml_optional(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def latest_session_file(directory: Path, pattern: re.Pattern, suffix: str) -> Path | None:
    latest = None
    latest_num = -1
    for p in directory.glob(f"session_*.{suffix}"):
        match = pattern.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    return latest


def read_last_log_entry(path: Path, max_lines: int) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if text.strip() == "":
        return ""
    idx = text.rfind("\n## ")
    if idx == -1:
        if text.startswith("## "):
            return text.strip()
        # Fallback: tail N lines
        return "\n".join(text.splitlines()[-max_lines:]).strip()
    return text[idx + 1 :].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact campaign resume pack.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename")
    parser.add_argument("--summary-count", type=int, default=3, help="How many recent memory summary lines to include")
    parser.add_argument("--log-lines", type=int, default=80, help="Fallback tail length for logs without headers")
    parser.add_argument("--no-log", action="store_true", help="Skip log output")
    parser.add_argument("--no-memory", action="store_true", help="Skip memory output")
    parser.add_argument("--no-checkpoint", action="store_true", help="Skip checkpoint output")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--yaml", action="store_true", help="Output YAML")

    args = parser.parse_args()

    if args.json and args.yaml:
        print("error: choose only one of --json or --yaml", file=sys.stderr)
        return 1

    root = _sslib.repo_root()
    campaign_dir = _sslib.campaign_dir(args.campaign, root=root)
    if not campaign_dir.exists():
        print(f"error: campaign not found: {campaign_dir}", file=sys.stderr)
        return 1

    campaign_file = _sslib.campaign_file(args.campaign, root=root)
    campaign = load_yaml_optional(campaign_file)

    # Character
    chars_dir = _sslib.campaign_characters_dir(args.campaign, root=root)
    sheet_path = None
    sheet = {}
    try:
        sheet_path = _sslib.resolve_character_file(chars_dir, args.character)
        sheet = load_yaml_optional(sheet_path)
    except FileNotFoundError:
        sheet_path = None

    # Tracker
    tracker_path = _sslib.campaign_trackers_dir(args.campaign, root=root) / "session.yaml"
    tracker = load_yaml_optional(tracker_path)

    # Memory
    memory_path = None
    memory = {}
    if not args.no_memory:
        memory_dir = _sslib.campaign_memory_dir(args.campaign, root=root)
        memory_path = latest_session_file(memory_dir, SESSION_YAML_RE, "yaml")
        if memory_path:
            memory = load_yaml_optional(memory_path)

    # Logs
    log_path = None
    log_entry = ""
    if not args.no_log:
        logs_dir = _sslib.campaign_logs_dir(args.campaign, root=root)
        log_path = latest_session_file(logs_dir, SESSION_MD_RE, "md")
        if log_path:
            log_entry = read_last_log_entry(log_path, args.log_lines)

    # Checkpoint
    checkpoint_text = ""
    checkpoint_meta = {}
    checkpoint_path = None
    if not args.no_checkpoint:
        checkpoint_path = _sslib.campaign_state_dir(args.campaign, root=root) / "checkpoints" / "last.md"
        if checkpoint_path.exists():
            checkpoint_text = checkpoint_path.read_text(encoding="utf-8")
            meta_path = checkpoint_path.with_suffix(".yaml")
            if meta_path.exists():
                checkpoint_meta = load_yaml_optional(meta_path)

    # Summaries
    summaries = memory.get("summary") if isinstance(memory.get("summary"), list) else []
    if isinstance(memory.get("summary"), str):
        summaries = [memory.get("summary")]
    summaries = summaries[-max(args.summary_count, 0) :]

    payload = {
        "campaign": {
            "file": str(campaign_file) if campaign_file.exists() else None,
            "slug": campaign.get("slug") or args.campaign,
            "title": campaign.get("title") or campaign.get("name") or args.campaign,
            "skin": campaign.get("skin"),
            "created": campaign.get("created"),
            "build_points_budget": campaign.get("build_points_budget"),
        },
        "character": {
            "file": str(sheet_path) if sheet_path else None,
            "name": sheet.get("name"),
            "stats": sheet.get("attributes"),
            "luck": sheet.get("pools", {}).get("luck"),
            "stamina": sheet.get("pools", {}).get("stamina"),
        },
        "tracker": {
            "file": str(tracker_path) if tracker_path.exists() else None,
            "scene": tracker.get("scene"),
            "clocks": tracker.get("clocks"),
        },
        "memory": {
            "file": str(memory_path) if memory_path else None,
            "summary": summaries,
            "threads": memory.get("threads"),
            "npcs": memory.get("npcs"),
            "secrets": memory.get("secrets"),
        },
        "log": {
            "file": str(log_path) if log_path else None,
            "last_entry": log_entry,
        },
        "checkpoint": {
            "file": str(checkpoint_path) if checkpoint_path and checkpoint_path.exists() else None,
            "meta": checkpoint_meta,
            "text": checkpoint_text,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    if args.yaml:
        print(yaml.safe_dump(payload, sort_keys=False))
        return 0

    # Plain text output
    def print_section(title: str, body: str):
        print(f"\n== {title} ==")
        print(body.rstrip())

    camp = payload["campaign"]
    print_section(
        "Campaign",
        f"Title: {camp.get('title')}\nSlug: {camp.get('slug')}\nSkin: {camp.get('skin')}\nCreated: {camp.get('created')}\nBuild points: {camp.get('build_points_budget')}",
    )

    char = payload["character"]
    if char.get("file"):
        stats = char.get("stats") or {}
        stats_line = " ".join(f"{k} {v}" for k, v in stats.items()) if isinstance(stats, dict) else ""
        luck = char.get("luck") or {}
        stam = char.get("stamina") or {}
        print_section(
            "Character",
            f"Name: {char.get('name')}\nFile: {char.get('file')}\nStats: {stats_line}\nLuck: {luck.get('current')}/{luck.get('max')} ({luck.get('name')})\nStamina: {stam.get('current')}/{stam.get('max')}",
        )
    else:
        print_section("Character", "(none found)")

    tracker_out = payload["tracker"]
    clocks = tracker_out.get("clocks") or {}
    if isinstance(clocks, dict):
        clock_pieces = []
        for key, value in clocks.items():
            if not isinstance(value, dict):
                continue
            name = value.get("name", key)
            clock_pieces.append(f"{name} {value.get('current')}/{value.get('max')}")
        clocks_line = ", ".join(clock_pieces)
    else:
        clocks_line = ""
    print_section(
        "Tracker",
        f"Scene: {tracker_out.get('scene')}\nClocks: {clocks_line}",
    )

    if not args.no_memory:
        mem = payload["memory"]
        summary_lines = mem.get("summary") or []
        if isinstance(summary_lines, list):
            summary_text = "\n".join(summary_lines) if summary_lines else "(none)"
        else:
            summary_text = str(summary_lines)
        print_section("Memory (latest summaries)", summary_text)

    if not args.no_log:
        log = payload["log"]
        log_text = log.get("last_entry") or "(none)"
        print_section("Log (last entry)", log_text)

    if not args.no_checkpoint:
        checkpoint = payload["checkpoint"]
        checkpoint_text = checkpoint.get("text") or "(none)"
        print_section("Checkpoint (last GM text)", checkpoint_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
