#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

import yaml

import _sslib
import _characters
import _rules


def load_sheet(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_sheet(sheet: dict, manifest: dict) -> _sslib.ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    schema_version = sheet.get("schema_version")
    if schema_version not in (1, _characters.SHEET_SCHEMA_VERSION) or isinstance(schema_version, bool):
        errors.append(f"sheet schema_version must be 1 or 2 (got {schema_version!r})")
    elif schema_version == 1:
        warnings.append("legacy sheet has no verified advancement history; adopt an unadvanced creation snapshot explicitly before advancing")

    skin_slug = sheet.get("skin")
    if not skin_slug or not isinstance(skin_slug, str):
        errors.append("missing or invalid sheet.skin")
        return _sslib.ValidationResult(errors, warnings)

    skins = manifest.get("skins", {})
    skin = skins.get(skin_slug)
    if not skin:
        errors.append(f"unknown skin '{skin_slug}'")
        return _sslib.ValidationResult(errors, warnings)

    expected_attrs = skin.get("attributes", {})
    if not isinstance(expected_attrs, dict) or len(expected_attrs) != 5:
        errors.append(f"manifest missing attributes for skin '{skin_slug}'")
        return _sslib.ValidationResult(errors, warnings)

    stats = sheet.get("attributes")
    if not isinstance(stats, dict):
        errors.append("missing or invalid sheet.attributes")
        return _sslib.ValidationResult(errors, warnings)

    expected_keys = set(expected_attrs.keys())
    actual_keys = set(stats.keys())
    if expected_keys != actual_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        if missing:
            errors.append(f"missing attributes: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected attributes: {', '.join(extra)}")

    # Type/range checks
    for key in sorted(expected_keys & actual_keys):
        value = stats.get(key)
        if not is_int(value):
            errors.append(f"attribute {key} must be int (got {type(value).__name__})")
            continue
        if not _rules.ATTRIBUTE_MIN <= value <= _rules.ATTRIBUTE_MAX:
            errors.append(f"attribute {key} out of range ({_rules.ATTRIBUTE_MIN}-{_rules.ATTRIBUTE_MAX}): {value}")

    if isinstance(sheet.get("tracks"), dict) and "pressure" in sheet["tracks"]:
        errors.append("Pressure belongs in campaign trackers, never tracks.pressure")

    # Pools
    pools = sheet.get("pools")
    if not isinstance(pools, dict):
        errors.append("missing or invalid sheet.pools")
        return _sslib.ValidationResult(errors, warnings)
    else:
        if "pressure" in pools:
            errors.append("Pressure belongs in campaign trackers, never pools.pressure")
        extra_pool_keys = sorted(set(pools.keys()) - {"luck", "stamina", "pressure"})
        if extra_pool_keys:
            warnings.append(f"unexpected pools keys: {', '.join(extra_pool_keys)}")

    luck_key = skin.get("luck_key")
    if not luck_key or not isinstance(luck_key, str):
        errors.append(f"manifest missing luck_key for skin '{skin_slug}'")
    elif luck_key in stats and is_int(stats.get(luck_key)):
        luck_stat_value = stats[luck_key]
        luck = pools.get("luck")
        if not isinstance(luck, dict):
            errors.append("missing or invalid pools.luck")
        else:
            extra_luck_keys = sorted(set(luck.keys()) - {"name", "current", "max"})
            if extra_luck_keys:
                warnings.append(f"unexpected pools.luck keys: {', '.join(extra_luck_keys)}")
            max_value = luck.get("max")
            cur_value = luck.get("current")
            if not is_int(max_value) or not is_int(cur_value):
                errors.append("pools.luck.current and pools.luck.max must be ints")
            else:
                if max_value != luck_stat_value:
                    errors.append(
                        f"pools.luck.max ({max_value}) != luck stat {luck_key} ({luck_stat_value})"
                    )
                if cur_value < 0 or cur_value > max_value:
                    errors.append(f"pools.luck.current out of range (0-{max_value}): {cur_value}")

            expected_luck_name = skin.get("luck_name")
            actual_luck_name = luck.get("name") if isinstance(luck, dict) else None
            if expected_luck_name and actual_luck_name and expected_luck_name != actual_luck_name:
                warnings.append(
                    f"pools.luck.name '{actual_luck_name}' != expected '{expected_luck_name}' for skin"
                )

    stamina = pools.get("stamina")
    stamina_max_for_validation = None
    if not isinstance(stamina, dict):
        errors.append("missing or invalid pools.stamina")
    else:
        extra_stamina_keys = sorted(set(stamina.keys()) - {"name", "current", "max"})
        if extra_stamina_keys:
            warnings.append(f"unexpected pools.stamina keys: {', '.join(extra_stamina_keys)}")
        max_value = stamina.get("max")
        cur_value = stamina.get("current")
        if not is_int(max_value) or not is_int(cur_value):
            errors.append("pools.stamina.current and pools.stamina.max must be ints")
        else:
            if not _rules.STAMINA_MIN <= max_value <= _rules.STAMINA_MAX:
                errors.append(f"pools.stamina.max out of range ({_rules.STAMINA_MIN}-{_rules.STAMINA_MAX}): {max_value}")
            if cur_value < 0 or cur_value > max_value:
                errors.append(f"pools.stamina.current out of range (0-{max_value}): {cur_value}")
            stamina_max_for_validation = max_value

    # Replay historical purchases from a fixed creation snapshot. Repricing the
    # current scores would erase spending when creation refunds exceed the cap.
    if schema_version == _characters.SHEET_SCHEMA_VERSION:
        try:
            _characters.replay_advancement(sheet, skin)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(str(exc))
    elif schema_version == 1:
        creation = sheet.get("creation")
        if not isinstance(creation, dict):
            errors.append("legacy creation spending is missing; cannot infer advancement history")
        elif sheet.get("advancement") or creation.get("snapshot"):
            errors.append("legacy advancement metadata is ambiguous; reconcile it into schema 2")
        else:
            try:
                budget = _rules.integer(creation.get("build_points_budget"), "creation build_points_budget")
                declared = _rules.integer(creation.get("build_points_used"), "creation build_points_used")
                if budget < 0 or declared < 0:
                    raise ValueError("creation build points must be nonnegative")
                tags = _characters._tags(sheet.get("tags", []))
                needed = _rules.creation_price(stats, stamina_max_for_validation, tags)
                if needed > budget:
                    errors.append(f"build points exceeded: needed={needed} budget={budget}")
                if declared != needed:
                    errors.append("legacy declared spending differs from its current creation price; advancement history is ambiguous")
                if tags:
                    warnings.append("legacy tags have no grant provenance and are treated as bought")
            except (ValueError, TypeError, KeyError) as exc:
                errors.append(str(exc))

    # Inventory warnings
    inv = sheet.get("inventory")
    if isinstance(inv, dict):
        big_items = inv.get("big_items")
        if isinstance(big_items, list) and len(big_items) > 6:
            warnings.append(f"carry limit: big_items has {len(big_items)} items (recommended <= 6)")

    return _sslib.ValidationResult(errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a character sheet YAML against the manifest and point-buy rules.")
    parser.add_argument("--file", help="Sheet YAML file")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--character", help="Character slug or filename under campaign state")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    root = _sslib.repo_root()
    manifest = _sslib.load_manifest(root)

    if args.file:
        sheet_path = Path(args.file)
        if not sheet_path.is_absolute():
            sheet_path = root / sheet_path
    elif args.campaign:
        chars_dir = _sslib.campaign_characters_dir(args.campaign, root=root)
        try:
            sheet_path = _sslib.resolve_character_file(chars_dir, args.character)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        print("error: provide --file or --campaign", file=sys.stderr)
        return 1

    if not sheet_path.exists():
        print(f"error: file not found: {sheet_path}", file=sys.stderr)
        return 1

    sheet = load_sheet(sheet_path)
    result = validate_sheet(sheet, manifest)

    payload = {
        "file": str(sheet_path),
        "ok": result.ok(),
        "errors": result.errors,
        "warnings": result.warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if result.ok():
            print("ok")
        else:
            print("error")
        for w in result.warnings:
            print(f"warning: {w}", file=sys.stderr)
        for e in result.errors:
            print(f"error: {e}", file=sys.stderr)

    return 0 if result.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
