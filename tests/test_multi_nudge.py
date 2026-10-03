"""Multiple post-roll adjustments cross the same campaign commit boundary."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _characters
import _dice
import _runtime
import _sslib
import campaign_init
import play


class MultiNudgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "campaign"
        manifest = _sslib.load_manifest()
        slug = "twilight_of_the_northlands"
        self.skin = manifest["skins"][slug]
        files = campaign_init.build_scaffold(manifest, skin_slug=slug,
            slug="campaign", title="Multiple nudges", existing_actors=["mara", "holo"])
        for actor in ("mara", "holo"):
            files[f"state/characters/{actor}.yaml"] = _characters.build_sheet(
                skin_slug=slug, skin=self.skin, name=actor,
                attributes={key: 10 for key in self.skin["attributes"]}, stamina=5,
                build_points_budget=6, build_points_used=0)
        campaign_init.write_scaffold(self.directory, files)

    def call(self, *args, expected=0):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = play.main(["--campaign", str(self.directory), "--json", *args])
        self.assertEqual(status, expected, error.getvalue())
        return json.loads(output.getvalue()) if status == 0 else error.getvalue()

    def prepare(self, attacker=9, defender=8):
        with patch.object(_dice, "roll_d20", side_effect=[attacker, defender]) as roller:
            receipt = self.call("opposed", "--actor", "mara", "--attribute", "HOP",
                "--opponent", "holo", "--defender-attribute", "HOP",
                "--method", "hold course", "--stakes", "lose the route", "--defer")
        self.assertEqual(roller.call_count, 2)
        self.assertTrue(receipt["result"]["pending"])
        return receipt["result"]["action"]

    def snapshot(self):
        return {path.relative_to(self.directory): path.read_bytes()
                for path in self.directory.rglob("*") if path.is_file()}

    def balances(self):
        _, _, _, sheets = _runtime.load_campaign(self.directory)
        return {actor: sheet["pools"]["luck"]["current"] for actor, sheet in sheets.items()}

    def spend(self, receipt):
        return {event["actor"]: -event["amount"] for event in receipt["events"]
                if event["type"] == "luck"}

    def roll_spend(self, receipt):
        return {event["actor"]: event["luck_spent"] for event in receipt["events"]
                if event["type"] == "roll"}

    def test_two_pc_payers_can_each_adjust_the_other_die(self):
        self.prepare()
        with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
            receipt = self.call("settle", "--adjust", "mara=defender:2",
                                "--adjust", "holo=attacker:1")
        checks = receipt["result"]["checks"]
        self.assertEqual((checks["attacker"]["result"], checks["defender"]["result"]), (10, 10))
        self.assertEqual((checks["attacker"]["raw_result"], checks["defender"]["raw_result"]), (9, 8))
        self.assertEqual(self.balances(), {"mara": 8, "holo": 9})
        self.assertEqual(self.spend(receipt), {"mara": 2, "holo": 1})
        self.assertEqual(self.roll_spend(receipt), {"mara": 2, "holo": 1})

    def test_one_payer_can_adjust_both_dice_without_lowering_fixed_luck_target(self):
        self.prepare(9, 10)
        receipt = self.call("settle", "--adjust", "mara=attacker:-2",
                            "--adjust", "mara=defender:2")
        checks = receipt["result"]["checks"]
        self.assertEqual((checks["attacker"]["result"], checks["defender"]["result"]), (7, 12))
        self.assertEqual([check["stat"] for check in checks.values()], [10, 10])
        self.assertTrue(checks["attacker"]["success"])
        self.assertEqual(checks["attacker"]["margin"], 3)
        self.assertEqual(self.balances(), {"mara": 6, "holo": 10})
        self.assertEqual(self.spend(receipt), {"mara": 4})
        self.assertEqual(self.roll_spend(receipt), {"mara": 4, "holo": 0})

    def test_opposite_adjustments_cancel_the_delta_but_not_the_spend(self):
        self.prepare()
        receipt = self.call("settle", "--adjust", "mara=attacker:3",
                            "--adjust", "mara=attacker:-3")
        check = receipt["result"]["checks"]["attacker"]
        self.assertEqual((check["raw_result"], check["result"], check["nudge"]), (9, 9, 0))
        self.assertEqual(self.balances(), {"mara": 4, "holo": 10})
        self.assertEqual(self.spend(receipt), {"mara": 6})
        self.assertEqual(self.roll_spend(receipt), {"mara": 6, "holo": 0})
        roll = next(event for event in receipt["events"] if event["type"] == "roll" and event["actor"] == "mara")
        self.assertEqual(roll["nudges"], [
            {"payer": "mara", "delta": 3, "funding": "luck"},
            {"payer": "mara", "delta": -3, "funding": "luck"},
        ])

    def test_companionship_funds_only_the_convenience_nudge(self):
        self.prepare(12, 12)
        receipt = self.call("settle", "--nudge", "-1", "--payer", "mara", "--fund", "companionship",
                            "--adjust", "mara=attacker:-1", "--adjust", "holo=defender:-1")
        checks = receipt["result"]["checks"]
        self.assertEqual((checks["attacker"]["result"], checks["defender"]["result"]), (10, 11))
        self.assertEqual(self.spend(receipt), {"mara": 1, "holo": 1})
        self.assertEqual(self.roll_spend(receipt), {"mara": 1, "holo": 1})
        self.assertEqual(self.balances(), {"mara": 9, "holo": 9})
        _, _, tracker, _ = _runtime.load_campaign(self.directory)
        self.assertEqual(tracker["resources"]["party"]["companionship"]["current"], 1)
        self.assertEqual(tracker["resources"]["characters"]["mara"]["companionship_nudge"]["used"], 1)

    def test_combined_cost_failure_leaves_saved_state_and_log_unchanged(self):
        self.call("--character", "mara", "luck", "--amount", "-5", "--source", "earlier spend")
        self.prepare(10, 10)
        before = self.snapshot()
        with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
            error = self.call("settle", "--adjust", "mara=attacker:-4",
                              "--adjust", "mara=defender:4", expected=1)
            self.assertIn("not enough Luck: need 8, have 5", error)
            self.assertEqual(self.snapshot(), before)
            receipt = self.call("settle", "--adjust", "mara=attacker:-4")
        checks = receipt["result"]["checks"]
        self.assertEqual((checks["attacker"]["raw_result"], checks["defender"]["result"]), (10, 10))
        self.assertEqual(self.balances(), {"mara": 1, "holo": 10})

    def test_locked_natural_cannot_be_bypassed_by_cancelling_adjustments_or_retry(self):
        for natural in (1, 20):
            with self.subTest(natural=natural):
                self.prepare(natural, 8)
                before = self.snapshot()
                with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
                    error = self.call("settle", "--adjust", "mara=attacker:1",
                                      "--adjust", "holo=attacker:-1", expected=1)
                    self.assertIn("cannot nudge a natural", error)
                    self.assertEqual(self.snapshot(), before)
                    receipt = self.call("settle", "--adjust", "holo=defender:-1")
                checks = receipt["result"]["checks"]
                self.assertEqual(checks["attacker"]["result"], natural)
                self.assertEqual(checks["attacker"]["crit"], "nat1" if natural == 1 else "nat20")
                self.assertEqual((checks["defender"]["raw_result"], checks["defender"]["result"]), (8, 7))

    def test_every_adjustment_and_aggregate_die_bounds_validate_before_commit(self):
        self.prepare(8, 8)
        before = self.snapshot()
        invalid = [
            ["mara=attacker:-1", "outsider=defender:-1"],
            ["mara=attacker:-1", "holo=other:-1"],
            ["mara=attacker:-1", "holo=defender"],
            ["mara=attacker:-1", "holo=defender:1.5"],
            ["mara=attacker:-1", "holo=defender:20"],
            ["mara=attacker:-6", "holo=attacker:-6"],
        ]
        with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
            for entries in invalid:
                with self.subTest(entries=entries):
                    arguments = [part for entry in entries for part in ("--adjust", entry)]
                    self.call("settle", *arguments, expected=1)
                    self.assertEqual(self.snapshot(), before)

    def test_deflection_rejects_adjust_and_keeps_its_existing_nudge_path(self):
        with patch.object(_dice, "roll_d20", side_effect=[1, 9, 8]):
            receipt = self.call("attack", "--actor", "mara", "--attribute", "STR",
                "--opponent", "holo", "--defender-attribute", "NIM", "--method", "spear",
                "--stakes", "harm", "--injury")
        self.assertEqual(receipt["result"]["phase"], "deflection")
        before = self.snapshot()
        with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
            error = self.call("settle", "--adjust", "holo=defender:-1", expected=1)
            self.assertIn("settle Deflection with --deflection-nudge", error)
            self.assertEqual(self.snapshot(), before)
            receipt = self.call("settle", "--deflection-nudge", "-1")
        check = receipt["result"]["deflection"]
        self.assertEqual((check["raw_result"], check["result"]), (8, 7))
        self.assertEqual(self.spend(receipt), {"holo": 1})


if __name__ == "__main__":
    unittest.main()
