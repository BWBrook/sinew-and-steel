"""A site's variety floor must not silently override its difficulty knob."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import _delvekit


class DelvekitDifficultyTests(unittest.TestCase):
    def test_soft_tiny_does_not_force_a_rejected_trap_to_fill_variety(self):
        # Reject every ordinary trap roll. The old feature floor called this
        # function again with probability=1, bypassing the Soft setting.
        calls, solo_calls = [], []
        def decline(data, rng, probability, style):
            calls.append(probability)
            return None
        def decline_solo(data, rng, probability, *args, **kwargs):
            solo_calls.append(probability)
            return []
        with patch.object(_delvekit, "_maybe_add_trap_room", side_effect=decline), \
             patch.object(_delvekit, "_maybe_add_solo_monster", side_effect=decline_solo):
            for seed in range(50):
                data = _delvekit.generate_dungeon(seed=seed, size="tiny", difficulty="soft")
                _delvekit.validate_dungeon(data)
                self.assertFalse(any(r["trap_tags"] for r in data["rooms"]))
                self.assertFalse(data["solo_monsters"])
        self.assertTrue(calls)
        self.assertTrue(all(p < 1 for p in calls))
        self.assertTrue(solo_calls)
        self.assertTrue(all(p < 1 for p in solo_calls))


if __name__ == "__main__":
    unittest.main()
