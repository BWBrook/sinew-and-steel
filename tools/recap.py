#!/usr/bin/env python3
"""Append private session memory; mechanical changes belong to play.py."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import yaml

import _runtime
import _sslib


ROOT = Path(__file__).resolve().parents[1]
MEMORY_FIELDS = ("summary", "threads", "npcs", "secrets")
MECHANICAL_FIELDS = {"attributes", "pools", "tags", "creation", "advancement",
                     "pressure", "resources", "clocks", "combat", "tracks", "scene"}


def ensure_list(value):
    if value is None or value == "":
        return []
    return list(value) if isinstance(value, list) else [value]


def prepare_memory(path: Path, additions: dict[str, list[str]]) -> str:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    data = {} if data is None else data
    if not isinstance(data, dict) or (data and data.get("schema_version") != 1):
        raise ValueError("memory schema_version must be 1")
    if MECHANICAL_FIELDS.intersection(data):
        raise ValueError("recap accepts private memory, not a character sheet or tracker")
    data = deepcopy(data)
    data.setdefault("schema_version", 1)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for field in MEMORY_FIELDS:
        values = additions[field]
        if field == "summary":
            values = [f"[{timestamp}] {line}" for line in values]
        # Assign fresh lists, preserving both existing entries and any other
        # memory content without mutating a YAML alias elsewhere in the file.
        data[field] = deepcopy(ensure_list(data.get(field))) + values
    return yaml.safe_dump(data, sort_keys=False)


def campaign_for_path(path: Path) -> Path | None:
    for candidate in (path.absolute(), path.resolve()):
        for parent in candidate.parents:
            if (parent / "campaign.yaml").is_file():
                return parent.resolve()
    return None


def current_memory(directory: Path) -> Path:
    tracker = _sslib.load_yaml(directory / "state/trackers/session.yaml")
    number = tracker.get("session")
    if type(number) is not int or number < 1:
        raise ValueError("campaign tracker must name a positive current session")
    return directory / "state/memory" / f"session_{number:03d}.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument("--campaign", help="Campaign slug or absolute directory; use its current tracker session")
    targets.add_argument("--memory", help="Explicit private-memory YAML file")
    parser.add_argument("--summary", action="append", default=[], help="Private summary line (repeatable)")
    parser.add_argument("--thread", action="append", default=[], help="Open thread (repeatable)")
    parser.add_argument("--npc", action="append", default=[], help="NPC update (repeatable)")
    parser.add_argument("--secret", action="append", default=[], help="Secret note (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without changing files or directories")
    parser.add_argument("--json", action="store_true", help="Print changed fields; private text is not printed")
    args = parser.parse_args(argv)
    additions = dict(zip(MEMORY_FIELDS, (args.summary, args.thread, args.npc, args.secret)))
    if not any(additions.values()):
        parser.error("provide at least one --summary, --thread, --npc, or --secret")
    try:
        explicit = None
        if args.campaign:
            directory = _sslib.campaign_dir(args.campaign, root=ROOT).resolve()
        else:
            explicit = Path(args.memory).expanduser()
            if not explicit.is_absolute():
                explicit = ROOT / explicit
            directory = campaign_for_path(explicit)
            explicit = explicit.resolve()
            if directory and not explicit.is_relative_to((directory / "state/memory").resolve()):
                raise ValueError("campaign recaps must target private files inside state/memory")

        def prepare():
            path = explicit if explicit is not None else current_memory(directory)
            if directory and not path.resolve().is_relative_to((directory / "state/memory").resolve()):
                raise ValueError("campaign recaps must stay inside state/memory")
            if path.suffix not in {".yaml", ".yml"}:
                raise ValueError("private memory must be a YAML file")
            return path, prepare_memory(path, additions)

        if directory:
            with _runtime.campaign_lock(directory, dry_run=True):
                path, output = prepare()
            if not args.dry_run:
                with _runtime.campaign_lock(directory):
                    path, output = prepare()
                    _runtime.commit_files(directory / "state", {path: output})
        else:
            path, output = prepare()
            if not args.dry_run:
                _runtime.atomic_text(path, output)
        payload = {"ok": True, "memory": str(path),
                   "changed": [field for field in MEMORY_FIELDS if additions[field]],
                   "dry_run": bool(args.dry_run)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"dry-run: recap would write to {path}" if args.dry_run else f"recap saved to {path}")
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
