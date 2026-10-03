#!/usr/bin/env python3
"""Explicit, backed-up adoption of legacy state without inventing its history."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys

import yaml

import _characters
import _pressure
import _resources
import _runtime
import _sslib
import validate_sheet

SESSION_FILE = re.compile(r"session_(\d+)\.(md|ya?ml|jsonl)$")


class UniqueKeyLoader(yaml.SafeLoader):
    """A duplicate YAML key is ambiguous history, not a last-value-wins import."""


def _unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key in reviewed state: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def read_mapping(path: Path) -> dict:
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping")
    return data


def select_session(directory: Path, tracker: dict) -> dict:
    """Reserve a clean telemetry namespace without changing any earlier evidence."""
    previous = tracker.get("session")
    if previous is not None and (type(previous) is not int or previous < 1):
        raise ValueError("legacy tracker.session must be a positive integer when present")
    closed = tracker.get("session_closed", False)
    if type(closed) is not bool:
        raise ValueError("legacy tracker.session_closed must be a boolean")
    numbers, telemetry_numbers = set(), set()
    for subdirectory in ("logs", "memory"):
        folder = directory / "state" / subdirectory
        for path in folder.iterdir() if folder.exists() else []:
            if not path.is_file() or not path.name.startswith("session_"):
                continue
            match = SESSION_FILE.fullmatch(path.name)
            if not match or int(match[1]) < 1:
                raise ValueError(f"ambiguous session filename: {path.name}")
            number = int(match[1])
            numbers.add(number)
            if match[2] == "jsonl":
                telemetry_numbers.add(number)
    highest = max(numbers, default=0)
    if previous is not None and previous >= highest and previous not in telemetry_numbers and not closed:
        selected, reason = previous, "preserved explicit legacy session; no telemetry collision"
    elif previous is None and not numbers and not closed:
        selected, reason = 1, "no earlier numbered session evidence"
    else:
        selected = max(highest, previous or 0) + 1
        reason = "new telemetry session above all preserved evidence"
    return {"previous": previous, "selected": selected, "existing_numbers": sorted(numbers), "reason": reason}


def _legacy_pressure_records(tracker: dict, sheets: dict[str, dict]) -> list[tuple[str, str | None, int, dict]]:
    records = []
    if tracker.get("pressure"):
        raise ValueError("schema-1 tracker already contains structured Pressure; reconcile that partial migration explicitly")
    clocks = tracker.get("clocks", {})
    if not isinstance(clocks, dict):
        raise ValueError("legacy tracker.clocks must be a mapping")
    entries = [("tracker clocks.pressure", None, clocks["pressure"])] if "pressure" in clocks else []
    for actor, sheet in sheets.items():
        for field in ("tracks", "pools"):
            container = sheet.get(field)
            if isinstance(container, dict) and "pressure" in container:
                entries.append((f"{actor} {field}.pressure", actor, container["pressure"]))
    for label, actor, data in entries:
        if not isinstance(data, dict) or type(data.get("current")) is not int or not 0 <= data["current"] <= 5:
            raise ValueError(f"{label}: missing or ambiguous current Pressure")
        if "max" in data and (type(data["max"]) is not int or data["max"] != 5):
            raise ValueError(f"{label}: legacy Pressure maximum is ambiguous")
        records.append((label, actor, data["current"], data))
    return records


def validate_reviewed_pressure(pressure: dict, skin: dict, actors: list[str]) -> None:
    required = {"name", "scope", "tracks", "effects", "crises"}
    if not required <= pressure.keys():
        raise ValueError("reviewed Pressure must include name, scope, tracks, effects, and crises")
    if pressure["name"] != skin.get("pressure_track", "Pressure"):
        raise ValueError("reviewed Pressure name does not match the skin")
    if not isinstance(pressure["tracks"], dict):
        raise ValueError("reviewed Pressure tracks must be a mapping")
    rules = {rule["step"]: rule for rule in skin.get("pressure_steps", []) if rule["kind"] == "next_disadvantage"}
    for key, track in pressure["tracks"].items():
        if not isinstance(track, dict) or not _pressure.new_track().keys() <= track.keys():
            raise ValueError(f"Pressure {key}: missing explicit cycle, fired-step, pending, or crisis history")
        if type(track["crisis_pending"]) is not bool:
            raise ValueError(f"Pressure {key}: crisis_pending must be boolean")
        if track["tipper"] is not None and track["tipper"] not in actors:
            raise ValueError(f"Pressure {key}: unknown tipper")
    errors = _pressure.validate_pressure(pressure, skin, actors)
    if errors:
        raise ValueError("; ".join(errors))
    for key, track in pressure["tracks"].items():
        if any(step <= track["current"] and step not in track["fired_steps"] for step in rules):
            raise ValueError(f"Pressure {key}: a crossed threshold is missing from fired_steps")
        for actor, pending in track["pending"].items():
            steps = [entry["step"] for entry in pending]
            if len(steps) != len(set(steps)):
                raise ValueError(f"Pressure {key}: repeated pending step for {actor}")
            for entry in pending:
                if not isinstance(entry.get("label"), str) or not entry["label"].strip():
                    raise ValueError(f"Pressure {key}: pending penalty needs a label")
                rule = rules[entry["step"]]
                for field in ("attributes", "contexts"):
                    value = entry.get(field)
                    if not isinstance(value, list) or any(not isinstance(item, str) for item in value) or set(value) != set(rule.get(field, [])):
                        raise ValueError(f"Pressure {key}: pending {field} does not match its threshold")
    effect_ids = []
    for effect in pressure["effects"]:
        if not isinstance(effect, dict) or not {"id", "active", "target", "description", "duration"} <= effect.keys():
            raise ValueError("reviewed Pressure effects require id, active, target, description, and duration")
        if (not isinstance(effect["id"], str) or not effect["id"] or type(effect["active"]) is not bool
                or effect["target"] not in [*actors, "party"]
                or any(not isinstance(effect[field], str) or not effect[field].strip() for field in ("description", "duration"))):
            raise ValueError("reviewed Pressure effect is invalid")
        effect_ids.append(effect["id"])
    if len(set(effect_ids)) != len(effect_ids):
        raise ValueError("reviewed Pressure has duplicate effect IDs")
    cycles = {key: [] for key in pressure["tracks"]}
    required_crisis = {"type", "id", "track", "cycle", "target", "tipper", "table_result", "description", "effects"}
    for index, record in enumerate(pressure["crises"], 1):
        if not isinstance(record, dict) or not required_crisis <= record.keys():
            raise ValueError("reviewed Pressure crisis history is missing explicit consequence metadata")
        if (record["type"] != "crisis" or type(record["id"]) is not int or record["id"] != index
                or record["track"] not in cycles or type(record["cycle"]) is not int or record["cycle"] < 0
                or record["target"] not in actors or record["tipper"] not in [None, *actors]
                or (pressure["scope"] == "character" and record["target"] != record["track"])
                or not isinstance(record["description"], str) or not record["description"].strip()
                or not isinstance(record["table_result"], list) or not record["table_result"]
                or any(type(face) is not int or not 1 <= face <= 6 for face in record["table_result"])
                or not isinstance(record["effects"], list)):
            raise ValueError("reviewed Pressure crisis history has invalid consequence metadata")
        for effect in record["effects"]:
            if not isinstance(effect, dict) or effect.get("id") not in effect_ids:
                raise ValueError("reviewed Pressure crisis is missing its lasting-effect record")
        cycles[record["track"]].append(record["cycle"])
    for key, completed in cycles.items():
        if (len(completed) != pressure["tracks"][key]["cycle"]
                or sorted(completed) != list(range(len(completed)))):
            raise ValueError(f"Pressure {key}: cycle count conflicts with completed crisis history")


def reconcile_pressure(records: list, pressure: dict, actors: list[str], *, fresh: bool) -> None:
    for label, actor, current, legacy in records:
        if fresh:
            if current != 0:
                raise ValueError(f"{label}: nonzero legacy Pressure cannot be discarded; supply --pressure-state")
            if any(legacy.get(field) for field in ("fired_steps", "pending", "crisis_pending", "effects", "crises")):
                raise ValueError(f"{label}: existing history contradicts --fresh-pressure")
            continue
        if pressure["scope"] == "party":
            expected = pressure["tracks"]["party"]["current"]
        elif actor is not None:
            expected = pressure["tracks"][actor]["current"]
        elif current == 0:
            # The old scaffold always supplied a shared zero clock, even for Mournful Shores.
            continue
        elif len(actors) == 1:
            expected = pressure["tracks"][actors[0]]["current"]
        else:
            raise ValueError("nonzero shared legacy Insanity has ambiguous investigator scope; reconcile the source history first")
        if current != expected:
            raise ValueError(f"{label}: reviewed current {expected} conflicts with recorded {current}; Pressure cannot be discarded or invented")


def prepare_migration(directory: Path, manifest: dict, *, fresh_pressure: bool,
                      pressure_path: Path | None, adopt_creation: bool, fresh_resources: bool,
                      resources_path: Path | None) -> tuple[dict, dict[Path, str]]:
    if fresh_pressure == bool(pressure_path):
        raise ValueError("select exactly one of --fresh-pressure or --pressure-state")
    if fresh_resources == bool(resources_path):
        raise ValueError("select exactly one of --fresh-resources or --resources-state")
    cpath, tpath = directory / "campaign.yaml", directory / "state/trackers/session.yaml"
    campaign, tracker = read_mapping(cpath), read_mapping(tpath)
    if tracker.get("schema_version") == 2:
        raise ValueError("campaign is already migrated; do not reset its history")
    if type(campaign.get("schema_version")) is not int or campaign["schema_version"] != 1 or type(tracker.get("schema_version")) is not int or tracker["schema_version"] != 1:
        raise ValueError("migration requires an explicit schema-1 campaign and tracker")
    if campaign.get("slug") != directory.name:
        raise ValueError("campaign slug does not match its directory")
    budget = campaign.get("build_points_budget")
    if type(budget) is not int or budget < 0:
        raise ValueError("campaign creation budget is missing or ambiguous")
    skin = manifest.get("skins", {}).get(campaign.get("skin"))
    if not skin:
        raise ValueError("campaign skin is missing from manifest")
    if tracker.get("pending_action") or (isinstance(tracker.get("combat"), dict) and tracker["combat"].get("active")):
        raise ValueError("legacy action/combat is unfinished; reconcile its pending resolution before migration")
    for field in ("combat", "npcs"):
        if field in tracker and not isinstance(tracker[field], dict):
            raise ValueError(f"legacy tracker.{field} must be a mapping")
    for field in ("scene", "beat"):
        if field in tracker and (type(tracker[field]) is not int or tracker[field] < 0):
            raise ValueError(f"legacy tracker.{field} must be a nonnegative integer")
    chars_dir = directory / "state/characters"
    if not chars_dir.is_dir():
        raise ValueError("campaign character directory is missing")
    paths = sorted(path for path in chars_dir.iterdir() if path.is_file() and path.suffix in {".yaml", ".yml"})
    if len({path.stem for path in paths}) != len(paths):
        raise ValueError("duplicate character filename stems across .yaml/.yml")
    sheets = {path.stem: read_mapping(path) for path in paths}
    actors = list(sheets)
    backup = directory / "state/migration_backup_v1"
    if backup.exists():
        raise ValueError("migration backup already exists; refusing to overwrite it")
    original = {path: path.read_text(encoding="utf-8") for path in [cpath, tpath, *paths]}
    legacy_pressure = _legacy_pressure_records(tracker, sheets)
    pressure = _pressure.new_pressure(skin, actors) if fresh_pressure else read_mapping(pressure_path)
    validate_reviewed_pressure(pressure, skin, actors)
    reconcile_pressure(legacy_pressure, pressure, actors, fresh=fresh_pressure)
    for actor, sheet in list(sheets.items()):
        if sheet.get("skin") != campaign["skin"]:
            raise ValueError(f"{actor}: sheet skin does not match campaign")
        # Pressure was checked against the reviewed campaign reconstruction above.
        sheet = deepcopy(sheet)
        for field in ("tracks", "pools"):
            container = sheet.get(field)
            if isinstance(container, dict) and "pressure" in container:
                del container["pressure"]
                if field == "tracks" and not container:
                    del sheet[field]
        if sheet.get("schema_version") == 1:
            if not adopt_creation:
                raise ValueError(f"{actor}: reconstruct advancement or explicitly --adopt-creation if unadvanced")
            sheet = _characters.adopt_legacy_creation(sheet, skin)
        if sheet.get("schema_version") != 2:
            raise ValueError(f"{actor}: expected a schema-2 sheet after adoption")
        result = validate_sheet.validate_sheet(sheet, manifest)
        if not result.ok():
            raise ValueError(f"{actor}: {'; '.join(result.errors)}")
        sheets[actor] = sheet
    resources = _resources.new_resources(skin, actors) if fresh_resources else read_mapping(resources_path)
    errors = _resources.validate_resources(resources, skin, actors)
    if errors:
        raise ValueError("; ".join(errors))
    if fresh_resources and tracker.get("resources") and tracker["resources"] != resources:
        raise ValueError("recorded resource state contradicts --fresh-resources; supply reviewed --resources-state")
    clocks = tracker.setdefault("clocks", {})
    clocks.pop("pressure", None)
    for key, definition in skin.get("clocks", {}).items():
        clocks.setdefault(key, deepcopy(definition))
    for key, clock in clocks.items():
        if (not isinstance(clock, dict) or type(clock.get("max")) is not int or clock["max"] < 1
                or type(clock.get("current")) is not int or not 0 <= clock["current"] <= clock["max"]):
            raise ValueError(f"clock {key}: current/max are invalid")
    session = select_session(directory, tracker)
    tracker.update(schema_version=2, pressure=pressure, resources=resources,
                   session=session["selected"], pending_action=None, session_closed=False,
                   telemetry_partial=True)
    if session["previous"] != session["selected"]:
        tracker["beat"] = 0
    tracker.setdefault("beat", 0)
    tracker.setdefault("scene", 0)
    tracker.setdefault("npcs", {})
    tracker.setdefault("combat", {})
    campaign.update(schema_version=2, prompt_profile="compact")
    updates = {cpath: yaml.safe_dump(campaign, sort_keys=False, allow_unicode=True), tpath: yaml.safe_dump(tracker, sort_keys=False, allow_unicode=True)}
    for path in paths:
        updates[path] = yaml.safe_dump(sheets[path.stem], sort_keys=False, allow_unicode=True)
    updates.update({backup / path.relative_to(directory): text for path, text in original.items()})
    payload = {"ok": True, "campaign": campaign, "tracker": tracker, "characters": actors,
               "sheets": sheets, "session_selection": session,
               "files": [str(path.relative_to(directory)) for path in updates],
               "backup": str(backup),
               "notice": "Exact originals are backed up on apply; prior logs/memory stay unchanged. Regenerate the prompt afterward."}
    return payload, updates


def _remove_empty_backup_dirs(backup: Path) -> None:
    """Rollback removes files; remove only directories created by this failed attempt."""
    if not backup.is_dir():
        return
    paths = sorted((path for path in backup.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True)
    for path in [*paths, backup]:
        try:
            path.rmdir()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, help="Campaign slug or absolute directory")
    parser.add_argument("--fresh-pressure", action="store_true", help="Assert known fresh/crisis-reset zero with no pending effects")
    parser.add_argument("--pressure-state", type=Path, help="Reviewed complete Pressure YAML, including fired thresholds and lasting effects")
    parser.add_argument("--adopt-creation", action="store_true", help="Assert legacy characters never advanced and existing tags were all bought")
    parser.add_argument("--fresh-resources", action="store_true", help="Assert initial pool balances and unused ability limits")
    parser.add_argument("--resources-state", type=Path, help="Reviewed pool balances/use counters for ongoing play")
    parser.add_argument("--apply", action="store_true", help="Commit after validation; default is a preview")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = _sslib.repo_root()
    directory = _sslib.campaign_dir(args.campaign, root).resolve()
    dry_run = not args.apply or args.dry_run
    try:
        manifest = _sslib.load_manifest(root)
        options = {"fresh_pressure": args.fresh_pressure, "pressure_path": args.pressure_state,
                   "adopt_creation": args.adopt_creation, "fresh_resources": args.fresh_resources,
                   "resources_path": args.resources_state}
        if args.fresh_pressure == bool(args.pressure_state) or args.fresh_resources == bool(args.resources_state):
            raise ValueError("select exactly one explicit Pressure choice and one resource choice")
        journal = directory / "state/.transaction.json"
        # Validate without creating a lock file or changing any campaign bytes.
        if dry_run or not journal.exists():
            with _runtime.campaign_lock(directory, dry_run=True):
                payload, updates = prepare_migration(directory, manifest, **options)
        if not dry_run:
            backup = directory / "state/migration_backup_v1"
            new_backup_entries = []
            if journal.exists():
                entries = json.loads(journal.read_text(encoding="utf-8"))
                new_backup_entries = [entry for entry in entries if Path(entry["path"]).resolve().is_relative_to(backup.resolve())]
            with _runtime.campaign_lock(directory):
                if new_backup_entries and all(entry["before"] is None for entry in new_backup_entries):
                    _remove_empty_backup_dirs(backup)
                # Re-read under the write lock rather than committing a stale preview.
                payload, updates = prepare_migration(directory, manifest, **options)
                try:
                    _runtime.commit_files(directory / "state", updates)
                except BaseException:
                    if not (directory / "state/.transaction.json").exists():
                        _remove_empty_backup_dirs(directory / "state/migration_backup_v1")
                    raise
        payload["dry_run"] = dry_run
        print(json.dumps(payload, indent=2, default=str))
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
