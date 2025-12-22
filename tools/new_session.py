#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import sys
import yaml

import _sslib

ROOT = Path(__file__).resolve().parents[1]
SESSION_MD_RE = re.compile(r"session_(\d{3})\.md$")
SESSION_YAML_RE = re.compile(r"session_(\d{3})\.ya?ml$")


def latest_session_num(directory: Path, pattern: re.Pattern, suffixes: tuple[str, ...]) -> int:
    latest = 0
    if not directory.exists():
        return latest
    for suffix in suffixes:
        for p in directory.glob(f"session_*.{suffix}"):
            match = pattern.search(p.name)
            if not match:
                continue
            num = int(match.group(1))
            if num > latest:
                latest = num
    return latest


def load_seed_memory() -> dict:
    seed_path = ROOT / "state" / "memory" / "seed_memory.yaml"
    if seed_path.exists():
        return yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
    return {
        "schema_version": 1,
        "summary": [],
        "threads": [],
        "npcs": [],
        "secrets": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new paired session memory + log file.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--number", type=int, help="Explicit session number (default: next available)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing session files")
    parser.add_argument("--dry-run", action="store_true", help="Compute output but do not write files")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")

    args = parser.parse_args()

    root = _sslib.repo_root()
    campaign_dir = _sslib.campaign_dir(args.campaign, root=root)
    if not campaign_dir.exists():
        print(f"error: campaign not found: {campaign_dir}", file=sys.stderr)
        return 1

    memory_dir = _sslib.campaign_memory_dir(args.campaign, root=root)
    logs_dir = _sslib.campaign_logs_dir(args.campaign, root=root)

    if args.number is not None and args.number < 1:
        print("error: --number must be >= 1", file=sys.stderr)
        return 1

    if args.number is None:
        latest_mem = latest_session_num(memory_dir, SESSION_YAML_RE, ("yaml", "yml"))
        latest_log = latest_session_num(logs_dir, SESSION_MD_RE, ("md",))
        number = max(latest_mem, latest_log) + 1
    else:
        number = args.number

    memory_path = memory_dir / f"session_{number:03d}.yaml"
    log_path = logs_dir / f"session_{number:03d}.md"

    if not args.force:
        if memory_path.exists():
            print(f"error: memory session already exists: {memory_path}", file=sys.stderr)
            return 1
        if log_path.exists():
            print(f"error: log session already exists: {log_path}", file=sys.stderr)
            return 1

    payload = {
        "ok": True,
        "campaign": args.campaign,
        "number": number,
        "memory_path": str(memory_path),
        "log_path": str(log_path),
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        if args.json:
            import json

            print(json.dumps(payload, indent=2))
        else:
            print(f"dry-run: would create {memory_path}")
            print(f"dry-run: would create {log_path}")
        return 0

    memory_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    seed_memory = load_seed_memory()
    memory_path.write_text(yaml.safe_dump(seed_memory, sort_keys=False), encoding="utf-8")
    log_path.write_text(f"# Session {number:03d}\n", encoding="utf-8")

    if args.json:
        import json

        print(json.dumps(payload, indent=2))
    else:
        print(f"created {memory_path}")
        print(f"created {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
