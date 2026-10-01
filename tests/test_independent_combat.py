"""Regression checks for the analytical model's Twilight round contract."""

from pathlib import Path
import random
import sys
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

import independent_combat as combat


class IndependentCombatTests(unittest.TestCase):
    def halvar(self):
        return combat.pc("halvar", 14, 14, 7, 2, 1, 0, stance="vanguard")

    def test_stance_exchange_controls_leave_the_elite_defence_plain(self):
        rows = {row["scenario"]: row for row in combat.exact_rows()}
        # Independent counts over two attack dice and one ordinary defence
        # die (8,000 equally likely outcomes); the Steady row uses 400.
        expected = {
            "vanguard": (5694 / 8000, 20551 / 8000),
            "steady": (202 / 400, 673 / 400),
            "watchful": (2386 / 8000, 6369 / 8000),
        }
        for stance, (hit, damage) in expected.items():
            with self.subTest(stance=stance):
                row = rows[f"halvar_{stance}_vs_elite"]
                self.assertEqual(row["defence_mode"], combat.MODE_PLAIN)
                self.assertAlmostEqual(row["hit_probability"], hit, places=12)
                self.assertAlmostEqual(
                    row["expected_damage_per_action"], damage, places=12
                )

    def test_injury_penalty_is_immediate_but_vanguard_fallback_waits(self):
        hero = combat.Fighter.fresh(self.halvar())
        foe = combat.Fighter.fresh(combat.npc("foe", 14, 6, 0, 1)[0])
        combat.declare_round_stance(hero)
        rng = Mock(spec=random.Random)
        # Natural-1 attack, failed disadvantaged defence, failed Deflection.
        rng.randint.side_effect = [1, 20, 20, 20]
        combat.resolve_attack(rng, foe, hero, False, "natural1", "none", 0)

        self.assertTrue(hero.injured)
        self.assertEqual(hero.stamina, 3)
        self.assertEqual(hero.declared_stance, "vanguard")
        # Injury now cancels the already-declared attack Advantage. It does
        # not replace the stance part-way through the round.
        self.assertEqual(combat.attack_mode(hero), combat.MODE_PLAIN)
        self.assertEqual(combat.defence_mode(hero, False), combat.MODE_DIS)

        combat.declare_round_stance(hero)
        self.assertEqual(hero.declared_stance, "steady")
        self.assertEqual(hero.spec.stance, "vanguard")
        self.assertEqual(combat.attack_mode(hero), combat.MODE_DIS)
        self.assertEqual(combat.defence_mode(hero, False), combat.MODE_DIS)

    def test_simulation_declares_before_either_side_acts_each_round(self):
        scenario = combat.Scenario(
            name="round_commitment",
            pcs=(self.halvar(),),
            npcs=combat.npc("foe", 14, 6, 0, 1),
            initiative="npc_first",
            injury_rule="natural1",
            luck_policy="none",
            max_rounds=2,
        )
        pc_attacks = []
        incoming = []

        def scripted_attack(rng, attacker, defender, *args):
            if attacker.spec.player:
                pc_attacks.append(
                    (attacker.declared_stance, combat.attack_mode(attacker))
                )
            else:
                incoming.append(defender.declared_stance)
                defender.injured = True

        with patch.object(combat, "resolve_attack", side_effect=scripted_attack):
            result = combat.simulate_once(scenario, random.Random(123))

        self.assertEqual(result.rounds, 2)
        self.assertEqual(incoming, ["vanguard", "steady"])
        self.assertEqual(
            pc_attacks,
            [("vanguard", combat.MODE_PLAIN), ("steady", combat.MODE_DIS)],
        )


if __name__ == "__main__":
    unittest.main()
