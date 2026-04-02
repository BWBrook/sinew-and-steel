#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys

import _delvekit


def _csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Candlelight Delvekit ASCII maps from dungeon YAML.")
    parser.add_argument("--file", required=True, help="Dungeon YAML file")
    parser.add_argument("--mode", choices=["gm", "player"], default="gm")
    parser.add_argument("--frontier", action="store_true", help="Show adjacent unknown boxes in player mode")
    parser.add_argument("--reveal-rooms", help="Comma-separated room ids to reveal temporarily")
    parser.add_argument(
        "--reveal-secret-connections",
        help="Comma-separated secret connections to reveal temporarily, formatted like 2|7,3|5",
    )
    parser.add_argument("--position", help="Room id for @ marker")
    parser.add_argument("--no-notes", action="store_true", help="Suppress connector notes legend")
    parser.add_argument("--out", help="Write rendered map to this path instead of stdout")

    args = parser.parse_args()

    payload = _delvekit.load_dungeon(args.file)
    text = _delvekit.render_map(
        payload,
        mode=args.mode,
        frontier=args.frontier,
        reveal_rooms=_csv_list(args.reveal_rooms),
        reveal_secret_connections=_csv_list(args.reveal_secret_connections),
        position=args.position,
        include_notes=not args.no_notes,
    )

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
