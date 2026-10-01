"""Executable legacy migration checks; every fixture lives in a temporary directory."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _characters
import _pressure
import _resources
import _runtime
import _sslib
import migrate_campaign
import validate_campaign

FRESH = ["--fresh-pressure", "--fresh-resources", "--adopt-creation"]


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _sslib.load_manifest(ROOT)

    def fixture(self, base, skin_slug="clanfire", *, session=1, extensions=("yaml", "yml")):
        path = Path(base) / "legacy"
        for subdir in ("characters", "trackers", "memory", "logs", "checkpoints"):
            (path / "state" / subdir).mkdir(parents=True)
        skin = self.manifest["skins"][skin_slug]
        campaign = {"schema_version": 1, "slug": path.name, "title": "Legacy", "skin": skin_slug,
                    "created": "2025-01-01", "build_points_budget": 6, "notes": "Preserve these notes."}
        tracker = {"schema_version": 1, "name": "Legacy tracker", "scene": 7, "beat": 12,
                   "clocks": {"pressure": {"name": skin["pressure_track"], "current": 0, "max": 5},
                              "storm": {"name": "Storm", "current": 2, "max": 6}}, "notes": ["A private clock note"]}
        if session is not None:
            tracker["session"] = session
        _sslib.save_yaml(path / "campaign.yaml", campaign)
        _sslib.save_yaml(path / "state/trackers/session.yaml", tracker)
        for name, extension in zip(("Ada", "Eli"), extensions):
            sheet = _characters.build_sheet(skin_slug=skin_slug, skin=skin, name=name,
                      attributes={key: 10 for key in skin["attributes"]}, stamina=5,
                      build_points_budget=6, build_points_used=0)
            sheet["schema_version"] = 1
            sheet["creation"].pop("snapshot")
            sheet.pop("advancement")
            _sslib.save_yaml(path / "state/characters" / f"{name.lower()}.{extension}", sheet)
        (path / "state/logs/session_001.md").write_text("# Session 001\nExact old narration.  \n")
        _sslib.save_yaml(path / "state/memory/session_001.yaml", {"schema_version": 1, "summary": ["Earlier events"], "secrets": ["The wolf is a spirit."]})
        (path / "state/checkpoints/last.md").write_text("Exact final public reply.\n")
        return path

    def run_cli(self, path, args=FRESH, *, apply=False):
        command = [sys.executable, str(ROOT / "tools/migrate_campaign.py"), "--campaign", str(path), "--json", *args]
        if apply:
            command.append("--apply")
        result = subprocess.run(command, text=True, capture_output=True)
        data = json.loads(result.stdout) if result.returncode == 0 else None
        return result, data

    @staticmethod
    def bytes(path):
        return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}

    @staticmethod
    def edit(path, callback):
        data = _sslib.load_yaml(path)
        callback(data)
        _sslib.save_yaml(path, data)

    def assert_refused_unchanged(self, path, args=FRESH, contains=None):
        before = self.bytes(path)
        result, _ = self.run_cli(path, args, apply=True)
        self.assertNotEqual(result.returncode, 0)
        if contains:
            self.assertIn(contains, result.stderr)
        self.assertEqual(before, self.bytes(path))
        self.assertFalse((path / "state/.transaction.json").exists())

    def reviewed(self, base, skin_slug, *, actor=None, current=2, resources=None):
        skin = self.manifest["skins"][skin_slug]
        pressure = _pressure.new_pressure(skin, ["ada", "eli"])
        _pressure.change(pressure, skin, ["ada", "eli"], amount=current, source="reviewed cause", category="ambient", actor=actor)
        ppath, rpath = Path(base) / "pressure.yaml", Path(base) / "resources.yaml"
        _sslib.save_yaml(ppath, pressure)
        _sslib.save_yaml(rpath, resources if resources is not None else _resources.new_resources(skin, ["ada", "eli"]))
        return pressure, ppath, rpath

    def test_preview_and_apply_dryrun_leave_every_byte_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            before = self.bytes(path)
            for args, apply in [(FRESH, False), ([*FRESH, "--dry-run"], True)]:
                result, data = self.run_cli(path, args, apply=apply)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(data["dry_run"])
                self.assertTrue(data["tracker"]["telemetry_partial"])
                self.assertEqual(data["session_selection"]["selected"], 1)
                self.assertEqual(before, self.bytes(path))
            self.assertFalse((path / "state/.runtime.lock").exists())

    def test_apply_preserves_extensions_exact_backups_and_prior_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            before = self.bytes(path)
            result, data = self.run_cli(path, apply=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(data["dry_run"])
            self.assertFalse((path / "state/characters/eli.yaml").exists())
            originals = ["campaign.yaml", "state/trackers/session.yaml", "state/characters/ada.yaml", "state/characters/eli.yml"]
            for relative in originals:
                self.assertEqual((path / "state/migration_backup_v1" / relative).read_bytes(), before[relative])
                self.assertEqual(_sslib.load_yaml(path / relative)["schema_version"], 2)
            for relative, value in before.items():
                if relative not in originals:
                    self.assertEqual((path / relative).read_bytes(), value)
            self.assertFalse((path / "state/logs/session_001.jsonl").exists())
            self.assertEqual(data["tracker"]["beat"], 12)
            self.assertEqual(data["tracker"]["scene"], 7)
            self.assertTrue(data["tracker"]["telemetry_partial"])
            self.assertEqual(validate_campaign.validate_campaign(str(path), self.manifest).errors, [])
            self.assert_refused_unchanged(path, contains="already migrated")

    def test_session_selection_preserves_or_advances_above_all_evidence(self):
        cases = [(7, False, False, 7), (7, True, False, 8), (2, False, False, 8),
                 (None, False, False, 8), (10, False, False, 10), (7, False, True, 8)]
        for previous, collision, closed, expected in cases:
            with self.subTest(previous=previous, collision=collision, closed=closed), tempfile.TemporaryDirectory() as temp:
                path = self.fixture(temp, session=previous)
                (path / "state/memory/session_007.yml").write_text("schema_version: 1\nsummary: [An old seventh session]\n")
                old_jsonl = path / "state/logs" / ("session_007.jsonl" if collision else "session_001.jsonl")
                old_jsonl.write_bytes(b'{"historical_evidence":"do not touch"}\n')
                if closed:
                    self.edit(path / "state/trackers/session.yaml", lambda d: d.update(session_closed=True))
                evidence = {str(p.relative_to(path)): p.read_bytes() for folder in ("logs", "memory")
                            for p in (path / "state" / folder).iterdir() if p.is_file()}
                result, data = self.run_cli(path, apply=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(data["tracker"]["session"], expected)
                self.assertEqual(data["tracker"]["beat"], 12 if expected == previous else 0)
                self.assertFalse(data["tracker"]["session_closed"])
                for relative, value in evidence.items():
                    self.assertEqual((path / relative).read_bytes(), value)
                self.assertFalse((path / "state/logs" / f"session_{expected:03d}.jsonl").exists())

    def test_duplicate_character_stems_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            (path / "state/characters/ada.yml").write_bytes((path / "state/characters/ada.yaml").read_bytes())
            self.assert_refused_unchanged(path, contains="duplicate character")

    def test_explicit_pressure_resource_and_creation_decisions_are_required(self):
        for args in [[], ["--fresh-pressure"], ["--fresh-pressure", "--fresh-resources"],
                     [*FRESH, "--pressure-state", "/unused"]]:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as temp:
                path = self.fixture(temp)
                self.assert_refused_unchanged(path, args)

    def test_fresh_and_reviewed_zero_cannot_discard_nonzero_pressure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp, "free_traders_of_the_drift_marches")
            self.edit(path / "state/trackers/session.yaml", lambda d: d["clocks"]["pressure"].update(current=2))
            self.assert_refused_unchanged(path, contains="nonzero legacy Pressure")
            _, ppath, rpath = self.reviewed(temp, "free_traders_of_the_drift_marches", current=0)
            self.assert_refused_unchanged(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"], contains="conflicts")

    def test_reviewed_pressure_and_spent_resources_are_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            slug = "free_traders_of_the_drift_marches"
            skin = self.manifest["skins"][slug]
            path = self.fixture(temp, slug)
            self.edit(path / "state/trackers/session.yaml", lambda d: d["clocks"]["pressure"].update(current=2))
            pressure = _pressure.new_pressure(skin, ["ada", "eli"])
            _pressure.change(pressure, skin, ["ada", "eli"], amount=5, source="former crisis", category="ambient", actor="ada")
            _pressure.crisis(pressure, skin, ["ada", "eli"], target="ada", table_result=[1], description="Panic",
                             effects=[{"description": "Shaken", "duration": "one scene"}])
            _pressure.change(pressure, skin, ["ada", "eli"], amount=2, source="next cycle", category="ambient")
            _pressure.modifiers(pressure, skin, "ada", "EDU", [], consume=True)
            resources = _resources.new_resources(skin, ["ada", "eli"])
            resources, _ = _resources.use_resource(resources, skin, "ship_shares")
            resources, _ = _resources.use_resource(resources, skin, "ex_marine", "ada")
            ppath, rpath = Path(temp) / "pressure.yaml", Path(temp) / "resources.yaml"
            _sslib.save_yaml(ppath, pressure)
            _sslib.save_yaml(rpath, resources)
            result, data = self.run_cli(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"], apply=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(data["tracker"]["pressure"], pressure)
            self.assertEqual(data["tracker"]["resources"], resources)
            self.assertEqual(data["tracker"]["clocks"]["storm"]["current"], 2)
            self.assertEqual(validate_campaign.validate_campaign(str(path), self.manifest).errors, [])

    def test_reviewed_personal_pressure_moves_from_each_sheet_without_guessing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp, "whispers_in_the_fog")
            self.edit(path / "state/characters/ada.yaml", lambda d: d["pools"].update(pressure={"name": "Insanity", "current": 2, "max": 5}))
            self.edit(path / "state/characters/eli.yml", lambda d: d.update(tracks={"pressure": {"name": "Insanity", "current": 0, "max": 5}}))
            self.assert_refused_unchanged(path, contains="nonzero legacy Pressure")
            pressure, ppath, rpath = self.reviewed(temp, "whispers_in_the_fog", actor="ada")
            result, data = self.run_cli(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"], apply=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(data["tracker"]["pressure"], pressure)
            self.assertNotIn("pressure", data["sheets"]["ada"]["pools"])
            self.assertNotIn("tracks", data["sheets"]["eli"])
            old_ada = _sslib.load_yaml(path / "state/migration_backup_v1/state/characters/ada.yaml")
            self.assertEqual(old_ada["pools"]["pressure"]["current"], 2)

    def test_conflicting_party_and_ambiguous_shared_whispers_history_fail(self):
        for slug in ["clanfire", "whispers_in_the_fog"]:
            with self.subTest(skin=slug), tempfile.TemporaryDirectory() as temp:
                path = self.fixture(temp, slug)
                self.edit(path / "state/trackers/session.yaml", lambda d: d["clocks"]["pressure"].update(current=2))
                if slug == "clanfire":
                    self.edit(path / "state/characters/ada.yaml", lambda d: d["pools"].update(pressure={"current": 1, "max": 5}))
                _, ppath, rpath = self.reviewed(temp, slug, actor="ada" if slug == "whispers_in_the_fog" else None)
                self.assert_refused_unchanged(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"],
                                              contains="ambiguous investigator scope" if slug == "whispers_in_the_fog" else "conflicts")

    def test_import_requires_explicit_threshold_history_and_correct_filters(self):
        edits = [lambda p: p["tracks"]["party"].pop("fired_steps"),
                 lambda p: p["tracks"]["party"].update(fired_steps=[], pending={}),
                 lambda p: p["tracks"]["party"]["pending"]["ada"][0].update(attributes=["WRONG"])]
        for edit in edits:
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as temp:
                path = self.fixture(temp, "free_traders_of_the_drift_marches")
                self.edit(path / "state/trackers/session.yaml", lambda d: d["clocks"]["pressure"].update(current=2))
                pressure, ppath, rpath = self.reviewed(temp, "free_traders_of_the_drift_marches")
                edit(pressure)
                _sslib.save_yaml(ppath, pressure)
                self.assert_refused_unchanged(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"])

    def test_invalid_resource_import_duplicate_yaml_keys_and_existing_backup_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            resources = _resources.new_resources(self.manifest["skins"]["clanfire"], ["ada", "eli"])
            resources["characters"]["ada"]["totem_mark"]["used"] = 2
            rpath = Path(temp) / "resources.yaml"
            _sslib.save_yaml(rpath, resources)
            self.assert_refused_unchanged(path, ["--fresh-pressure", "--resources-state", str(rpath), "--adopt-creation"], contains=".used")
            rpath.write_text("party: {}\nparty: {}\ncharacters: {}\n")
            self.assert_refused_unchanged(path, ["--fresh-pressure", "--resources-state", str(rpath), "--adopt-creation"], contains="duplicate YAML key")
            backup = path / "state/migration_backup_v1"
            backup.mkdir()
            (backup / "precious.txt").write_text("Previous backup")
            self.assert_refused_unchanged(path, contains="backup already exists")

    def test_malformed_crisis_and_effect_history_is_refused_unchanged(self):
        edits = [lambda p: p["crises"].__setitem__(0, {}),
                 lambda p: p["crises"].clear(),
                 lambda p: p["crises"][0].update(table_result=[True]),
                 lambda p: p["effects"][0].update(description=7),
                 lambda p: p["effects"].clear()]
        for edit in edits:
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as temp:
                slug = "free_traders_of_the_drift_marches"
                path = self.fixture(temp, slug)
                skin = self.manifest["skins"][slug]
                pressure, ppath, rpath = self.reviewed(temp, slug, current=5)
                _pressure.crisis(pressure, skin, ["ada", "eli"], target="ada", table_result=[1], description="Panic",
                                 effects=[{"description": "Shaken", "duration": "one scene"}])
                edit(pressure)
                _sslib.save_yaml(ppath, pressure)
                self.assert_refused_unchanged(path, ["--pressure-state", str(ppath), "--resources-state", str(rpath), "--adopt-creation"])

    def test_invalid_or_ambiguous_legacy_state_fails_before_writing(self):
        cases = [("campaign.yaml", lambda d: d.pop("build_points_budget")),
                 ("state/characters/ada.yaml", lambda d: d.update(milestones=["unknown award"])),
                 ("state/trackers/session.yaml", lambda d: d.update(session=True)),
                 ("state/trackers/session.yaml", lambda d: d.update(pending_action={"unresolved": True})),
                 ("state/trackers/session.yaml", lambda d: d["clocks"]["storm"].update(current=8)),
                 ("state/trackers/session.yaml", lambda d: d["clocks"]["pressure"].pop("current"))]
        for relative, edit in cases:
            with self.subTest(path=relative, edit=edit), tempfile.TemporaryDirectory() as temp:
                path = self.fixture(temp)
                self.edit(path / relative, edit)
                self.assert_refused_unchanged(path)

    def test_failed_commit_rolls_back_backups_and_allows_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            (path / "state/.runtime.lock").touch()
            before = self.bytes(path)
            original = _runtime.atomic_text
            fail_path = path / "state/migration_backup_v1/state/trackers/session.yaml"
            failed = False
            def injected(destination, text):
                nonlocal failed
                if destination.resolve() == fail_path.resolve() and not failed:
                    failed = True
                    raise OSError("injected backup write failure")
                return original(destination, text)
            argv = ["migrate_campaign.py", "--campaign", str(path), *FRESH, "--apply", "--json"]
            with patch.object(sys, "argv", argv), patch.object(_runtime, "atomic_text", side_effect=injected):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(migrate_campaign.main(), 1)
            self.assertTrue(failed)
            self.assertEqual(before, self.bytes(path))
            self.assertFalse((path / "state/migration_backup_v1").exists())
            self.assertFalse((path / "state/.transaction.json").exists())
            result, _ = self.run_cli(path, apply=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_apply_recovers_interrupted_migration_before_revalidating(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.fixture(temp)
            cpath = path / "campaign.yaml"
            original = cpath.read_text()
            partial_backup = path / "state/migration_backup_v1/campaign.yaml"
            partial_backup.parent.mkdir()
            partial_backup.write_text(original)
            self.edit(cpath, lambda d: d.update(schema_version=2))
            journal = path / "state/.transaction.json"
            journal.write_text(json.dumps([{"path": str(cpath), "before": original},
                                           {"path": str(partial_backup), "before": None}]))
            before = self.bytes(path)
            preview, _ = self.run_cli(path)
            self.assertNotEqual(preview.returncode, 0)
            self.assertEqual(before, self.bytes(path))
            result, _ = self.run_cli(path, apply=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(partial_backup.read_text(), original)
            self.assertFalse(journal.exists())
            self.assertEqual(_sslib.load_yaml(cpath)["schema_version"], 2)


if __name__ == "__main__":
    unittest.main()
