#!/usr/bin/env python3
"""Validate campaign state without migrating or otherwise changing it."""
import argparse
import json
from pathlib import Path
import sys

import yaml

import _pressure
import _resources
import _sslib
import build_prompt
import validate_sheet


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_campaign(campaign_slug: str, manifest: dict, *, root: Path | None = None) -> _sslib.ValidationResult:
    root = root or _sslib.repo_root()
    cdir = _sslib.campaign_dir(campaign_slug, root=root)
    errors, warnings = [], []

    def read(path: Path):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError("expected a mapping")
            return data
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.name}: {exc}")
            return None

    if not cdir.is_dir():
        return _sslib.ValidationResult([f"campaign directory missing: {cdir}"], [])
    campaign = read(cdir / "campaign.yaml")
    if campaign is None:
        return _sslib.ValidationResult(errors, warnings)
    if campaign.get("schema_version") != 2:
        errors.append("campaign.yaml schema_version must be 2; adopt legacy campaigns explicitly")
    if campaign.get("slug") != cdir.name:
        errors.append("campaign.yaml slug does not match the campaign folder")
    budget = campaign.get("build_points_budget")
    if not is_int(budget) or budget < 0:
        errors.append("campaign.yaml build_points_budget must be a nonnegative integer")
    if campaign.get("prompt_profile", "compact") not in {"compact", "full"}:
        errors.append("campaign.yaml prompt_profile must be compact or full")
    skin_slug = campaign.get("skin")
    skin = manifest.get("skins", {}).get(skin_slug)
    if not skin:
        return _sslib.ValidationResult(errors + [f"unknown campaign skin: {skin_slug}"], warnings)

    for relative in ("state", "state/characters", "state/trackers", "state/memory", "state/logs", "state/checkpoints"):
        if not (cdir / relative).is_dir():
            errors.append(f"missing directory: {relative}")
    sheets = sorted([*(cdir / "state/characters").glob("*.yaml"), *(cdir / "state/characters").glob("*.yml")])
    actors = [path.stem for path in sheets]
    if len(actors) != len(set(actors)):
        errors.append("character filenames have duplicate stems")
    if not sheets:
        warnings.append("no character sheets found")
    for path in sheets:
        sheet = read(path)
        if sheet is None:
            continue
        result = validate_sheet.validate_sheet(sheet, manifest)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
        if sheet.get("skin") != skin_slug:
            errors.append(f"{path.name}: skin does not match campaign")

    tracker = read(cdir / "state/trackers/session.yaml")
    if tracker is not None:
        if tracker.get("schema_version") != 2:
            errors.append("tracker schema_version must be 2; adopt legacy tracking explicitly")
        for counter in ("scene", "session"):
            if not is_int(tracker.get(counter)) or tracker[counter] < 0:
                errors.append(f"tracker {counter} must be a nonnegative integer")
        errors.extend(_pressure.validate_pressure(tracker.get("pressure"), skin, actors))
        errors.extend(_resources.validate_resources(tracker.get("resources"), skin, actors))
        clocks = tracker.get("clocks")
        if not isinstance(clocks, dict):
            errors.append("tracker clocks must be a mapping")
        else:
            if "pressure" in clocks:
                errors.append("legacy clocks.pressure duplicates structured Pressure; adopt it explicitly")
            for key, clock in clocks.items():
                if not isinstance(clock, dict):
                    errors.append(f"clock {key} must be a mapping")
                    continue
                current, maximum = clock.get("current"), clock.get("max")
                if not is_int(maximum) or maximum < 1:
                    errors.append(f"clock {key} max must be a positive integer")
                if not is_int(current) or current < 0 or (is_int(maximum) and current > maximum):
                    errors.append(f"clock {key} current must be between zero and its maximum")
            for key in skin.get("clocks", {}):
                if key not in clocks:
                    warnings.append(f"recommended skin clock missing: {key}")

    memory_files = sorted((cdir / "state/memory").glob("session_*.y*ml"))
    if not memory_files:
        warnings.append("no session memory yet")
    for path in memory_files:
        memory = read(path)
        if memory is None:
            continue
        if memory.get("schema_version") != 1:
            errors.append(f"{path.name}: memory schema_version must be 1")
        for key in ("summary", "threads", "npcs", "secrets"):
            if key in memory and not isinstance(memory[key], (list, str)):
                errors.append(f"{path.name}: {key} must be a list or string")
    if not any((cdir / "state/logs").glob("session_*.md")):
        warnings.append("no public session log yet")
    prompt = cdir / "prompt.md"
    if prompt.exists():
        errors.extend(build_prompt.check_prompt(prompt, root))
    else:
        warnings.append("no prompt.md yet; build it before starting a Custodian session")
    return _sslib.ValidationResult(errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate campaign sheets, structured Pressure, resources, and prompt freshness.")
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate_campaign(args.campaign, _sslib.load_manifest())
    payload = {"campaign": args.campaign, "ok": result.ok(), "errors": result.errors, "warnings": result.warnings}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("ok" if result.ok() else "error")
        for message in result.warnings:
            print(f"warning: {message}", file=sys.stderr)
        for message in result.errors:
            print(f"error: {message}", file=sys.stderr)
    return 0 if result.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
