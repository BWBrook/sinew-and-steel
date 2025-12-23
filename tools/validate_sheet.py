#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

import yaml

import _sslib


def load_sheet(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_sheet(sheet: dict, manifest: dict) -> _sslib.ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    schema_version = sheet.get("schema_version")
    if schema_version is None:
        warnings.append("sheet missing schema_version")
    elif not isinstance(schema_version, int):
        warnings.append(f"sheet schema_version is not int: {schema_version}")

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
        if value < 6 or value > 16:
            errors.append(f"attribute {key} out of range (6-16): {value}")

    # Pools
    pools = sheet.get("pools")
    if not isinstance(pools, dict):
        errors.append("missing or invalid sheet.pools")
        return _sslib.ValidationResult(errors, warnings)
    else:
        extra_pool_keys = sorted(set(pools.keys()) - {"luck", "stamina"})
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
                    warnings.append(
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
    stamina_max_for_ledger = None
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
            if max_value < 3 or max_value > 9:
                errors.append(f"pools.stamina.max out of range (3-9): {max_value}")
            if cur_value < 0 or cur_value > max_value:
                errors.append(f"pools.stamina.current out of range (0-{max_value}): {cur_value}")
            stamina_max_for_ledger = max_value

    # Build points validation (attributes baseline 10; stamina baseline 5).
    # Economy: +1 above baseline costs 2 build points; +1 below baseline costs 1 build point.
    creation = sheet.get("creation")
    if creation is None:
        warnings.append("sheet missing creation section (assuming build_points_budget=6)")
        build_points_budget = 6
        build_points_declared_used = None
    elif not isinstance(creation, dict):
        warnings.append("sheet creation is not a dict (assuming build_points_budget=6)")
        build_points_budget = 6
        build_points_declared_used = None
    else:
        budget = creation.get("build_points_budget")
        if budget is None:
            warnings.append("creation missing build_points_budget (assuming 6)")
            build_points_budget = 6
        elif not is_int(budget):
            warnings.append(f"creation build_points_budget is not int (assuming 6): {budget}")
            build_points_budget = 6
        else:
            build_points_budget = int(budget)
        if is_int(build_points_budget) and int(build_points_budget) < 0:
            errors.append(f"creation build_points_budget must be >= 0 (got {build_points_budget})")

        declared = creation.get("build_points_used")
        build_points_declared_used = int(declared) if is_int(declared) else None
        if declared is not None and build_points_declared_used is None:
            warnings.append(f"creation build_points_used is not int: {declared}")

    try:
        baselines = {key: 10 for key in stats.keys()}
        values = dict(stats)
        baselines["STM"] = 5
        if stamina_max_for_ledger is None:
            raise ValueError("missing stamina max for point-buy validation")
        values["STM"] = stamina_max_for_ledger

        needed, increases, decreases, required, slack = _sslib.build_points_needed_mixed(values, baselines)
        if needed > int(build_points_budget):
            errors.append(
                f"build points exceeded: needed={needed} budget={build_points_budget} "
                f"(increases={increases} decreases={decreases})"
            )
        if slack > 0:
            warnings.append(f"extra decreases below baseline: slack={slack} (voluntary weakness)")
        if build_points_declared_used is not None and build_points_declared_used != needed:
            warnings.append(
                f"creation build_points_used ({build_points_declared_used}) != computed needed ({needed})"
            )
    except Exception as exc:
        errors.append(f"failed to compute point-buy validation: {exc}")

    # Tracks
    tracks = sheet.get("tracks")
    if not isinstance(tracks, dict):
        errors.append("missing or invalid sheet.tracks")
    else:
        extra_track_keys = sorted(set(tracks.keys()) - {"pressure"})
        if extra_track_keys:
            warnings.append(f"unexpected tracks keys: {', '.join(extra_track_keys)}")
        pressure = tracks.get("pressure")
        if not isinstance(pressure, dict):
            errors.append("missing or invalid tracks.pressure")
        else:
            extra_pressure_keys = sorted(set(pressure.keys()) - {"name", "current", "max"})
            if extra_pressure_keys:
                warnings.append(f"unexpected tracks.pressure keys: {', '.join(extra_pressure_keys)}")
            max_value = pressure.get("max")
            cur_value = pressure.get("current")
            if not is_int(max_value) or not is_int(cur_value):
                errors.append("tracks.pressure.current and tracks.pressure.max must be ints")
            else:
                if max_value != 5:
                    warnings.append(f"tracks.pressure.max expected 5 (got {max_value})")
                if cur_value < 0 or cur_value > max_value:
                    errors.append(f"tracks.pressure.current out of range (0-{max_value}): {cur_value}")

            expected_pressure_name = skin.get("pressure_track")
            actual_pressure_name = pressure.get("name")
            if expected_pressure_name and actual_pressure_name and expected_pressure_name != actual_pressure_name:
                warnings.append(
                    f"tracks.pressure.name '{actual_pressure_name}' != expected '{expected_pressure_name}' for skin"
                )

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
