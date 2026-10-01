"""Metadata and private recaps cannot bypass mechanical transaction commands."""

from copy import deepcopy
import contextlib
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

import _runtime
import update_sheet


def hero():
    attributes = {"MGT": 10, "FLT": 10, "CUN": 10, "SPR": 10, "INS": 10}
    return {
        "schema_version": 2, "name": "Hero", "player": "", "skin": "clanfire",
        "attributes": attributes,
        "pools": {"luck": {"current": 7, "max": 10}, "stamina": {"current": 4, "max": 5}},
        "creation": {"build_points_budget": 6, "build_points_used": 2,
                     "snapshot": {"attributes": deepcopy(attributes), "stamina": 5,
                                  "bought_tags": ["Tracker"], "free_tags": []}},
        "advancement": {"entries": []}, "tags": ["Tracker"],
        "inventory": {"big_items": ["Spear"], "small_items": ["Twine"], "description": "kept inventory detail"},
        "notes": ["Old note"], "conditions": {"injured": True},
        "meta": {"generated": {"seed": 123}},
    }


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def tree(directory):
    return {str(path.relative_to(directory)): None if path.is_dir() else path.read_bytes()
            for path in directory.rglob("*")}


class StateBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.campaign = self.base / "campaign"
        self.sheet = self.campaign / "state/characters/hero.yaml"
        self.tracker = self.campaign / "state/trackers/session.yaml"
        self.memory = self.campaign / "state/memory"
        write_yaml(self.campaign / "campaign.yaml", {"skin": "clanfire", "schema_version": 2})
        write_yaml(self.sheet, hero())
        write_yaml(self.tracker, {"schema_version": 2, "session": 4, "scene": 7,
                                 "pressure": {"scope": "party", "tracks": {"party": {"current": 4}}},
                                 "clocks": {"storm": {"current": 2, "max": 6}}})
        for number in (1, 9):
            write_yaml(self.memory / f"session_{number:03d}.yaml", {
                "schema_version": 1, "summary": [f"Keep session {number}"],
                "threads": [], "npcs": [], "secrets": ["Unrevealed clue"],
            })

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, tool, *arguments):
        return subprocess.run([sys.executable, str(ROOT / "tools" / tool), *map(str, arguments)],
                              capture_output=True, text=True)

    def test_mechanical_paths_and_entire_parents_fail_before_any_write(self):
        prohibited = [
            "attributes.MGT=16", "attributes={MGT: 16}",
            "pools.luck.current=99", "pools={luck: {current: 99}}",
            "pressure.current=0", "pressure={current: 0}", "tags=[Cheat]",
            "creation.build_points_budget=999", "creation={build_points_budget: 999}",
            "advancement.entries=[]", "advancement={entries: []}",
            "resources={}", "clocks={}", "combat={}", "session=100", "scene=0",
            "tracks.pressure.current=0", "conditions.injured=false", "meta.generated.seed=999",
            "notes.pools={luck: {current: 99}}", "inventory.tags=[Cheat]",
        ]
        before = tree(self.campaign)
        for change in prohibited:
            with self.subTest(change=change):
                result = self.cli("update_sheet.py", "--campaign", self.campaign, "--character", "hero",
                                  "--set", "name=Would change", "--set", change, "--allow-new", "--json")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("metadata only", result.stderr)
                self.assertEqual(tree(self.campaign), before)

    def test_old_increment_and_clamp_bypass_flags_are_removed(self):
        before = tree(self.campaign)
        for arguments in (("--inc", "pools.luck.current=3"), ("--clamp",)):
            with self.subTest(arguments=arguments):
                result = self.cli("update_sheet.py", "--file", self.sheet, "--set", "name=Changed", *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(tree(self.campaign), before)

    def test_valid_inventory_and_note_edits_preserve_mechanics_and_existing_content(self):
        old = yaml.safe_load(self.sheet.read_text())
        tracker_before = self.tracker.read_bytes()
        result = self.cli("update_sheet.py", "--campaign", self.campaign, "--character", "hero",
                          "--append", "inventory.big_items=Rope", "--append", "notes=Met a guide",
                          "--set", "player=Barry", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        changed = yaml.safe_load(self.sheet.read_text())
        self.assertEqual(changed["inventory"]["big_items"], ["Spear", "Rope"])
        self.assertEqual(changed["inventory"]["small_items"], ["Twine"])
        self.assertEqual(changed["inventory"]["description"], "kept inventory detail")
        self.assertEqual(changed["notes"], ["Old note", "Met a guide"])
        self.assertEqual(changed["player"], "Barry")
        for key in set(old) - {"inventory", "notes", "player"}:
            self.assertEqual(changed[key], old[key], key)
        self.assertEqual(self.tracker.read_bytes(), tracker_before)
        self.assertTrue((self.campaign / "state/.runtime.lock").exists())
        self.assertFalse((self.campaign / "state/.transaction.json").exists())

    def test_direct_file_campaign_edit_still_uses_the_transaction(self):
        result = self.cli("update_sheet.py", "--file", self.sheet, "--set", "inventory={big_items: [Lantern]}", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = yaml.safe_load(self.sheet.read_text())
        self.assertEqual(saved["inventory"], {"big_items": ["Lantern"], "small_items": ["Twine"], "description": "kept inventory detail"})
        self.assertTrue((self.campaign / "state/.runtime.lock").exists())

    def test_sheet_previews_leave_the_entire_tree_unchanged(self):
        before = tree(self.campaign)
        for flag in ("--dry-run", "--stdout"):
            with self.subTest(flag=flag):
                result = self.cli("update_sheet.py", "--file", self.sheet, "--append", "notes=Preview only", flag, "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(json.loads(result.stdout)["dry_run"])
                self.assertEqual(tree(self.campaign), before)

    def test_invalid_metadata_or_parent_type_does_not_clobber_existing_values(self):
        for change in ("notes={bad: mapping}", "inventory=[]", "inventory={pools: {luck: 99}}"):
            with self.subTest(change=change):
                before = tree(self.campaign)
                result = self.cli("update_sheet.py", "--file", self.sheet, "--set", "name=Changed", "--set", change, "--allow-new")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(tree(self.campaign), before)
        data = hero()
        data["inventory"] = "Preserve this old inventory description"
        write_yaml(self.sheet, data)
        before = tree(self.campaign)
        result = self.cli("update_sheet.py", "--file", self.sheet, "--set", "name=Changed",
                          "--append", "inventory.big_items=Rope", "--allow-new")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to replace", result.stderr)
        self.assertEqual(tree(self.campaign), before)

    def test_yaml_alias_does_not_turn_a_note_append_into_a_tag_change(self):
        data = hero()
        data["notes"] = data["tags"]
        write_yaml(self.sheet, data)
        result = self.cli("update_sheet.py", "--file", self.sheet, "--append", "notes=Private detail")
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = yaml.safe_load(self.sheet.read_text())
        self.assertEqual(saved["tags"], ["Tracker"])
        self.assertEqual(saved["notes"], ["Tracker", "Private detail"])

    def test_standalone_sheet_uses_atomic_write(self):
        path = self.base / "standalone.yaml"
        write_yaml(path, hero())
        with patch.object(_runtime, "atomic_text", wraps=_runtime.atomic_text) as writer, contextlib.redirect_stdout(io.StringIO()):
            result = update_sheet.main(["--file", str(path), "--append", "notes=Standalone note"])
        self.assertEqual(result, 0)
        writer.assert_called_once()
        self.assertEqual(yaml.safe_load(path.read_text())["notes"], ["Old note", "Standalone note"])

    def test_campaign_character_selection_cannot_escape_the_campaign(self):
        outside = self.base / "outside.yaml"
        write_yaml(outside, hero())
        before = tree(self.base)
        result = self.cli("update_sheet.py", "--campaign", self.campaign, "--character", outside, "--set", "name=Changed")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree(self.base), before)

    def test_recap_has_no_tracker_mutation_flags(self):
        before = tree(self.campaign)
        for arguments in (("--pressure-inc", "1"), ("--scene-inc", "1"), ("--clock-inc", "storm=1"),
                          ("--clock-set", "storm=0"), ("--tracker", self.tracker), ("--no-clamp",)):
            with self.subTest(arguments=arguments):
                result = self.cli("recap.py", "--campaign", self.campaign, "--summary", "Would append", *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(tree(self.campaign), before)

    def test_recap_uses_tracker_session_and_keeps_all_existing_memories(self):
        before = tree(self.campaign)
        result = self.cli("recap.py", "--campaign", self.campaign, "--summary", "Current session outcome",
                          "--thread", "Follow the tracks", "--npc", "Guide agreed to help", "--secret", "The guide is lying", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(Path(payload["memory"]).resolve(), (self.memory / "session_004.yaml").resolve())
        self.assertNotIn("The guide is lying", result.stdout)
        saved = yaml.safe_load((self.memory / "session_004.yaml").read_text())
        self.assertEqual(saved["schema_version"], 1)
        self.assertTrue(saved["summary"][0].endswith("Current session outcome"))
        self.assertEqual(saved["threads"], ["Follow the tracks"])
        self.assertEqual(saved["npcs"], ["Guide agreed to help"])
        self.assertEqual(saved["secrets"], ["The guide is lying"])
        for relative, content in before.items():
            if content is not None:
                self.assertEqual((self.campaign / relative).read_bytes(), content)
        self.assertFalse((self.campaign / "state/.transaction.json").exists())

    def test_recap_preview_creates_no_current_memory_or_lock_file(self):
        before = tree(self.campaign)
        result = self.cli("recap.py", "--campaign", self.campaign, "--summary", "Preview", "--dry-run", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["dry_run"])
        self.assertEqual(tree(self.campaign), before)

    def test_recap_cannot_mistake_a_tracker_for_memory(self):
        before = tree(self.campaign)
        result = self.cli("recap.py", "--memory", self.tracker, "--summary", "Wrong target")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree(self.campaign), before)
        old_tracker = self.base / "old_tracker.yaml"
        write_yaml(old_tracker, {"schema_version": 1, "clocks": {"pressure": {"current": 4}}})
        before = tree(self.base)
        result = self.cli("recap.py", "--memory", old_tracker, "--summary", "Wrong target")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree(self.base), before)

    def test_recap_appends_without_overwriting_existing_private_content(self):
        current = self.memory / "session_004.yaml"
        old = {"schema_version": 1, "summary": ["Prior outcome"], "threads": ["Old thread"],
               "npcs": [{"name": "Guide", "motive": "Secret motive"}], "secrets": ["Old secret"],
               "custom_note": {"preserve": True}}
        write_yaml(current, old)
        result = self.cli("recap.py", "--memory", current, "--summary", "New outcome", "--secret", "New secret")
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = yaml.safe_load(current.read_text())
        self.assertEqual(saved["summary"][0], "Prior outcome")
        self.assertTrue(saved["summary"][1].endswith("New outcome"))
        self.assertEqual(saved["secrets"], ["Old secret", "New secret"])
        for key in ("threads", "npcs", "custom_note"):
            self.assertEqual(saved[key], old[key])
        self.assertTrue((self.campaign / "state/.runtime.lock").exists())


if __name__ == "__main__":
    unittest.main()
