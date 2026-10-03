"""Campaign scaffolding, resource limits, privacy, and prompt freshness contracts."""
from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
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

import _pressure
import _resources
import _sslib
import build_prompt
import campaign_init
import resume_pack
import validate_campaign


class CampaignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _sslib.load_manifest(ROOT)

    def scaffold(self, base, skin="clanfire", names=None):
        path = Path(base) / "campaign"
        files = campaign_init.build_scaffold(self.manifest, skin_slug=skin, slug=path.name,
                                             title="Test party", names=names or ["Ada", "Eli"], seed=41)
        campaign_init.write_scaffold(path, files)
        return path, files

    def test_all_ten_skins_scaffold_pressure_and_resources(self):
        self.assertEqual(len(self.manifest["skins"]), 10)
        with tempfile.TemporaryDirectory() as temp:
            for slug, skin in self.manifest["skins"].items():
                with self.subTest(skin=slug):
                    path, files = self.scaffold(Path(temp) / slug, slug)
                    tracker = files["state/trackers/session.yaml"]
                    actors = ["ada", "eli"]
                    self.assertEqual(tracker["schema_version"], 2)
                    self.assertNotIn("pressure", tracker["clocks"])
                    expected = set(actors) if slug == "whispers_in_the_fog" else {"party"}
                    self.assertEqual(set(tracker["pressure"]["tracks"]), expected)
                    self.assertEqual(_pressure.validate_pressure(tracker["pressure"], skin, actors), [])
                    self.assertEqual(_resources.validate_resources(tracker["resources"], skin, actors), [])
                    result = validate_campaign.validate_campaign(str(path), self.manifest)
                    self.assertEqual(result.errors, [])
                    if slug == "twilight_of_the_northlands":
                        self.assertEqual(tracker["resources"]["party"]["companionship"]["current"], 2)
                    if slug == "free_traders_of_the_drift_marches":
                        self.assertEqual(set(tracker["clocks"]), {"fuel", "hull", "debt", "medkit"})

    def test_empty_whispers_scaffold_has_no_shared_or_phantom_investigator(self):
        files = campaign_init.build_scaffold(self.manifest, skin_slug="whispers_in_the_fog", slug="empty", title="Empty")
        tracker = files["state/trackers/session.yaml"]
        self.assertEqual(tracker["pressure"]["scope"], "character")
        self.assertEqual(tracker["pressure"]["tracks"], {})
        self.assertEqual(tracker["resources"]["characters"], {})

    def test_seeded_dryrun_contains_same_characters_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, str(ROOT / "tools/campaign_init.py"), "--slug", "dryrun", "--skin", "clanfire",
                       "--random-character", "Ada", "--random-character", "Eli", "--seed", "38", "--base-dir", temp,
                       "--dry-run", "--json"]
            first = subprocess.run(command, check=True, capture_output=True, text=True)
            second = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
            self.assertIn("state/characters/ada.yaml", json.loads(first.stdout)["files"])
            self.assertEqual(list(Path(temp).iterdir()), [])
            written = subprocess.run([arg for arg in command if arg != "--dry-run"], check=True, capture_output=True, text=True)
            self.assertTrue(json.loads(written.stdout)["ok"])
            actual = yaml.safe_load((Path(temp) / "dryrun/state/characters/ada.yaml").read_text())
            self.assertEqual(actual, json.loads(first.stdout)["files"]["state/characters/ada.yaml"])

    def test_failed_generation_leaves_no_campaign(self):
        with tempfile.TemporaryDirectory() as temp:
            argv = ["campaign_init.py", "--slug", "failed", "--skin", "clanfire", "--base-dir", temp,
                    "--random-character", "Ada"]
            with patch.object(sys, "argv", argv), patch.object(campaign_init.gen_character, "build_sheet", side_effect=ValueError("broken generation")):
                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    self.assertEqual(campaign_init.main(), 1)
            self.assertFalse((Path(temp) / "failed").exists())

    def test_force_only_fills_missing_files_and_preserves_saved_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = self.scaffold(temp)
            tracker = path / "state/trackers/session.yaml"
            original = tracker.read_text() + "private_test_note: keep this\n"
            tracker.write_text(original)
            files = campaign_init.build_scaffold(self.manifest, skin_slug="clanfire", slug=path.name,
                                                 title="Replacement title", names=["New Actor"], seed=44)
            written = campaign_init.write_scaffold(path, files)
            self.assertNotIn("state/trackers/session.yaml", written)
            self.assertEqual(tracker.read_text(), original)
            self.assertEqual(yaml.safe_load((path / "campaign.yaml").read_text())["title"], "Test party")
            self.assertTrue((path / "state/characters/new_actor.yaml").exists())

    def test_force_cannot_add_an_actor_without_updating_saved_roster(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = self.scaffold(temp)
            before = {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}
            result = subprocess.run([sys.executable, str(ROOT / "tools/campaign_init.py"), "--slug", path.name,
                                     "--base-dir", temp, "--skin", "clanfire", "--force", "--random-character", "New Hero"],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("gen_character.py --campaign", result.stderr)
            self.assertEqual(before, {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()})

    def test_public_resume_never_exports_private_canaries_in_any_format(self):
        with tempfile.TemporaryDirectory(prefix="PRIVATE_CANARY_") as temp:
            path, _ = self.scaffold(temp)
            for relative in ["campaign.yaml", "state/characters/ada.yaml", "state/trackers/session.yaml", "state/memory/session_001.yaml"]:
                file = path / relative
                data = yaml.safe_load(file.read_text())
                data["notes"] = ["PRIVATE_CANARY"]
                data["secrets"] = ["PRIVATE_CANARY"]
                if "clocks" in data:
                    data["clocks"]["PRIVATE_CANARY"] = {"name": "PRIVATE_CANARY", "current": 1, "max": 5}
                file.write_text(yaml.safe_dump(data))
            (path / "state/logs/session_001.md").write_text("## Private bookkeeping\nPRIVATE_CANARY\n")
            (path / "state/checkpoints/last.yaml").write_text("notes: PRIVATE_CANARY\n")
            exact = "You see a gate.  \n\nWhat next?\n![](public-map.png)\n"
            (path / "state/checkpoints/last.md").write_text(exact)
            public = resume_pack.collect_resume(path, self.manifest, public=True)
            self.assertEqual(public["checkpoint"]["text"], exact)
            self.assertNotIn("PRIVATE_CANARY", json.dumps(public))
            self.assertNotIn("tracker", public)
            self.assertNotIn("memory", public)
            self.assertNotIn("log", public)
            private = resume_pack.collect_resume(path, self.manifest)
            self.assertIn("PRIVATE_CANARY", json.dumps(private))
            for tool, formats in [("resume_pack.py", [[], ["--json"], ["--yaml"]]), ("summary.py", [[], ["--json"]])]:
                for format_args in formats:
                    result = subprocess.run([sys.executable, str(ROOT / "tools" / tool), "--campaign", str(path),
                                             "--public", *format_args], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn("PRIVATE_CANARY", result.stdout + result.stderr)
                    self.assertNotIn(str(path), result.stdout + result.stderr)

    def test_chat_prompts_default_to_the_full_books(self):
        def build(*extra):
            output = io.StringIO()
            argv = ["build_prompt.py", "--skin", "clanfire", "--mode", "chat", "--dry-run", "--json", *extra]
            with patch.object(sys, "argv", argv), redirect_stdout(output):
                self.assertEqual(build_prompt.main(), 0)
            return json.loads(output.getvalue())
        self.assertEqual(build()["profile"], "full")
        self.assertEqual(build("--profile", "compact")["profile"], "compact")
        compact, _ = build_prompt.assemble_prompt(self.manifest, "clanfire", mode="chat")
        self.assertIn("do not invent a procedure", compact)
        self.assertNotIn("tools/build_prompt.py --section", compact)

    def test_campaign_files_and_prompt_are_owner_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path, files = self.scaffold(temp)
            argv = ["build_prompt.py", "--campaign", str(path)]
            with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                self.assertEqual(build_prompt.main(), 0)
            for relative in [*files, "prompt.md"]:
                self.assertEqual((path / relative).stat().st_mode & 0o777, 0o600, relative)

    def test_prompt_fingerprint_tracks_state_source_inventory_and_body(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = self.scaffold(temp)
            (path / "state/memory/hidden_scenario.md").write_text("The wolf is a spirit.\n")
            (path / "state/checkpoints/last.md").write_text("The gate.\n![](public-map.png)\n")
            text, meta = build_prompt.assemble_prompt(self.manifest, "clanfire", campaign_dir=path)
            again, _ = build_prompt.assemble_prompt(self.manifest, "clanfire", campaign_dir=path)
            self.assertEqual(text, again)
            self.assertEqual(meta["profile"], "compact")
            self.assertIn("The wolf is a spirit.", text)
            self.assertIn("![](public-map.png)", text)
            self.assertNotIn("# Sinew & Steel Adventurer's Manual", text)
            prompt = path / "prompt.md"
            prompt.write_text(text)
            self.assertEqual(build_prompt.check_prompt(prompt), [])
            self.assertEqual(validate_campaign.validate_campaign(str(path), self.manifest).errors, [])
            tracker = path / "state/trackers/session.yaml"
            original = tracker.read_text()
            tracker.write_text(original + "\n# State changed\n")
            self.assertTrue(any("stale prompt source" in error for error in build_prompt.check_prompt(prompt)))
            self.assertTrue(any("stale prompt source" in error for error in validate_campaign.validate_campaign(str(path), self.manifest).errors))
            tracker.write_text(original)
            (path / "state/memory/session_002.yaml").write_text("schema_version: 1\nsummary: [Next scene]\n")
            self.assertIn("stale prompt: campaign source files changed", build_prompt.check_prompt(prompt))
            (path / "state/memory/session_002.yaml").unlink()
            prompt.write_text(text + "Edited\n")
            self.assertIn("prompt body changed after assembly", build_prompt.check_prompt(prompt))

    def test_full_prompt_and_on_demand_sections_preserve_source_rules(self):
        compact, _ = build_prompt.assemble_prompt(self.manifest, "clanfire")
        full, _ = build_prompt.assemble_prompt(self.manifest, "clanfire", profile="full")
        self.assertLess(len(compact), len(full))
        self.assertIn("# Sinew & Steel Adventurer's Manual", full)
        section, _ = build_prompt.assemble_prompt(self.manifest, None, sections=["manual:6", "almanac:4"])
        self.assertIn("## 6. Combat", section)
        self.assertIn("### 4. Pressure and clocks", section)
        self.assertNotIn("## 7. Carry limit", section)
        with self.assertRaises(ValueError):
            build_prompt.assemble_prompt(self.manifest, None, sections=["manual:999"])

    def test_resources_enforce_limits_without_mutating_inputs_or_refilling_pools(self):
        skin = self.manifest["skins"]["twilight_of_the_northlands"]
        resources = _resources.new_resources(skin, ["ada", "eli"])
        original = deepcopy(resources)
        used, event = _resources.use_resource(resources, skin, "companionship", "ada", purpose="nudge")
        self.assertEqual(resources, original)
        self.assertEqual(event["pressure_gain"], 0)
        with self.assertRaises(ValueError):
            _resources.use_resource(used, skin, "companionship", "ada", purpose="nudge")
        with self.assertRaises(ValueError):
            _resources.use_resource(used, skin, "companionship", "eli", purpose="knack")
        exhausted, event = _resources.use_resource(used, skin, "companionship", "eli", purpose="nudge")
        self.assertEqual(event["pressure_gain"], 1)
        reset = _resources.reset_resources(exhausted, "scene")
        self.assertEqual(reset["party"]["companionship"]["current"], 0)
        self.assertEqual(reset["characters"]["ada"]["companionship_nudge"]["used"], 0)
        session_used, _ = _resources.use_resource(reset, skin, "stout_heart", "ada")
        scene = _resources.reset_resources(session_used, "scene")
        self.assertEqual(scene["characters"]["ada"]["stout_heart"]["used"], 1)
        self.assertEqual(_resources.reset_resources(scene, "session")["characters"]["ada"]["stout_heart"]["used"], 0)
        restored, _ = _resources.recover_resource(scene, skin, "companionship", amount=5)
        self.assertEqual(restored["party"]["companionship"]["current"], 2)
        self.assertEqual(_resources.validate_resources(restored, skin, ["ada", "eli"]), [])

    def test_validator_rejects_invalid_resource_and_pressure_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            path, _ = self.scaffold(temp, "whispers_in_the_fog")
            tracker_path = path / "state/trackers/session.yaml"
            tracker = yaml.safe_load(tracker_path.read_text())
            tracker["pressure"]["scope"] = "party"
            tracker["resources"]["characters"]["ada"]["detective_intuition"]["used"] = 2
            tracker_path.write_text(yaml.safe_dump(tracker))
            errors = validate_campaign.validate_campaign(str(path), self.manifest).errors
            self.assertTrue(any("scope" in error for error in errors))
            self.assertTrue(any(".used" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
