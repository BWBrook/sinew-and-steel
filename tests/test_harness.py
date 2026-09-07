import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _characters
import _dice
import _delvekit
import _delvekit_output
import _pdf_common
import _sslib
import recap
import validate_sheet


class HarnessTests(unittest.TestCase):
    def test_opposed_resolution_keeps_defender_on_double_failure(self):
        attacker = {"success": False, "margin": -3}
        defender = {"success": False, "margin": -7}
        self.assertEqual(
            _dice.resolve_opposed_outcome(attacker, defender),
            {"winner": "defender", "reason": "both_failed_defender"},
        )

    def test_canonical_sheet_has_no_pressure_ledger(self):
        manifest = _sslib.load_manifest(ROOT)
        skin = {**manifest["skins"]["clanfire"], "slug": "clanfire"}
        sheet = _characters.build_sheet(
            skin_slug="clanfire",
            skin=skin,
            name="Test Hero",
            attributes={"MGT": 11, "FLT": 11, "CUN": 10, "SPR": 10, "INS": 10},
            stamina=5,
            build_points_budget=6,
            build_points_used=4,
        )
        self.assertNotIn("tracks", sheet)
        self.assertTrue(validate_sheet.validate_sheet(sheet, manifest).ok())

    def test_tag_costs_two_build_points(self):
        manifest = _sslib.load_manifest(ROOT)
        skin = {**manifest["skins"]["clanfire"], "slug": "clanfire"}
        kwargs = dict(
            skin_slug="clanfire",
            skin=skin,
            name="Tagged Hero",
            attributes={"MGT": 12, "FLT": 10, "CUN": 10, "SPR": 10, "INS": 10},
            stamina=5,
            build_points_budget=6,
        )
        one_tag = _characters.build_sheet(**kwargs, build_points_used=6, tags=["Megafauna tracker"])
        self.assertTrue(validate_sheet.validate_sheet(one_tag, manifest).ok())
        two_tags = _characters.build_sheet(**kwargs, build_points_used=8, tags=["Megafauna tracker", "Steady hands"])
        self.assertFalse(validate_sheet.validate_sheet(two_tags, manifest).ok())

    def test_generated_character_with_tag_stays_on_budget(self):
        command = [
            sys.executable, str(ROOT / "tools" / "gen_character.py"),
            "--skin", "clanfire", "--name", "Tagged", "--seed", "7",
            "--tag", "Megafauna tracker", "--dry-run", "--json",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True, cwd=ROOT)
        sheet = json.loads(result.stdout)["sheet"]
        manifest = _sslib.load_manifest(ROOT)
        self.assertEqual(sheet["tags"], ["Megafauna tracker"])
        self.assertLessEqual(sheet["creation"]["build_points_used"], 6)
        self.assertEqual(sheet["meta"]["generated"]["tags_cost"], 2)
        self.assertTrue(validate_sheet.validate_sheet(sheet, manifest).ok())

    def test_every_cli_tool_prints_help(self):
        scripts = sorted(
            p for p in (ROOT / "tools").glob("*.py")
            if not p.name.startswith("_")
        )
        self.assertGreater(len(scripts), 20)
        for script in scripts:
            with self.subTest(tool=script.name):
                result = subprocess.run(
                    [sys.executable, str(script), "--help"],
                    capture_output=True, text=True, cwd=ROOT,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-400:])

    def test_delvekit_generated_data_validates_and_renders(self):
        data = _delvekit.generate_dungeon(seed=42, size="tiny", difficulty="hard")
        self.assertIs(_delvekit.validate_dungeon(data), data)
        self.assertIn("Connector Notes", _delvekit_output.render_map(data))
        self.assertIn("## Room Key", _delvekit_output.dungeon_to_markdown(data))

    def test_seed_is_part_of_roll_receipt(self):
        command = [
            sys.executable,
            str(ROOT / "tools" / "roll.py"),
            "--seed",
            "42",
            "check",
            "--stat",
            "12",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["seed"], 42)

    def test_recap_reports_scene_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker_path = Path(temp_dir) / "session.yaml"
            tracker_path.write_text("schema_version: 1\nscene: 2\nclocks: {}\n", encoding="utf-8")
            _, changed = recap.update_tracker(tracker_path, 1, None, [], [], clamp=True)
            self.assertIn("scene", changed)

    def test_image_rewrite_preserves_angle_link_syntax(self):
        text = '![art](<../assets/art.png> "caption")'
        rewritten = _pdf_common.rewrite_markdown_image_paths(
            text=text,
            source_path=Path("rules/book/example.md"),
        )
        self.assertEqual(rewritten, '![art](<rules/assets/art.png> "caption")')


if __name__ == "__main__":
    unittest.main()
