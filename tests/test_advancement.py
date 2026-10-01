"""Creation provenance, historical spending, and file-level advancement checks."""
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

import _characters
import _rules
import _sslib
import _pressure
import _resources
import _runtime
import advance
import char_builder
import gen_character
import recalc_sheet
import validate_sheet

MANIFEST = _sslib.load_manifest(ROOT)
SKIN = MANIFEST["skins"]["clanfire"]


def hero(attrs=None, stamina=5, budget=6, tags=None, slug="clanfire", free_tags=None):
    skin = MANIFEST["skins"][slug]
    attrs = attrs or {key: 10 for key in skin["attributes"]}
    tags = tags or []
    return _characters.build_sheet(
        skin_slug=slug, skin=skin, name="Ledger Test", attributes=attrs,
        stamina=stamina, build_points_budget=budget,
        build_points_used=_rules.creation_price(attrs, stamina, tags),
        tags=tags, free_tags=free_tags,
    )


def extreme():
    return hero(dict(zip(SKIN["attributes"], [16, 6, 6, 6, 8])), stamina=9, budget=12)


def run_tool(name, *arguments):
    return subprocess.run([sys.executable, str(ROOT / "tools" / name), *map(str, arguments)],
                          cwd=ROOT, capture_output=True, text=True)


class AdvancementTests(unittest.TestCase):
    def test_refund_cap_cannot_erase_a_below_baseline_purchase(self):
        sheet = extreme()
        original_creation = deepcopy(sheet["creation"])
        sheet["pools"]["luck"]["current"] = 1
        awarded = _characters.award_milestone(sheet, SKIN, "escape", boon="Safe refuge")
        self.assertEqual(awarded["pools"]["luck"]["current"], 8)
        raised = _characters.raise_stat(awarded, SKIN, "FLT")
        self.assertEqual(_rules.creation_price(raised["attributes"], 9), 12)
        self.assertEqual(raised["creation"], original_creation)
        self.assertEqual(raised["attributes"]["FLT"], 7)
        summary = _characters.replay_advancement(raised, SKIN)
        self.assertEqual((summary["advancement_points_spent"], summary["points_available"]), (1, 1))
        self.assertTrue(validate_sheet.validate_sheet(raised, MANIFEST).ok())
        self.assertEqual(sheet["attributes"]["FLT"], 6)
        self.assertEqual(sheet["advancement"]["entries"], [])

    def test_crossing_baseline_prices_each_step_and_rejects_overspend_atomically(self):
        sheet = hero({**{key: 10 for key in SKIN["attributes"]}, "FLT": 9}, budget=0)
        sheet = _characters.award_milestone(sheet, SKIN, "one")
        untouched = deepcopy(sheet)
        with self.assertRaisesRegex(ValueError, "overspends"):
            _characters.raise_stat(sheet, SKIN, "FLT", steps=2)
        self.assertEqual(sheet, untouched)
        sheet = _characters.award_milestone(sheet, SKIN, "two")
        sheet = _characters.raise_stat(sheet, SKIN, "FLT", steps=2)
        self.assertEqual([entry["cost"] for entry in sheet["advancement"]["entries"] if entry["type"] == "raise"], [1, 2])
        self.assertEqual(_characters.replay_advancement(sheet, SKIN)["points_available"], 1)

    def test_score_ceilings_hold_for_attributes_luck_and_stamina(self):
        for key in ("MGT", "INS", "STM"):
            sheet = hero({key: 16 for key in SKIN["attributes"]}, stamina=9, budget=100)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "legal range"):
                _characters.raise_stat(sheet, SKIN, key)

    def test_grim_can_claim_free_grants_but_cannot_buy_tags_with_reductions(self):
        attrs = {key: 6 for key in SKIN["attributes"]}
        invalid = hero(attrs, stamina=3, budget=0, tags=["Steady hands"])
        self.assertFalse(validate_sheet.validate_sheet(invalid, MANIFEST).ok())
        free = hero(budget=0, slug="whispers_in_the_fog", free_tags=[{"name": "Occult scholar", "grant": "knack"}])
        self.assertTrue(validate_sheet.validate_sheet(free, MANIFEST).ok())
        self.assertEqual(free["creation"]["build_points_used"], 0)
        self.assertEqual(free["creation"]["snapshot"]["bought_tags"], [])
        self.assertEqual(free["tags"], ["Occult scholar"])
        with self.assertRaisesRegex(ValueError, "only 0"):
            hero(budget=0, free_tags=[{"name": "Invented grant", "grant": "knack"}])
        with self.assertRaisesRegex(ValueError, "only 1"):
            hero(budget=0, slug="whispers_in_the_fog", free_tags=[{"name": name, "grant": "knack"} for name in ("One", "Two")])
        earned = _characters.award_milestone(hero(budget=0), SKIN, "first")
        earned = _characters.buy_tag(earned, SKIN, "Steady hands")
        self.assertEqual(_characters.replay_advancement(earned, SKIN)["points_available"], 0)

    def test_replay_rejects_edited_current_stats_prices_and_duplicate_awards(self):
        sheet = _characters.award_milestone(extreme(), SKIN, "one")
        sheet = _characters.raise_stat(sheet, SKIN, "FLT")
        cases = []
        altered = deepcopy(sheet)
        altered["attributes"]["FLT"] = 8
        cases.append(altered)
        altered = deepcopy(sheet)
        altered["advancement"]["entries"][-1]["cost"] = 0
        cases.append(altered)
        altered = deepcopy(sheet)
        altered["creation"]["build_points_used"] = 13
        cases.append(altered)
        altered = deepcopy(sheet)
        altered["advancement"]["entries"].append(deepcopy(altered["advancement"]["entries"][0]))
        cases.append(altered)
        altered = deepcopy(sheet)
        altered["tags"].append("Unpaid tag")
        cases.append(altered)
        for altered in cases:
            with self.subTest(altered=altered["advancement"]):
                self.assertFalse(validate_sheet.validate_sheet(altered, MANIFEST).ok())

    def test_mfield_sensitive_is_a_bought_tag_on_five_attribute_sheet(self):
        result = run_tool("char_builder.py", "--skin", "service_duct_blues", "--name", "Sensitive", "--tag", "M-field sensitive", "--json", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        sheet = json.loads(result.stdout)["sheet"]
        self.assertEqual(len(sheet["attributes"]), 5)
        self.assertEqual(sheet["creation"]["build_points_used"], 2)
        self.assertEqual(sheet["creation"]["snapshot"]["bought_tags"], ["M-field sensitive"])

    def test_pressure_cannot_reappear_on_character_pools(self):
        sheet = hero()
        sheet["pools"]["pressure"] = {"current": 0, "max": 5}
        result = validate_sheet.validate_sheet(sheet, MANIFEST)
        self.assertFalse(result.ok())
        self.assertTrue(any("pools.pressure" in error for error in result.errors))

    def test_cli_dry_run_recalc_and_failed_purchase_preserve_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hero.yaml"
            _sslib.save_yaml(path, extreme())
            original = path.read_bytes()
            preview = run_tool("advance.py", "--file", path, "award", "--id", "one", "--json", "--dry-run")
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(path.read_bytes(), original)
            awarded = run_tool("advance.py", "award", "--id", "one", "--file", path, "--json")
            self.assertEqual(awarded.returncode, 0, awarded.stderr)
            bought = run_tool("advance.py", "--file", path, "raise", "--stat", "FLT", "--json")
            self.assertEqual(bought.returncode, 0, bought.stderr)
            before = _sslib.load_yaml(path)
            recalculated = run_tool("recalc_sheet.py", "--file", path, "--json")
            self.assertEqual(recalculated.returncode, 0, recalculated.stderr)
            after = _sslib.load_yaml(path)
            self.assertEqual(after["creation"], before["creation"])
            self.assertEqual(after["advancement"], before["advancement"])
            self.assertEqual(json.loads(recalculated.stdout)["details"]["points_available"], 1)
            before_bytes = path.read_bytes()
            failed = run_tool("advance.py", "--file", path, "tag", "--name", "Too costly", "--json")
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(path.read_bytes(), before_bytes)

    def test_legacy_recalculation_needs_explicit_unadvanced_assertion(self):
        sheet = hero()
        sheet["schema_version"] = 1
        del sheet["creation"]["snapshot"]
        del sheet["advancement"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.yaml"
            _sslib.save_yaml(path, sheet)
            before = path.read_bytes()
            rejected = run_tool("recalc_sheet.py", "--file", path, "--json")
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            adopted = run_tool("recalc_sheet.py", "--file", path, "--adopt-creation", "--json")
            self.assertEqual(adopted.returncode, 0, adopted.stdout)
            self.assertEqual(_sslib.load_yaml(path)["schema_version"], 2)
        sheet["tracks"] = {"pressure": {"current": 0, "max": 5}}
        adopted = _characters.adopt_legacy_creation(sheet, SKIN)
        self.assertNotIn("tracks", adopted)
        self.assertIn("tracks", sheet)
        sheet["tracks"]["pressure"]["current"] = 1
        with self.assertRaisesRegex(ValueError, "history migration"):
            _characters.adopt_legacy_creation(sheet, SKIN)
        del sheet["tracks"]
        sheet["creation"]["build_points_used"] = 2
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            _characters.adopt_legacy_creation(sheet, SKIN)
        sheet["creation"]["build_points_used"] = 0
        sheet["milestones"] = 1
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            _characters.adopt_legacy_creation(sheet, SKIN)

    def test_campaign_award_logs_actual_luck_recovery_and_replays_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / "campaigns" / "ledger"
            _sslib.save_yaml(root / "manifest.yaml", MANIFEST)
            _sslib.save_yaml(campaign / "campaign.yaml", {"schema_version": 2, "skin": "clanfire"})
            sheet = extreme()
            sheet["pools"]["luck"]["current"] = 1
            _sslib.save_yaml(campaign / "state/characters/hero.yaml", sheet)
            tracker = {"schema_version": 2, "session": 1, "scene": 0, "beat": 0,
                       "pressure": _pressure.new_pressure(SKIN, ["hero"])}
            _sslib.save_yaml(campaign / "state/trackers/session.yaml", tracker)
            argv = ["advance.py", "--campaign", "ledger", "--character", "hero", "--json",
                    "--event-id", "milestone-test", "award", "--id", "escape"]

            def call(extra=()):
                output = io.StringIO()
                with patch.object(_sslib, "repo_root", return_value=root), \
                     patch.object(sys, "argv", [*argv, *extra]), contextlib.redirect_stdout(output):
                    status = advance.main()
                self.assertEqual(status, 0, output.getvalue())
                return json.loads(output.getvalue())

            before = {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()}
            preview = call(["--dry-run"])
            self.assertTrue(preview["dry_run"])
            self.assertEqual(before, {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()})
            first = call()
            events = first["events"]
            self.assertEqual(events[0]["type"], "session_start")
            self.assertEqual(events[0]["initial_luck"], {"hero": 1})
            luck = next(event for event in events if event["type"] == "luck")
            self.assertEqual((luck["source"], luck["before"], luck["after"], luck["amount"]), ("milestone:escape", 1, 8, 7))
            self.assertEqual(luck["category"], "recovery")
            log = campaign / "state/logs/session_001.jsonl"
            log_before = log.read_bytes()
            retried = call()
            self.assertTrue(retried["replayed"])
            self.assertEqual(log.read_bytes(), log_before)
            saved = _sslib.load_yaml(campaign / "state/characters/hero.yaml")
            self.assertEqual(len(saved["advancement"]["entries"]), 1)
            self.assertEqual(saved["pools"]["luck"]["current"], 8)

    def test_campaign_builders_register_roster_without_overwriting_played_sheets(self):
        skin = MANIFEST["skins"]["whispers_in_the_fog"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / "campaigns" / "fog"
            (campaign / "state/characters").mkdir(parents=True)
            _sslib.save_yaml(root / "manifest.yaml", MANIFEST)
            _sslib.save_yaml(campaign / "campaign.yaml", {"schema_version": 2, "skin": "whispers_in_the_fog", "build_points_budget": 6})
            _sslib.save_yaml(campaign / "state/trackers/session.yaml", {
                "schema_version": 2, "session": 1, "scene": 0, "beat": 0,
                "pressure": _pressure.new_pressure(skin, []),
                "resources": _resources.new_resources(skin, []),
            })

            def call(module, name, extra=()):
                output, errors = io.StringIO(), io.StringIO()
                argv = [module.__name__ + ".py", "--campaign", "fog", "--name", name, "--json", *extra]
                with patch.object(_sslib, "repo_root", return_value=root), patch.object(module, "ROOT", root), \
                     patch.object(sys, "argv", argv), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    status = module.main()
                return status, output.getvalue(), errors.getvalue()

            before = {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()}
            self.assertEqual(call(char_builder, "Ada", ["--dry-run"])[0], 0)
            self.assertEqual(before, {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()})
            result = call(char_builder, "Ada", ["--free-tag", "knack=Keen eye"])
            self.assertEqual(result[0], 0, result[2])
            result = call(gen_character, "Bea", ["--seed", "7"])
            self.assertEqual(result[0], 0, result[2])
            tracker = _sslib.load_yaml(campaign / "state/trackers/session.yaml")
            self.assertEqual(set(tracker["pressure"]["tracks"]), {"ada", "bea"})
            self.assertEqual(set(tracker["resources"]["characters"]), {"ada", "bea"})
            path = campaign / "state/characters/ada.yaml"
            before = path.read_bytes()
            rejected = call(char_builder, "Ada")
            self.assertNotEqual(rejected[0], 0)
            self.assertIn("already exists", rejected[2])
            self.assertEqual(path.read_bytes(), before)

    def test_generator_baseline_and_free_tag_contract(self):
        skin = MANIFEST["skins"]["whispers_in_the_fog"]
        sheet = gen_character.build_sheet({**skin, "slug": "whispers_in_the_fog", "_gen": {"steps": 0, "build_points_budget": 0}},
                                          "Quiet", "", free_tags=[{"name": "Keen eye", "grant": "knack"}])
        self.assertTrue(validate_sheet.validate_sheet(sheet, MANIFEST).ok())
        self.assertTrue(all(value == 10 for value in sheet["attributes"].values()))
        self.assertEqual(sheet["tags"], ["Keen eye"])
        self.assertNotIn("pressure", sheet["pools"])


def isolated_campaign(root: Path, *, suffix=".yaml"):
    campaign = root / "isolated"
    _sslib.save_yaml(root / "manifest.yaml", MANIFEST)
    _sslib.save_yaml(campaign / "campaign.yaml", {"schema_version": 2, "skin": "clanfire", "build_points_budget": 6})
    sheet_path = campaign / "state/characters" / ("hero" + suffix)
    sheet = hero()
    sheet["pools"]["luck"]["current"] = 1
    _sslib.save_yaml(sheet_path, sheet)
    tracker_path = campaign / "state/trackers/session.yaml"
    _sslib.save_yaml(tracker_path, {
        "schema_version": 2, "session": 1, "scene": 0, "beat": 0,
        "pending_action": None, "session_closed": False,
        "pressure": _pressure.new_pressure(SKIN, ["hero"]),
        "resources": _resources.new_resources(SKIN, ["hero"]),
    })
    return campaign, sheet_path, tracker_path


def file_snapshot(directory: Path):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


class CharacterPathIntegrityTests(unittest.TestCase):
    def test_creation_refuses_existing_standalone_output_including_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.yaml"
            path.write_text("preserve this existing document\n")
            before = path.read_bytes()
            for tool in ("char_builder.py", "gen_character.py"):
                for options in ([], ["--dry-run"]):
                    with self.subTest(tool=tool, options=options):
                        result = run_tool(tool, "--skin", "clanfire", "--name", "New", "--out", path, *options)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("already exists", result.stderr)
                        self.assertEqual(path.read_bytes(), before)

    def test_creation_out_cannot_add_or_replace_campaign_characters_through_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign, sheet_path, _ = isolated_campaign(root)
            alias = root / "linked_characters"
            alias.symlink_to(sheet_path.parent, target_is_directory=True)
            before = file_snapshot(campaign)
            for tool in ("char_builder.py", "gen_character.py"):
                for path in (sheet_path, sheet_path.parent / "new.yaml", alias / "new.yaml"):
                    for preview in ([], ["--dry-run"]):
                        with self.subTest(tool=tool, path=path, preview=preview):
                            result = run_tool(tool, "--skin", "clanfire", "--name", "New", "--out", path, *preview)
                            self.assertNotEqual(result.returncode, 0)
                            self.assertTrue("already exists" in result.stderr or "use --campaign" in result.stderr, result.stderr)
                            self.assertEqual(file_snapshot(campaign), before)

    def test_campaign_file_advance_keeps_pending_and_closed_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign, path, tracker_path = isolated_campaign(root)
            alias = root / "outside_alias.yaml"
            alias.symlink_to(path)
            # Failed writing commands may acquire this existing lock, but must
            # not change any sheet, tracker, receipt or telemetry file.
            (campaign / "state/.runtime.lock").touch()
            base = _sslib.load_yaml(tracker_path)
            for condition in ({"pending_action": {"phase": "test"}}, {"session_closed": True}):
                _sslib.save_yaml(tracker_path, {**base, **condition})
                before = file_snapshot(campaign)
                for target in (path, alias):
                    for preview in ([], ["--dry-run"]):
                        with self.subTest(condition=condition, target=target, preview=preview):
                            result = run_tool("advance.py", "--file", target, "award", "--id", "forbidden", "--json", *preview)
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn("settle the pending action or open the next session", result.stdout)
                            self.assertEqual(file_snapshot(campaign), before)
                    shown = run_tool("advance.py", "--file", target, "show", "--json")
                    self.assertEqual(shown.returncode, 0, shown.stdout)
                    self.assertEqual(file_snapshot(campaign), before)

    def test_campaign_file_advance_logs_luck_and_is_readonly_until_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign, path, _ = isolated_campaign(root, suffix=".yml")
            alias = root / "outside_alias.yaml"
            alias.symlink_to(path)
            before = file_snapshot(campaign)
            args = ["--file", alias, "--event-id", "file-award", "award", "--id", "first", "--json"]
            shown = run_tool("advance.py", "--file", alias, "show", "--json")
            self.assertEqual(shown.returncode, 0, shown.stdout)
            preview = run_tool("advance.py", *args, "--dry-run")
            self.assertEqual(preview.returncode, 0, preview.stdout)
            self.assertEqual(file_snapshot(campaign), before)
            written = run_tool("advance.py", *args)
            self.assertEqual(written.returncode, 0, written.stdout)
            receipt = json.loads(written.stdout)
            self.assertEqual(Path(receipt["result"]["file"]), path.resolve())
            luck = next(event for event in receipt["events"] if event["type"] == "luck")
            self.assertEqual((luck["source"], luck["before"], luck["after"]), ("milestone:first", 1, 10))
            self.assertEqual(_sslib.load_yaml(path)["pools"]["luck"]["current"], 10)
            self.assertTrue(alias.is_symlink())
            self.assertFalse(path.with_suffix(".yaml").exists())
            after = file_snapshot(campaign)
            retry = run_tool("advance.py", *args)
            self.assertEqual(retry.returncode, 0, retry.stdout)
            self.assertTrue(json.loads(retry.stdout)["replayed"])
            self.assertEqual(file_snapshot(campaign), after)

    def test_recalc_file_uses_campaign_lock_and_transaction_even_through_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign, path, _ = isolated_campaign(root)
            sheet = _sslib.load_yaml(path)
            sheet["pools"]["luck"]["max"] = 9
            _sslib.save_yaml(path, sheet)
            alias = root / "outside_alias.yaml"
            alias.symlink_to(path)
            before = file_snapshot(campaign)

            def call(extra=()):
                output = io.StringIO()
                with patch.object(_sslib, "repo_root", return_value=root), \
                     patch.object(sys, "argv", ["recalc_sheet.py", "--file", str(alias), "--json", *extra]), \
                     patch.object(_runtime, "campaign_lock", wraps=_runtime.campaign_lock) as lock, \
                     patch.object(_runtime, "commit_files", wraps=_runtime.commit_files) as commit, \
                     contextlib.redirect_stdout(output):
                    status = recalc_sheet.main()
                self.assertEqual(status, 0, output.getvalue())
                return lock, commit

            lock, commit = call(["--dry-run"])
            lock.assert_called_once_with(campaign.resolve(), dry_run=True)
            commit.assert_not_called()
            self.assertEqual(file_snapshot(campaign), before)
            lock, commit = call()
            lock.assert_called_once_with(campaign.resolve(), dry_run=False)
            self.assertEqual(commit.call_args.args[0], campaign.resolve() / "state")
            self.assertEqual(set(commit.call_args.args[1]), {path.resolve()})
            saved = _sslib.load_yaml(path)
            self.assertEqual(saved["pools"]["luck"], {**sheet["pools"]["luck"], "max": 10})
            self.assertEqual(saved["creation"], sheet["creation"])
            self.assertEqual(saved["advancement"], sheet["advancement"])
            self.assertTrue(alias.is_symlink())
            self.assertFalse((campaign / "state/.transaction.json").exists())

    def test_tagless_legacy_creation_adopts_empty_tags_without_mutating_input(self):
        sheet = hero()
        sheet["schema_version"] = 1
        del sheet["tags"]
        del sheet["creation"]["snapshot"]
        del sheet["advancement"]
        adopted = _characters.adopt_legacy_creation(sheet, SKIN)
        self.assertNotIn("tags", sheet)
        self.assertEqual(adopted["tags"], [])
        self.assertEqual(adopted["creation"]["snapshot"]["bought_tags"], [])
        self.assertTrue(validate_sheet.validate_sheet(adopted, MANIFEST).ok())


if __name__ == "__main__":
    unittest.main()
