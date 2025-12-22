#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SESSION_RE = re.compile(r"session_(\d{3})\.md$")


def find_latest_log(logs_dir: Path) -> Path | None:
    latest = None
    latest_num = -1
    for p in logs_dir.glob("session_*.md"):
        match = SESSION_RE.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    return latest


def next_log_path(logs_dir: Path) -> Path:
    latest = find_latest_log(logs_dir)
    if not latest:
        return logs_dir / "session_001.md"
    match = SESSION_RE.search(latest.name)
    num = int(match.group(1)) if match else 0
    return logs_dir / f"session_{num + 1:03d}.md"


def read_text_from_stdin() -> str:
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Append public narration or roll results to a session log.")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--file", help="Log file path to append")
    parser.add_argument("--new", action="store_true", help="Create a new session log")
    parser.add_argument("--role", help="Role label (GM, Player, System)")
    parser.add_argument("--text", help="Text to append")
    parser.add_argument("--text-file", help="Read text from file")
    parser.add_argument("--no-timestamp", action="store_true", help="Disable timestamp heading")
    parser.add_argument("--dry-run", action="store_true", help="Compute output but do not write files")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")

    args = parser.parse_args()

    log_path = None

    if args.file:
        log_path = Path(args.file)
        if not log_path.is_absolute():
            log_path = ROOT / log_path

    if args.campaign:
        campaign_dir = ROOT / "campaigns" / args.campaign
        if not campaign_dir.exists():
            print(f"error: campaign not found: {campaign_dir}", file=sys.stderr)
            return 1
        logs_dir = campaign_dir / "state" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        if log_path is None:
            if args.new:
                log_path = next_log_path(logs_dir)
            else:
                log_path = find_latest_log(logs_dir) or next_log_path(logs_dir)

    if not log_path:
        print("error: provide --campaign or --file", file=sys.stderr)
        return 1

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = read_text_from_stdin()

    if text.strip() == "":
        print("error: no text provided", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    header_parts = []
    if not args.no_timestamp:
        header_parts.append(timestamp)
    if args.role:
        header_parts.append(args.role)

    entry = text.rstrip() + "\n"
    if header_parts:
        header = " - ".join(header_parts)
        entry = f"## {header}\n\n{entry}\n"

    if args.json:
        if not args.dry_run:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(entry)

        payload = {
            "ok": True,
            "file": str(log_path),
            "dry_run": bool(args.dry_run),
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.dry_run:
        print(entry)
        return 0

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    print(f"logged to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
