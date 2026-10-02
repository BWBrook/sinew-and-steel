#!/usr/bin/env python3
"""Edit character metadata without bypassing the mechanical state ledger."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

import yaml

import _runtime
import _sslib


LIST_PATHS = {"notes", "inventory.big_items", "inventory.small_items"}
SET_PATHS = {"name", "player", "inventory", *LIST_PATHS}
METADATA_ROOTS = {"name", "player", "inventory", "notes"}


def parse_kv(item: str):
    if "=" not in item:
        raise ValueError(f"Expected key=value, got '{item}'")
    key, value = item.split("=", 1)
    return key.strip(), value.strip()


def parse_operations(sets: list[str], appends: list[str]) -> list[tuple]:
    operations = []
    for mode, items in (("set", sets), ("append", appends)):
        for item in items:
            key, raw = parse_kv(item)
            allowed = SET_PATHS if mode == "set" else LIST_PATHS
            if key not in allowed:
                raise ValueError(f"metadata only: '{key}' is not editable; use play.py or advance.py for mechanics")
            try:
                value = yaml.safe_load(raw) if raw else ""
            except yaml.YAMLError as exc:
                raise ValueError(f"invalid YAML value for '{key}': {exc}") from exc
            if key in {"name", "player"}:
                if not isinstance(value, str):
                    raise ValueError(f"'{key}' must be text")
            elif key == "inventory":
                if not isinstance(value, dict) or not set(value) <= {"big_items", "small_items"}:
                    raise ValueError("inventory accepts only big_items and small_items lists")
                if any(not isinstance(items, list) or any(not isinstance(item, str) for item in items)
                       for items in value.values()):
                    raise ValueError("inventory entries must be lists of text")
            else:
                if mode == "append" and isinstance(value, str):
                    value = [value]
                if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                    raise ValueError(f"'{key}' requires a list of text (or one text item with --append)")
            operations.append((mode, key, value))
    if not operations:
        raise ValueError("provide at least one --set or --append")
    return operations


def campaign_for_path(path: Path) -> Path | None:
    # Check the spelled and resolved paths, so --file cannot sidestep a
    # campaign transaction through a symlink.
    for candidate in (path.absolute(), path.resolve()):
        for parent in candidate.parents:
            if (parent / "campaign.yaml").is_file():
                return parent.resolve()
    return None


def _value(data: dict, key: str):
    current = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def prepare_sheet(path: Path, operations: list[tuple], allow_new: bool) -> tuple[str, list[str]]:
    original = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(original, dict) or not isinstance(original.get("attributes"), dict) or not isinstance(original.get("pools"), dict):
        raise ValueError("metadata edits require a character sheet with attributes and pools")
    data = deepcopy(original)
    for mode, key, value in operations:
        if key.startswith("inventory"):
            if "inventory" not in data and not allow_new:
                raise ValueError("missing inventory; use --allow-new for an approved metadata field")
            inventory = data.get("inventory", {})
            if not isinstance(inventory, dict):
                raise ValueError("inventory is not a mapping; refusing to replace existing content")
            # Break any YAML alias before mutation; inventory must not alias a
            # mechanical parent such as pools.
            inventory = deepcopy(inventory)
            replacements = value if key == "inventory" else {key.split(".")[1]: value}
            for field, items in replacements.items():
                if field not in inventory and not allow_new:
                    raise ValueError(f"missing inventory.{field}; use --allow-new")
                if mode == "append":
                    existing = inventory.get(field, [])
                    if not isinstance(existing, list):
                        raise ValueError(f"inventory.{field} is not a list; refusing to replace existing content")
                    inventory[field] = deepcopy(existing) + items
                else:
                    inventory[field] = deepcopy(items)
            # Whole-inventory updates merge the named lists, preserving every
            # omitted list or existing descriptive field.
            data["inventory"] = inventory
        else:
            if key not in data and not allow_new:
                raise ValueError(f"missing {key}; use --allow-new")
            if mode == "append":
                existing = data.get(key, [])
                if not isinstance(existing, list):
                    raise ValueError(f"{key} is not a list; refusing to replace existing content")
                data[key] = deepcopy(existing) + value
            else:
                data[key] = deepcopy(value)
    if any(data.get(key) != value for key, value in original.items() if key not in METADATA_ROOTS):
        raise ValueError("metadata edit would alter mechanical or other protected content")
    changed = list(dict.fromkeys(key for _, key, _ in operations if _value(original, key) != _value(data, key)))
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True), changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument("--file", help="Character YAML file; campaign files remain transactional")
    targets.add_argument("--campaign", help="Campaign slug or absolute directory")
    parser.add_argument("--character", help="Character slug or filename inside the selected campaign")
    parser.add_argument("--set", action="append", default=[], help="Set name/player/notes or inventory lists; whole inventory merges named lists")
    parser.add_argument("--append", action="append", default=[], help="Append text or a text list to notes/inventory.big_items/inventory.small_items")
    parser.add_argument("--allow-new", action="store_true", help="Create missing approved metadata keys; never unlock mechanical paths")
    parser.add_argument("--stdout", action="store_true", help="Preview YAML without writing")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing")
    parser.add_argument("--json", action="store_true", help="Print the operation summary")
    args = parser.parse_args(argv)
    if args.character and not args.campaign:
        parser.error("--character requires --campaign")
    try:
        # Validate every requested path/value before a writing lock can create
        # its lock file or recover a transaction.
        operations = parse_operations(args.set, args.append)
        root = _sslib.repo_root()
        directory = None
        if args.campaign:
            directory = _sslib.campaign_dir(args.campaign, root=root).resolve()
            path = _sslib.resolve_character_file(directory / "state/characters", args.character)
        else:
            path = Path(args.file).expanduser()
            if not path.is_absolute():
                path = root / path
            directory = campaign_for_path(path)
        path = path.resolve()
        if directory and path.parent != (directory / "state/characters").resolve():
            raise ValueError("campaign metadata edits must target a character file inside state/characters")
        preview = args.dry_run or args.stdout
        if directory:
            # Check file content without creating a lock or touching the tree.
            # Re-read under the writing lock before committing to avoid losing
            # another command's intervening sheet changes.
            with _runtime.campaign_lock(directory, dry_run=True):
                output, changed = prepare_sheet(path, operations, args.allow_new)
            if not preview and changed:
                with _runtime.campaign_lock(directory):
                    output, changed = prepare_sheet(path, operations, args.allow_new)
                    if changed:
                        _runtime.commit_files(directory / "state", {path: output})
        else:
            output, changed = prepare_sheet(path, operations, args.allow_new)
            if not preview and changed:
                _runtime.atomic_text(path, output)
        payload = {"ok": True, "file": str(path), "changed": changed, "dry_run": bool(preview)}
        if args.json:
            print(json.dumps(payload, indent=2))
        elif preview:
            print(output, end="")
        else:
            print(f"metadata saved to {path}" if changed else f"metadata unchanged: {path}")
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
