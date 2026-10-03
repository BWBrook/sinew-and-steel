"""Campaign I/O, transactions and structured session receipts.

Commands validate their in-memory changes before commit. A write-ahead rollback
journal and an advisory lock protect sheets, trackers and telemetry as a unit.
An interrupted commit is rolled back before the next writing command.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import fcntl
import hashlib
import json
import os
import re
import tempfile

import yaml

import _sslib


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _restore(journal: Path) -> None:
    entries = json.loads(journal.read_text(encoding="utf-8"))
    campaign_root = journal.parent.parent.resolve()
    if any(not Path(entry["path"]).resolve().is_relative_to(campaign_root) for entry in entries):
        raise ValueError("transaction journal contains a path outside this campaign")
    for entry in entries:
        path = Path(entry["path"])
        if entry["before"] is None:
            path.unlink(missing_ok=True)
        else:
            atomic_text(path, entry["before"])
    journal.unlink()


def commit_files(state_dir: Path, updates: dict[Path, str | None]) -> None:
    """Must be called while holding campaign_lock. Failed writes roll back; None deletes."""
    journal = state_dir / ".transaction.json"
    if any(not path.resolve().is_relative_to(state_dir.parent.resolve()) for path in updates):
        raise ValueError("campaign transaction cannot write outside its directory")
    if journal.exists():
        raise ValueError("unrecovered campaign transaction")
    entries = [{"path": str(path.resolve()),
                "before": path.read_text(encoding="utf-8") if path.exists() else None}
               for path in updates]
    atomic_text(journal, json.dumps(entries, ensure_ascii=False))
    try:
        for path, text in updates.items():
            if text is None:
                path.unlink(missing_ok=True)
            else:
                atomic_text(path, text)
        journal.unlink()
    except BaseException:
        _restore(journal)
        raise


@contextmanager
def campaign_lock(directory: Path, *, dry_run: bool = False):
    state = directory / "state"
    if not (directory / "campaign.yaml").exists() or not state.is_dir():
        raise ValueError(f"campaign not found: {directory}")
    journal = state / ".transaction.json"
    if dry_run:
        with campaign_snapshot(directory):
            yield
        return
    with (state / ".runtime.lock").open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        if journal.exists():
            _restore(journal)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def campaign_snapshot(directory: Path):
    """Readers share the writers' lock, so they see one whole campaign state."""
    lock = directory / "state" / ".runtime.lock"
    if not lock.exists():
        # No writer has ever run here; campaign_init creates the lock file.
        ensure_recovered(directory)
        yield
        return
    with lock.open("r", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_SH)
        try:
            ensure_recovered(directory)
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def ensure_recovered(directory: Path) -> None:
    """Readers must not report half-written state from an interrupted transaction."""
    if (directory / "state" / ".transaction.json").exists():
        raise ValueError("interrupted transaction: run `play.py --campaign <campaign> status` to recover it first")


def load_campaign(directory: Path, root: Path | None = None) -> tuple[dict, dict, dict, dict[str, dict]]:
    campaign = _sslib.load_yaml(directory / "campaign.yaml")
    manifest = _sslib.load_manifest(root)
    skin = manifest["skins"].get(campaign.get("skin"))
    if skin is None:
        raise ValueError("campaign skin is missing from manifest")
    tracker = _sslib.load_yaml(directory / "state/trackers/session.yaml")
    if tracker.get("schema_version") != 2 or "pressure" not in tracker:
        raise ValueError("legacy tracker: use migrate_campaign.py with an explicit Pressure history decision")
    paths = sorted(p for p in (directory / "state/characters").iterdir() if p.suffix in {".yaml", ".yml"})
    if len({p.stem for p in paths}) != len(paths):
        raise ValueError("duplicate character filename stems")
    sheets = {path.stem: _sslib.load_yaml(path) for path in paths}
    import validate_sheet
    for key, sheet in sheets.items():
        if sheet.get("skin") != campaign["skin"] or sheet.get("schema_version") != 2:
            raise ValueError(f"{key}: expected a schema-2 character with the campaign skin")
        validation = validate_sheet.validate_sheet(sheet, manifest)
        if not validation.ok():
            raise ValueError(f"{key}: {'; '.join(validation.errors)}")
    return campaign, skin, tracker, sheets


def retire_character(directory: Path, character: str, reason: str, *, dry_run: bool = False) -> dict:
    """Take a dead or departed character out of play between sessions, keeping the sheet."""
    import _pressure
    import _resources
    if not reason.strip():
        raise ValueError("record why the character leaves play")
    with campaign_lock(directory, dry_run=dry_run):
        campaign, skin, tracker, sheets = load_campaign(directory)
        stem = actor_key(character, sheets)
        if len(sheets) < 2:
            raise ValueError("the last character cannot retire; close the campaign instead")
        if tracker.get("pending_action") or tracker.get("combat", {}).get("active"):
            raise ValueError("finish the current action/combat before changing the party roster")
        telemetry = event_path(directory, tracker)
        started = telemetry.exists() and bool(telemetry.read_text().strip())
        if started and not tracker.get("session_closed"):
            raise ValueError("close the current session before a character retires; the roster changes between sessions")
        pressure = tracker["pressure"]
        if any(track["crisis_pending"] for track in pressure["tracks"].values()):
            raise ValueError("record the pending crisis before changing the roster")
        if pressure["scope"] == "character":
            pressure["tracks"].pop(stem, None)
        for track in pressure["tracks"].values():
            track["pending"].pop(stem, None)
        for effect in pressure["effects"]:
            if effect.get("active") and effect.get("target") == stem:
                effect.update(active=False, ended_by=f"retired: {reason}")
        sheet = sheets.pop(stem)
        old = tracker.get("resources", {})
        resources = _resources.new_resources(skin, list(sheets))
        for actor in sheets:
            resources["characters"][actor] = old.get("characters", {}).get(actor, resources["characters"][actor])
        for key, new in resources["party"].items():
            previous = old.get("party", {}).get(key)
            if previous:
                field = "used" if new["kind"] == "uses" else "current"
                # A smaller party shrinks a shared pool's capacity; spent tokens stay spent.
                new[field] = previous[field] if new.get("max") is None else min(previous[field], new["max"])
        tracker["resources"] = resources
        errors = (_pressure.validate_pressure(tracker["pressure"], skin, list(sheets))
                  + _resources.validate_resources(tracker["resources"], skin, list(sheets)))
        if errors:
            raise ValueError("; ".join(errors))
        sheet["retired"] = {"reason": reason, "session": tracker.get("session", 1)}
        path = directory / "state/characters" / f"{stem}.yaml"
        if not path.exists():
            path = path.with_suffix(".yml")
        result = {"ok": True, "retired": stem, "roster": sorted(sheets), "dry_run": dry_run}
        if not dry_run:
            commit_files(directory / "state", {
                directory / "state/characters/retired" / f"{stem}.yaml": yaml.safe_dump(sheet, sort_keys=False, allow_unicode=True),
                path: None,
                directory / "state/trackers/session.yaml": yaml.safe_dump(tracker, sort_keys=False, allow_unicode=True)})
        return result


def actor_key(character: str | None, sheets: dict[str, dict]) -> str:
    if character:
        key = Path(character).stem
        if key in sheets:
            return key
        wanted = key.casefold()
        matches = [k for k, sheet in sheets.items()
                   if wanted in {k.casefold(), str(sheet.get("name", "")).casefold()}]
        if len(matches) == 1:
            return matches[0]
        raise ValueError(f"unknown character: {character}")
    if len(sheets) == 1:
        return next(iter(sheets))
    raise ValueError("select --character when the campaign has zero or multiple characters")


def sheet_stat(sheet: dict, skin: dict, key: str) -> int:
    if key not in sheet.get("attributes", {}):
        raise ValueError(f"attribute not on sheet: {key}")
    value = (sheet["pools"]["luck"]["current"] if key == skin["luck_key"]
             else sheet["attributes"][key])
    if type(value) is not int:
        raise ValueError(f"attribute is not an integer: {key}")
    return value


def luck_change(sheet: dict, amount: int, *, actor: str, source: str,
                category: str = "recovery") -> dict:
    pool = sheet["pools"]["luck"]
    before = pool["current"]
    if type(amount) is not int or before + amount < 0:
        raise ValueError(f"not enough Luck: need {-amount}, have {before}")
    pool["current"] = min(pool["max"], before + amount)
    return {"type": "luck", "actor": actor, "source": source, "category": category,
            "requested": amount, "amount": pool["current"] - before,
            "before": before, "after": pool["current"], "maximum": pool["max"]}


def event_path(directory: Path, tracker: dict) -> Path:
    number = tracker.get("session", 1)
    return directory / "state/logs" / f"session_{number:03d}.jsonl"


def request_hash(request: dict) -> str:
    ignored = {"dry_run", "json", "event_id"}
    clean = {k: v for k, v in request.items() if k not in ignored}
    return hashlib.sha256(json.dumps(clean, sort_keys=True, default=str).encode()).hexdigest()


def receipt_path(directory: Path, event_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", event_id):
        raise ValueError("event ID must be 1..120 letters, digits, dots, hyphens or underscores")
    # IDs are case-insensitive, so every filesystem treats them alike.
    return directory / "state/receipts" / f"{event_id.lower()}.json"


def replay_receipt(directory: Path, event_id: str, request: dict, session: int | None = None) -> dict | None:
    path = receipt_path(directory, event_id)
    if not path.exists():
        return None
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt["request_hash"] != request_hash(request):
        raise ValueError("event ID was already used for a different command")
    if session is not None and receipt.get("session", session) != session:
        raise ValueError(f"event ID {event_id} was already used in session {receipt['session']}; choose a new ID")
    return {**receipt, "replayed": True}


def commit_campaign(directory: Path, campaign: dict, tracker: dict,
                    sheets: dict[str, dict], events: list[dict], result: dict, *,
                    request: dict, event_id: str, dry_run: bool,
                    initial_luck: dict | None = None, initial_pressure: dict | None = None) -> dict:
    path = event_path(directory, tracker)
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    # Split on newlines only: str.splitlines() also breaks on U+2028 and friends,
    # which JSON writes raw inside strings.
    existing = [json.loads(line) for line in prior.split("\n") if line.strip()]
    # Capture the true start of telemetry, including campaigns with no rolls yet.
    if not existing:
        events = [{"type": "session_start", "initial_luck": initial_luck or {},
                   "initial_pressure": initial_pressure or {},
                   "history_complete": not tracker.get("telemetry_partial", False)}, *events]
    base = {"schema_version": 1, "session": tracker.get("session", 1),
            "beat": tracker.get("beat", 0), "scene": tracker.get("scene", 0),
            "skin": campaign["skin"], "party_size": len(sheets),
            "event_id": event_id, "seed": request.get("seed")}
    stamped = [{**base, **event, "sequence": len(existing) + i + 1}
               for i, event in enumerate(events)]
    receipt = {"ok": True, "event_id": event_id, "request_hash": request_hash(request),
               "session": tracker.get("session", 1),
               "dry_run": dry_run, "result": result, "events": stamped}
    if not dry_run:
        lines = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True, default=str) + "\n" for event in stamped)
        updates = {directory / "state/trackers/session.yaml": yaml.safe_dump(tracker, sort_keys=False, allow_unicode=True),
                   path: prior + lines,
                   receipt_path(directory, event_id): json.dumps(receipt, indent=2, ensure_ascii=False, default=str) + "\n"}
        for key, sheet in sheets.items():
            path = directory / "state/characters" / f"{key}.yaml"
            if not path.exists() and path.with_suffix(".yml").exists():
                path = path.with_suffix(".yml")
            updates[path] = yaml.safe_dump(sheet, sort_keys=False, allow_unicode=True)
        if any(event["type"] == "session" for event in events):
            number = tracker["session"]
            public_log = directory / "state/logs" / f"session_{number:03d}.md"
            memory = directory / "state/memory" / f"session_{number:03d}.yaml"
            if public_log.exists() or memory.exists():
                raise ValueError("new session's memory/log files already exist; refusing to overwrite")
            updates[public_log] = f"# Session {number:03d}\n"
            # Threads, NPCs and secrets continue; the summary is per session.
            carried = {"threads": [], "npcs": [], "secrets": []}
            previous = directory / "state/memory" / f"session_{number - 1:03d}.yaml"
            if previous.exists():
                prior = yaml.safe_load(previous.read_text(encoding="utf-8")) or {}
                for field in carried:
                    value = prior.get(field) or []
                    carried[field] = value if isinstance(value, list) else [value]
            updates[memory] = yaml.safe_dump({"schema_version": 1, "summary": [], **carried}, sort_keys=False, allow_unicode=True)
        commit_files(directory / "state", updates)
    return receipt


def add_character(directory: Path, filename_stem: str, sheet: dict, *, dry_run: bool = False) -> dict:
    """Add a new sheet and its skin bookkeeping in one campaign transaction."""
    import _pressure
    import _resources
    with campaign_lock(directory, dry_run=dry_run):
        campaign, skin, tracker, sheets = load_campaign(directory)
        if filename_stem in sheets:
            raise ValueError("character already exists; creation cannot overwrite a played sheet")
        if sheet.get("skin") != campaign["skin"]:
            raise ValueError("character skin does not match campaign")
        if tracker.get("pending_action") or tracker.get("combat", {}).get("active"):
            raise ValueError("finish the current action/combat before changing the party roster")
        telemetry = event_path(directory, tracker)
        started = telemetry.exists() and bool(telemetry.read_text().strip())
        if started and not tracker.get("session_closed"):
            raise ValueError("close the current session before adding a character; add the new roster before opening the next session")
        old_actors = list(sheets)
        sheets[filename_stem] = sheet
        _pressure.sync_actors(tracker["pressure"], list(sheets))
        resources = _resources.new_resources(skin, list(sheets))
        old_resources = tracker.get("resources", {})
        for actor in old_actors:
            resources["characters"][actor] = old_resources.get("characters", {}).get(actor, resources["characters"][actor])
        for key, new in resources["party"].items():
            old = old_resources.get("party", {}).get(key)
            if old:
                # A larger party changes capacity, never restores a spent pool.
                field = "used" if new["kind"] == "uses" else "current"
                spent_pool = new["kind"] == "pool" and old.get("current") != old.get("max")
                if started or spent_pool or not skin["resources"][key].get("per_character"):
                    new[field] = old[field]
        tracker["resources"] = resources
        # Roster changes sit between telemetry sessions. The next session_start
        # records the new roster and balances without changing completed evidence.
        result = {"ok": True, "actor": filename_stem, "dry_run": dry_run}
        if not dry_run:
            commit_files(directory / "state", {
                directory / "state/characters" / f"{filename_stem}.yaml": yaml.safe_dump(sheet, sort_keys=False, allow_unicode=True),
                directory / "state/trackers/session.yaml": yaml.safe_dump(tracker, sort_keys=False, allow_unicode=True)})
        return result
