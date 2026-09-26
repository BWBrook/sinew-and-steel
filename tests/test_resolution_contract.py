"""Resolution expectations from the core manual and quickstart, not the atlas.

Manual §§1 and 3 specify kept dice, natural results, margins, defender ties,
and token-paid nudges. Sheet/CLI checks exercise that same contract at its
state boundary, including current Luck and the pre-spend target snapshot.
"""

import argparse
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

import _dice
import _sslib
import beat


def sheet():
    return {
        "skin": "clanfire",
        "attributes": {"MGT": 12, "INS": 10},
        "pools": {"luck": {"current": 3, "max": 10}},
    }


def args(**overrides):
    defaults = dict(
        command="check", stat=None, stat_key="INS", adv=False, dis=False,
        nudge=0, label=None, attacker=None, attacker_key=None,
        defender=None, defender_key=None, as_role="attacker",
        adv_attacker=False, dis_attacker=False, adv_defender=False,
        dis_defender=False, nudge_target="attacker", nudge_spend="as",
    )
    return argparse.Namespace(**(defaults | overrides))


class ResolutionContractTests(unittest.TestCase):
    def roll(self, stat, result, **kwargs):
        with patch.object(_dice, "roll_d20", return_value=result):
            return _dice.resolve_check(stat, **kwargs)

    def test_natural_results_override_zero_luck_and_high_npc_scores(self):
        for stat in (0, 1, 6, 16, 20, 25):
            with self.subTest(stat=stat):
                one = self.roll(stat, 1)
                twenty = self.roll(stat, 20)
                self.assertTrue(one["success"])
                self.assertFalse(twenty["success"])
                self.assertEqual(one["crit"], "nat1")
                self.assertEqual(twenty["crit"], "nat20")
                self.assertEqual(one["margin"], stat - 1)
                self.assertEqual(twenty["margin"], stat - 20)

    def test_zero_and_one_luck_have_only_natural_one_success(self):
        for tokens in (0, 1):
            successful_faces = [r for r in range(1, 21) if self.roll(tokens, r)["success"]]
            self.assertEqual(successful_faces, [1])

    def test_equal_target_succeeds_with_zero_margin(self):
        check = self.roll(12, 12)
        self.assertTrue(check["success"])
        self.assertEqual(check["margin"], 0)
        self.assertFalse(self.roll(12, 13)["success"])

    def test_advantage_and_disadvantage_keep_only_one_face(self):
        for mode, expected in (({"adv": True}, 1), ({"dis": True}, 20)):
            with self.subTest(mode=mode), patch.object(_dice, "roll_d20", side_effect=[20, 1]):
                check = _dice.resolve_check(12, **mode)
                self.assertEqual(check["result"], expected)
                self.assertEqual(check["rolls"], [20, 1])
                self.assertEqual(check["success"], expected == 1)

    def test_opposing_sources_cancel_without_consuming_second_die(self):
        with patch.object(_dice, "roll_d20", side_effect=[13, 1]) as roller:
            check = _dice.resolve_check(12, adv=True, dis=True)
        self.assertEqual(check["rolls"], [13])
        self.assertFalse(check["success"])
        self.assertFalse(check["adv"])
        self.assertFalse(check["dis"])
        roller.assert_called_once()

    def test_opposed_decisions_include_defender_ties_and_double_failure(self):
        cases = [
            (12, 8, 10, 9, "attacker"),  # quickstart example
            (12, 8, 10, 6, "defender"),  # tied successful margins
            (12, 13, 10, 18, "defender"),  # both fail, regardless of margins
            (12, 8, 10, 11, "attacker"),
            (12, 13, 10, 8, "defender"),
            (0, 1, 0, 2, "attacker"),  # natural success at zero Luck
            (25, 20, 10, 19, "defender"),  # natural failure above 19
            (6, 1, 16, 2, "defender"),  # no automatic opposed victory for nat1
        ]
        for a_stat, a_die, d_stat, d_die, winner in cases:
            with self.subTest(case=(a_stat, a_die, d_stat, d_die)):
                with patch.object(_dice, "roll_d20", side_effect=[a_die, d_die]):
                    result = _dice.resolve_opposed(a_stat, d_stat)
                self.assertEqual(result["outcome"]["winner"], winner)

    def test_nudge_preserves_raw_failure_and_records_final_success(self):
        final = _dice.apply_nudge_to_check(self.roll(12, 15), -3)
        self.assertEqual((final["raw_result"], final["raw_margin"], final["raw_success"]), (15, -3, False))
        self.assertEqual((final["result"], final["margin"], final["success"]), (12, 0, True))
        self.assertEqual(final["final_result"], final["result"])
        self.assertEqual(final["final_margin"], final["margin"])
        self.assertEqual(final["final_success"], final["success"])

    def test_nudges_cannot_change_naturals_or_manufacture_them(self):
        for natural in (1, 20):
            check = self.roll(12, natural)
            with self.assertRaisesRegex(ValueError, "natural"):
                _dice.apply_nudge_to_check(check, 1 if natural == 1 else -1)
            self.assertEqual(_dice.apply_nudge_to_check(check, 0)["crit"], check["crit"])
        nudged_one = _dice.apply_nudge_to_check(self.roll(0, 2), -1)
        nudged_twenty = _dice.apply_nudge_to_check(self.roll(25, 19), 1)
        self.assertIsNone(nudged_one["crit"])
        self.assertIsNone(nudged_twenty["crit"])
        self.assertFalse(nudged_one["success"])
        self.assertTrue(nudged_twenty["success"])

    def test_out_of_range_nudge_rejected_instead_of_clipped_and_overcharged(self):
        for raw, nudge in ((2, -2), (19, 2)):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "between 1 and 20"):
                _dice.apply_nudge_to_check(self.roll(12, raw), nudge)

    def test_every_skin_uses_current_luck_not_attribute_maximum(self):
        for slug, skin in _sslib.load_manifest()["skins"].items():
            hero = sheet()
            hero["skin"] = slug
            key = skin["luck_key"]
            hero["attributes"] = {key: 10}
            with self.subTest(skin=slug), patch.object(_dice, "roll_d20", return_value=4):
                check, success = beat.resolve_roll(args(stat_key=key), hero)
            self.assertEqual(check["stat"], 3)
            self.assertFalse(success)

    def test_luck_target_is_snapshot_before_own_nudge_spend(self):
        hero = sheet()
        options = args(nudge=-1)
        with patch.object(_dice, "roll_d20", return_value=4):
            check, success = beat.resolve_roll(options, hero)
        beat.spend_luck(options, hero, check)
        self.assertTrue(success)
        self.assertEqual(check["stat"], 3)
        self.assertEqual(check["result"], 3)
        self.assertEqual(hero["pools"]["luck"]["current"], 2)
        self.assertEqual(check["luck_spent"], 1)

    def test_owner_pays_to_nudge_opponent_on_either_side(self):
        for role, target, delta in (("attacker", "defender", 2), ("defender", "attacker", 2)):
            hero = sheet()
            options = args(command="opposed", attacker=12, defender=12,
                           as_role=role, nudge_target=target, nudge=delta)
            with self.subTest(role=role), patch.object(_dice, "roll_d20", side_effect=[8, 8]):
                result, success = beat.resolve_roll(options, hero)
            beat.spend_luck(options, hero, result)
            self.assertTrue(success)
            self.assertEqual(result["outcome"]["winner"], role)
            self.assertEqual(hero["pools"]["luck"]["current"], 1)
            self.assertEqual(result["luck_spent"], 2)

    def test_insufficient_or_wrong_owner_spend_cannot_debit(self):
        for options, message in (
            (args(nudge=-4), "not enough luck"),
            (args(command="opposed", nudge=-1, nudge_spend="defender"), "owning character"),
        ):
            hero = sheet()
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                beat.spend_luck(options, hero, {})
            self.assertEqual(hero["pools"]["luck"]["current"], 3)

    def test_explicit_manual_accounting_skips_pool_debit(self):
        hero, receipt = sheet(), {}
        beat.spend_luck(args(nudge=-2, nudge_spend="none"), hero, receipt)
        self.assertEqual(hero["pools"]["luck"]["current"], 3)
        self.assertEqual(receipt["nudge_spend"], "none")
        self.assertNotIn("luck_spent", receipt)

    def test_opposed_sheet_keys_belong_to_selected_role(self):
        for options in (
            args(command="opposed", as_role="defender", attacker_key="INS", defender=10),
            args(command="opposed", attacker=10, defender_key="INS"),
        ):
            with self.assertRaisesRegex(ValueError, "owning sheet"):
                beat.resolve_roll(options, sheet())

    def test_roll_cli_cancellation_in_check_and_opposed(self):
        commands = [
            ["check", "--stat", "12", "--adv", "--dis"],
            ["opposed", "--attacker", "12", "--defender", "10", "--adv-attacker",
             "--dis-attacker", "--adv-defender", "--dis-defender"],
        ]
        for command in commands:
            result = subprocess.run([sys.executable, str(ROOT / "tools/roll.py"),
                                     "--seed", "42", *command], check=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            checks = [data] if command[0] == "check" else [data["attacker"], data["defender"]]
            for check in checks:
                self.assertEqual(len(check["rolls"]), 1)
                self.assertFalse(check["adv"] or check["dis"])

    def test_defender_luck_cli_persists_correct_pool_and_recomputed_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            campaign = root / "campaigns" / "contract"
            characters = campaign / "state" / "characters"
            trackers = campaign / "state" / "trackers"
            characters.mkdir(parents=True)
            trackers.mkdir()
            (campaign / "campaign.yaml").write_text("{}\n")
            hero_path = characters / "hero.yaml"
            hero_path.write_text(yaml.safe_dump(sheet()))
            (trackers / "session.yaml").write_text("scene: 0\nclocks: {}\n")
            # Manifest-backed names are still canonical; only runtime state is temporary.
            (root / "manifest.yaml").write_text((ROOT / "manifest.yaml").read_text())
            argv = ["beat.py", "--campaign", "contract", "--character", "hero", "--json",
                    "--nudge", "-1", "--nudge-target", "defender", "opposed", "--as", "defender",
                    "--attacker", "10", "--defender-key", "INS", "--adv-defender", "--dis-defender"]
            output = io.StringIO()
            with patch.object(_sslib, "repo_root", return_value=root), \
                 patch.object(_dice, "roll_d20", side_effect=[10, 4]), \
                 patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
                status = beat.main()
            self.assertEqual(status, 0)
            receipt = json.loads(output.getvalue())
            self.assertEqual(receipt["defender"]["stat"], 3)
            self.assertEqual(receipt["defender"]["result"], 3)
            self.assertEqual(receipt["outcome"]["winner"], "defender")
            self.assertEqual(receipt["luck_spent"], 1)
            self.assertEqual(yaml.safe_load(hero_path.read_text())["pools"]["luck"]["current"], 2)


if __name__ == "__main__":
    unittest.main()
