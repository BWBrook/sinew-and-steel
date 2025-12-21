#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import yaml

import _sslib


def read_text(args) -> str:
    if args.text_file:
        path = Path(args.text_file)
        if not path.is_absolute():
            path = _sslib.repo_root() / path
        return path.read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    return sys.stdin.read()


def checkpoint_dir(campaign: str, root: Path) -> Path:
    return _sslib.campaign_state_dir(campaign, root=root) / "checkpoints"


def role_slug(role: str) -> str:
    return _sslib.slugify(role, fallback="role")


def write_checkpoint(
    *,
    campaign: str,
    role: str,
    root: Path,
    text: str,
    replace: bool,
    archive: bool,
) -> dict:
    cdir = checkpoint_dir(campaign, root)
    cdir.mkdir(parents=True, exist_ok=True)

    role_key = role_slug(role)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def write_pair(base: Path) -> None:
        base.write_text(text, encoding="utf-8")
        meta = {
            "schema_version": 1,
            "campaign": campaign,
            "role": role,
            "created": timestamp,
        }
        base.with_suffix(".yaml").write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")

    written = []

    if replace:
        base = cdir / f"last_{role_key}.md"
        write_pair(base)
        written.append(str(base))

    if archive:
        safe_ts = timestamp.replace(":", "").replace("-", "").replace("T", "_").replace("Z", "Z")
        base = cdir / f"checkpoint_{safe_ts}_{role_key}.md"
        write_pair(base)
        written.append(str(base))

    return {"campaign": campaign, "role": role, "written": written, "created": timestamp}


def show_checkpoint(*, campaign: str, role: str, root: Path) -> int:
    cdir = checkpoint_dir(campaign, root)
    role_key = role_slug(role)
    path = cdir / f"last_{role_key}.md"
    if not path.exists():
        print(f"error: no checkpoint found: {path}", file=sys.stderr)
        return 1
    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Save/restore exact GM text checkpoints for save-and-quit.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--role", default="GM", help="Role label for checkpoint filename")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--save", action="store_true", help="Save checkpoint (default)")
    mode.add_argument("--show", action="store_true", help="Print the latest checkpoint and exit")

    parser.add_argument("--replace", action="store_true", help="Write/overwrite last_<role>.md")
    parser.add_argument("--archive", action="store_true", help="Also write a timestamped checkpoint file")

    parser.add_argument("--text", help="Checkpoint text (exact GM message)")
    parser.add_argument("--text-file", help="Read checkpoint text from a file")
    parser.add_argument("--json", action="store_true", help="Output JSON payload")

    args = parser.parse_args()

    root = _sslib.repo_root()
    if not _sslib.campaign_dir(args.campaign, root=root).exists():
        print(f"error: campaign not found: {args.campaign}", file=sys.stderr)
        return 1

    if args.show:
        return show_checkpoint(campaign=args.campaign, role=args.role, root=root)

    # Default is save.
    text = read_text(args)
    if text == "":
        print("error: no text provided", file=sys.stderr)
        return 1

    payload = write_checkpoint(
        campaign=args.campaign,
        role=args.role,
        root=root,
        text=text,
        replace=bool(args.replace or not args.archive),
        archive=bool(args.archive),
    )

    if args.json:
        import json

        print(json.dumps(payload, indent=2))
    else:
        for path in payload["written"]:
            print(f"saved {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
