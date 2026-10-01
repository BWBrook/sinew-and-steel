"""Arithmetic boundary cases for the shared pure rules, independent of RNG."""
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _dice
import _rules


class RulesCoreTests(unittest.TestCase):
    def test_capped_refunds_do_not_purchase_tags(self):
        attrs = {"A": 6, "B": 6, "C": 6, "D": 6, "E": 6}
        self.assertEqual(_rules.creation_price(attrs, 3), 0)
        self.assertEqual(_rules.creation_price(attrs, 3, ["Steady hands"]), 2)
        # Stamina reductions share the same cap as attributes.
        raised = {"A": 16, "B": 8, "C": 8, "D": 8, "E": 10}
        self.assertEqual(_rules.creation_price(raised, 3), 4)
        self.assertEqual(_rules.creation_price(raised | {"E": 6}, 3), 4)

    def test_scores_and_prices_reject_noninteger_data(self):
        for value in (True, 10.5, "10"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _rules.creation_price({"A": value}, 5)
        for value in (0, 21, True):
            with self.subTest(face=value), self.assertRaises(ValueError):
                _rules.resolve_check_from_rolls(12, [value])

    def test_seeded_wrapper_preserves_original_draw_sequence(self):
        random.seed(42)
        ordinary = _dice.resolve_check(12)
        advantage = _dice.resolve_check(12, adv=True)
        cancelled = _dice.resolve_check(12, adv=True, dis=True)
        self.assertEqual(ordinary["rolls"], [4])
        self.assertEqual(advantage["rolls"], [1, 9])
        self.assertEqual(cancelled["rolls"], [8])
        self.assertEqual(advantage["crit"], "nat1")

    def test_nudged_one_is_not_natural_damage_or_locked_die(self):
        original = _rules.resolve_check_from_rolls(12, [3])
        nudged = _rules.apply_nudge_to_check(original, -2)
        self.assertIsNone(nudged["crit"])
        self.assertEqual(_rules.damage_from_check(nudged, edge=1, soak=3), 1)
        # A further adjustment is legal; only the original natural faces lock.
        nudged_again = _rules.apply_nudge_to_check(nudged, 1)
        self.assertEqual(nudged_again["raw_result"], 3)
        self.assertEqual(nudged_again["result"], 2)
        self.assertEqual(nudged_again["nudge"], -1)
        self.assertEqual(original["result"], 3)

    def test_damage_uses_winners_margin_and_natural_soak_exception(self):
        plain = _rules.resolve_check_from_rolls(12, [7])
        self.assertEqual(_rules.damage_from_check(plain, edge=1, soak=2), 1)
        self.assertEqual(_rules.damage_from_check(plain, edge=2, soak=0), 4)
        natural = _rules.resolve_check_from_rolls(12, [1])
        self.assertEqual(_rules.damage_from_check(natural, edge=1, soak=99), 5)
        self.assertEqual(_rules.damage_from_check(_rules.resolve_check_from_rolls(25, [20]), 2, 0), 0)
        zero_luck_natural = _rules.resolve_check_from_rolls(0, [1])
        self.assertEqual(_rules.damage_from_check(zero_luck_natural, 0, 3), 2)

    def test_opposition_uses_final_nudged_margin_but_natural_is_not_auto_win(self):
        attacker = _rules.resolve_check_from_rolls(12, [8])
        defender = _rules.resolve_check_from_rolls(10, [6])
        self.assertEqual(_rules.resolve_opposed_outcome(attacker, defender)["winner"], "defender")
        attacker = _rules.apply_nudge_to_check(attacker, -1)
        self.assertEqual(_rules.resolve_opposed_outcome(attacker, defender)["winner"], "attacker")
        natural = _rules.resolve_check_from_rolls(6, [1])
        strong = _rules.resolve_check_from_rolls(16, [2])
        self.assertEqual(_rules.resolve_opposed_outcome(natural, strong)["winner"], "defender")


if __name__ == "__main__":
    unittest.main()
