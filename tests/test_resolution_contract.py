"""Resolution expectations from the core manual and quickstart, not the atlas.

Manual §§1 and 3 specify kept dice, natural results, margins, defender ties,
and token-paid nudges. Sheet/CLI checks exercise that same contract at its
state boundary, including current Luck and the pre-spend target snapshot.
"""

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _dice
import _sslib
import _characters
import _play
import _pressure
import _resources


def state(slug="clanfire"):
    skin = _sslib.load_manifest()["skins"][slug]
    actors = ("hero", "rival")
    sheets = {actor: _characters.build_sheet(skin_slug=slug, skin=skin, name=actor,
        attributes={key: 10 for key in skin["attributes"]}, stamina=5,
        build_points_budget=6, build_points_used=0) for actor in actors}
    for sheet in sheets.values():
        sheet["pools"]["luck"]["current"] = 3
    tracker = {"pressure": _pressure.new_pressure(skin, list(actors)),
               "resources": _resources.new_resources(skin, list(actors))}
    return skin, sheets, tracker


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
        for slug in _sslib.load_manifest()["skins"]:
            skin, sheets, tracker = state(slug)
            with self.subTest(skin=slug), patch.object(_dice, "roll_d20", return_value=4):
                action, _ = _play.prepare_action(tracker, sheets, skin, kind="check", actor="hero",
                    attribute=skin["luck_key"], method="chance", stakes="fall")
            self.assertEqual(action["checks"]["attacker"]["stat"], 3)
            self.assertFalse(action["checks"]["attacker"]["success"])

    def test_luck_target_is_snapshot_before_own_nudge_spend(self):
        skin, sheets, tracker = state()
        with patch.object(_dice, "roll_d20", return_value=4):
            _play.prepare_action(tracker, sheets, skin, kind="check", actor="hero",
                attribute="INS", method="chance", stakes="fall")
        result, events = _play.finish_action(tracker, sheets, skin, nudge=-1)
        self.assertTrue(result["success"])
        self.assertEqual(result["checks"]["attacker"]["stat"], 3)
        self.assertEqual(result["checks"]["attacker"]["result"], 3)
        self.assertEqual(sheets["hero"]["pools"]["luck"]["current"], 2)
        self.assertEqual(sum(e["amount"] for e in events if e["type"] == "luck"), -1)

    def test_either_participant_can_pay_to_nudge_opponent(self):
        for payer, target, winner in (("hero", "defender", "attacker"), ("rival", "attacker", "defender")):
            skin, sheets, tracker = state()
            with patch.object(_dice, "roll_d20", side_effect=[8, 8]):
                _play.prepare_action(tracker, sheets, skin, kind="opposed", actor="hero", attribute="MGT",
                    opponent="rival", defender_attribute="FLT", method="grapple", stakes="held")
            result, _ = _play.finish_action(tracker, sheets, skin, nudge=2, nudge_target=target, payer=payer)
            self.assertEqual(result["outcome"]["winner"], winner)
            self.assertEqual(sheets[payer]["pools"]["luck"]["current"], 1)

    def test_insufficient_luck_or_uninvolved_payer_rejected(self):
        for options in ({"nudge": -4}, {"nudge": -1, "payer": "outsider"}):
            skin, sheets, tracker = state()
            with patch.object(_dice, "roll_d20", return_value=8):
                _play.prepare_action(tracker, sheets, skin, kind="check", actor="hero", attribute="MGT",
                    method="climb", stakes="fall")
            with self.assertRaises(ValueError):
                _play.finish_action(tracker, sheets, skin, **options)
            self.assertEqual(sheets["hero"]["pools"]["luck"]["current"], 3)

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



if __name__ == "__main__":
    unittest.main()
