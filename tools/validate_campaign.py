#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys

import yaml

import _sslib
import validate_sheet


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_campaign(campaign_slug: str, manifest: dict) -> _sslib.ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    root = _sslib.repo_root()
    cdir = _sslib.campaign_dir(campaign_slug, root=root)

    if not cdir.exists():
        errors.append(f"campaign directory missing: {cdir}")
        return _sslib.ValidationResult(errors, warnings)

    cfile = _sslib.campaign_file(campaign_slug, root=root)
    if not cfile.exists():
        errors.append(f"campaign.yaml missing: {cfile}")
        return _sslib.ValidationResult(errors, warnings)

    campaign = yaml.safe_load(cfile.read_text(encoding="utf-8")) or {}
    skin_slug = campaign.get("skin")
    if not skin_slug:
        errors.append("campaign.yaml missing skin")
        return _sslib.ValidationResult(errors, warnings)

    schema_version = campaign.get("schema_version")
    if schema_version is None:
        warnings.append("campaign.yaml missing schema_version")
    elif not isinstance(schema_version, int):
        warnings.append(f"campaign.yaml schema_version is not int: {schema_version}")

    build_points_budget = campaign.get("build_points_budget")
    if build_points_budget is None:
        warnings.append("campaign.yaml missing build_points_budget")
    elif not is_int(build_points_budget):
        errors.append(f"campaign.yaml build_points_budget is not int: {build_points_budget}")
    elif int(build_points_budget) < 0:
        errors.append(f"campaign.yaml build_points_budget must be >= 0 (got {build_points_budget})")

    name_field = campaign.get("name")
    slug_field = campaign.get("slug") or name_field
    if slug_field and slug_field != campaign_slug:
        warnings.append(f"campaign.yaml slug '{slug_field}' != folder '{campaign_slug}'")
    if campaign.get("slug") and name_field and campaign.get("slug") != name_field:
        warnings.append(f"campaign.yaml name '{name_field}' != slug '{campaign.get('slug')}'")

    skins = manifest.get("skins", {})
    skin = skins.get(skin_slug)
    if not skin:
        errors.append(f"campaign references unknown skin '{skin_slug}'")
        return _sslib.ValidationResult(errors, warnings)

    # Required dirs
    for rel_dir in (
        _sslib.campaign_state_dir(campaign_slug, root=root),
        _sslib.campaign_characters_dir(campaign_slug, root=root),
        _sslib.campaign_trackers_dir(campaign_slug, root=root),
        _sslib.campaign_memory_dir(campaign_slug, root=root),
        _sslib.campaign_logs_dir(campaign_slug, root=root),
    ):
        if not rel_dir.exists():
            errors.append(f"missing directory: {rel_dir}")

    # Tracker
    tracker_path = _sslib.campaign_trackers_dir(campaign_slug, root=root) / "session.yaml"
    if not tracker_path.exists():
        errors.append(f"missing tracker: {tracker_path}")
    else:
        tracker = yaml.safe_load(tracker_path.read_text(encoding="utf-8")) or {}
        tracker_schema = tracker.get("schema_version")
        if tracker_schema is None:
            warnings.append("tracker missing schema_version")
        elif not is_int(tracker_schema):
            warnings.append(f"tracker schema_version is not int: {tracker_schema}")

        extra_tracker_keys = sorted(set(tracker.keys()) - {"schema_version", "name", "scene", "clocks", "notes"})
        if extra_tracker_keys:
            warnings.append(f"tracker unexpected keys: {', '.join(extra_tracker_keys)}")

        scene = tracker.get("scene")
        if scene is None:
            warnings.append("tracker missing scene counter")
        elif not is_int(scene):
            errors.append("tracker scene is not an int")

        clocks = tracker.get("clocks")
        if not isinstance(clocks, dict):
            errors.append("tracker clocks missing or invalid")
        else:
            for clock_name, clock in clocks.items():
                if not isinstance(clock, dict):
                    errors.append(f"tracker clock '{clock_name}' is not a dict")
                    continue
                extra_clock_keys = sorted(set(clock.keys()) - {"name", "current", "max", "notes"})
                if extra_clock_keys:
                    warnings.append(f"tracker clock '{clock_name}' unexpected keys: {', '.join(extra_clock_keys)}")
                cur_value = clock.get("current")
                max_value = clock.get("max")
                if not is_int(cur_value) or not is_int(max_value):
                    errors.append(f"tracker clock '{clock_name}' current/max must be ints")
                else:
                    if cur_value < 0 or cur_value > max_value:
                        errors.append(
                            f"tracker clock '{clock_name}' current out of range (0-{max_value}): {cur_value}"
                        )

            pressure = clocks.get("pressure")
            if not isinstance(pressure, dict):
                errors.append("tracker missing clocks.pressure")
            else:
                cur_value = pressure.get("current")
                max_value = pressure.get("max")
                if not is_int(cur_value) or not is_int(max_value):
                    errors.append("tracker clocks.pressure current/max must be ints")
                else:
                    if max_value != 5:
                        warnings.append(f"tracker clocks.pressure.max expected 5 (got {max_value})")
                    if cur_value < 0 or cur_value > max_value:
                        errors.append(f"tracker clocks.pressure.current out of range (0-{max_value}): {cur_value}")

                expected_name = skin.get("pressure_track")
                actual_name = pressure.get("name")
                if expected_name and actual_name and expected_name != actual_name:
                    warnings.append(
                        f"tracker clocks.pressure.name '{actual_name}' != expected '{expected_name}' for skin"
                    )

    tracker_pressure = None
    if tracker_path.exists():
        try:
            tracker_data = yaml.safe_load(tracker_path.read_text(encoding="utf-8")) or {}
            tracker_pressure = (
                tracker_data.get("clocks", {}).get("pressure", {}).get("current")
                if isinstance(tracker_data.get("clocks"), dict)
                else None
            )
        except Exception:
            tracker_pressure = None

    # Characters
    chars_dir = _sslib.campaign_characters_dir(campaign_slug, root=root)
    sheets = sorted(chars_dir.glob("*.yaml"))
    if not sheets:
        warnings.append("no character sheets found")
    for sheet_path in sheets:
        try:
            sheet = validate_sheet.load_sheet(sheet_path)
        except Exception as exc:
            errors.append(f"failed to read sheet {sheet_path.name}: {exc}")
            continue

        sheet_result = validate_sheet.validate_sheet(sheet, manifest)
        for e in sheet_result.errors:
            errors.append(f"{sheet_path.name}: {e}")
        for w in sheet_result.warnings:
            warnings.append(f"{sheet_path.name}: {w}")

        # Cross-check tracker vs sheet pressure (if present)
        try:
            sheet_tracks = sheet.get("tracks") if isinstance(sheet.get("tracks"), dict) else {}
            sheet_pressure = None
            if isinstance(sheet_tracks, dict):
                pressure = sheet_tracks.get("pressure")
                if isinstance(pressure, dict):
                    sheet_pressure = pressure.get("current")
            if tracker_pressure is not None and sheet_pressure is not None:
                if is_int(tracker_pressure) and is_int(sheet_pressure):
                    if int(tracker_pressure) != int(sheet_pressure):
                        warnings.append(
                            f"{sheet_path.name}: tracks.pressure.current ({sheet_pressure}) != "
                            f"tracker clocks.pressure.current ({tracker_pressure})"
                        )
        except Exception:
            pass

    # Memory
    memory_dir = _sslib.campaign_memory_dir(campaign_slug, root=root)
    if memory_dir.exists():
        memory_files = sorted(memory_dir.glob("session_*.yaml"))
        if not memory_files:
            warnings.append("no session_*.yaml files in memory")
        for mem_path in memory_files:
            mem = yaml.safe_load(mem_path.read_text(encoding="utf-8")) or {}
            mem_schema = mem.get("schema_version")
            if mem_schema is None:
                warnings.append(f"{mem_path.name}: missing schema_version")
            elif not is_int(mem_schema):
                warnings.append(f"{mem_path.name}: schema_version is not int: {mem_schema}")
            for key in ("summary", "threads", "npcs", "secrets"):
                if key not in mem:
                    continue
                value = mem.get(key)
                if not isinstance(value, list) and not isinstance(value, str):
                    warnings.append(f"{mem_path.name}: {key} should be list or string")

    # Logs
    logs_dir = _sslib.campaign_logs_dir(campaign_slug, root=root)
    if logs_dir.exists():
        if not any(logs_dir.glob("session_*.md")):
            warnings.append("no session_*.md logs yet")

    return _sslib.ValidationResult(errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a campaign scaffold and its state files.")
    parser.add_argument("--campaign", required=True, help="Campaign slug under campaigns/")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    manifest = _sslib.load_manifest()
    result = validate_campaign(args.campaign, manifest)

    payload = {
        "campaign": args.campaign,
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
