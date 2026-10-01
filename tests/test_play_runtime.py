"""Adversarial state sequences across the real campaign transaction boundary."""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import _characters
import _dice
import _play
import _pressure
import _resources
import _runtime
import _sslib
import campaign_init
import play
import playtest_summary


def fixture(slug="free_traders_of_the_drift_marches", actors=("mara", "holo")):
    skin = _sslib.load_manifest()["skins"][slug]
    sheets = {actor: _characters.build_sheet(skin_slug=slug, skin=skin, name=actor,
              attributes={key: 10 for key in skin["attributes"]}, stamina=5,
              build_points_budget=6, build_points_used=0) for actor in actors}
    tracker = {"schema_version": 2, "scene": 0, "session": 1, "beat": 0,
               "pressure": _pressure.new_pressure(skin, list(actors)),
               "resources": _resources.new_resources(skin, list(actors)), "clocks": {}}
    return skin, sheets, tracker


class PlayRuntimeTests(unittest.TestCase):
    def test_pressure_snapshot_precedes_all_upfront_costs(self):
        skin, sheets, tracker = fixture()
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=1, source="hazard", category="ambient")
        with patch.object(_dice, "roll_d20", side_effect=[6, 8]):
            action, events = _play.prepare_action(tracker, sheets, skin, kind="opposed",
                actor="mara", attribute="EDU", opponent="holo", defender_attribute="SOC",
                method="argue", stakes="lose the cargo", pressure_cost=2)
        # Both dice use level1. The crossing fires penalties for their NEXT test.
        self.assertEqual([s["modifiers"]["level"] for s in action["sides"].values()], [1, 1])
        self.assertTrue(all(not c["dis"] for c in action["checks"].values()))
        self.assertEqual([sheets[a]["pools"]["luck"]["current"] for a in sheets], [10, 10])
        track = tracker["pressure"]["tracks"]["party"]
        self.assertEqual(track["current"], 3)
        self.assertEqual({a: len(p) for a, p in track["pending"].items()}, {"mara": 1, "holo": 1})
        self.assertEqual(sum(e["amount"] for e in events if e["type"] == "pressure"), 2)

    def test_shared_penalty_consumes_even_with_cancelling_advantage(self):
        skin, sheets, tracker = fixture()
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=3, source="jump", category="failure")
        with patch.object(_dice, "roll_d20", side_effect=[7]) as roller:
            action, _ = _play.prepare_action(tracker, sheets, skin, kind="check", actor="mara", attribute="SOC",
                method="trade", stakes="cargo lost", adv_sources=["preparation"], toll="luck")
        self.assertEqual(roller.call_count, 1)
        self.assertFalse(action["checks"]["attacker"]["adv"] or action["checks"]["attacker"]["dis"])
        self.assertFalse(tracker["pressure"]["tracks"]["party"]["pending"]["mara"])
        self.assertEqual(sheets["mara"]["pools"]["luck"]["current"], 9)

    def test_personal_insanity_never_penalizes_other_investigator(self):
        skin, sheets, tracker = fixture("whispers_in_the_fog")
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=4, source="tome", category="ambient", actor="mara")
        with patch.object(_dice, "roll_d20", return_value=8):
            action, events = _play.prepare_action(tracker, sheets, skin, kind="check", actor="holo", attribute="SCH",
                method="search", stakes="exposure")
        self.assertEqual(action["sides"]["attacker"]["modifiers"]["level"], 0)
        self.assertFalse(action["checks"]["attacker"]["dis"])
        self.assertFalse(events)

    def test_five_stays_pending_until_one_crisis_clears_every_gain(self):
        skin, sheets, tracker = fixture()
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=7, source="jump", category="failure", actor="mara")
        with self.assertRaisesRegex(ValueError, "pending crisis"):
            _play.ensure_ready(tracker)
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=2, source="crisis fallout", category="failure", actor="mara")
        events = _pressure.crisis(tracker["pressure"], skin, list(sheets), target="mara", table_result=[3],
            description="Mutiny sparked", effects=[{"description": "next social test Disadvantage", "duration": "next social test"}])
        track = tracker["pressure"]["tracks"]["party"]
        self.assertEqual((track["current"], track["cycle"], track["fired_steps"], track["pending"]), (0, 1, [], {}))
        self.assertEqual(events[0]["target"], "mara")
        self.assertTrue(tracker["pressure"]["effects"][0]["active"])
        self.assertEqual(len(tracker["pressure"]["crises"]), 1)

    def test_damage_uses_attacker_margin_not_margin_difference(self):
        skin, sheets, tracker = fixture("clanfire")
        sheets["holo"]["pools"]["stamina"]["current"] = 5
        with patch.object(_dice, "roll_d20", side_effect=[4, 8]):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="MGT",
                opponent="holo", defender_attribute="FLT", method="spear", stakes="harm", edge=1, soak=1)
            result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertEqual(result["damage"], 2)  # margin6, not effective margin4
        self.assertEqual(sheets["holo"]["pools"]["stamina"]["current"], 3)

    def test_second_injury_drops_target_and_positions_hold(self):
        skin, sheets, tracker = fixture("twilight_of_the_northlands")
        sheets["holo"].setdefault("conditions", {})["injured"] = True
        _play.start_combat(tracker, sheets, {"a": ["mara"], "b": ["holo"]}, ["a", "b"])
        with self.assertRaisesRegex(ValueError, "Injured"):
            _play.set_positions(tracker, sheets, {"holo": "vanguard"})
        # Natural1 wins; injured NIM defence has two dice, then Deflection20.
        with patch.object(_dice, "roll_d20", side_effect=[1, 10, 10, 20]):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="STR",
                opponent="holo", defender_attribute="NIM", method="spear", stakes="harm", injury=True)
            result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertTrue(result["pending"])
        # Rejecting a nudge of the locked natural20 cannot offer a new die.
        with patch.object(_dice, "roll_d20", side_effect=AssertionError("must not reroll")):
            with self.assertRaisesRegex(ValueError, "natural"):
                _play.finish_action(tracker, sheets, skin, deflection_nudge=-1)
            result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertFalse(result["deflection"]["success"])
        self.assertEqual(sheets["holo"]["pools"]["stamina"]["current"], 0)
        with self.assertRaisesRegex(ValueError, "whole round"):
            _play.set_positions(tracker, sheets, {"mara": "watchful"})
        _play.set_positions(tracker, sheets, {"mara": "watchful"}, next_round=True)
        self.assertEqual(tracker["combat"]["order"], ["a", "b"])

    def test_ended_positions_do_not_apply_and_injured_vanguard_can_defend(self):
        skin, sheets, tracker = fixture("twilight_of_the_northlands")
        _play.start_combat(tracker, sheets, {"a": ["mara"], "b": ["holo"]}, ["a", "b"])
        _play.set_positions(tracker, sheets, {"holo": "vanguard"})
        sheets["holo"].setdefault("conditions", {})["injured"] = True
        with patch.object(_dice, "roll_d20", side_effect=[8, 4, 6]):
            action, _ = _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="STR",
                opponent="holo", defender_attribute="NIM", method="spear", stakes="harm")
        self.assertTrue(action["checks"]["defender"]["dis"])
        _play.finish_action(tracker, sheets, skin)
        tracker["combat"]["active"] = False
        sheets["holo"]["conditions"]["injured"] = False
        with patch.object(_dice, "roll_d20", side_effect=[8, 4]) as roller:
            action, _ = _play.prepare_action(tracker, sheets, skin, kind="attack", actor="holo", attribute="STR",
                opponent="mara", defender_attribute="NIM", method="spear", stakes="harm")
        self.assertEqual(roller.call_count, 2)
        self.assertFalse(action["checks"]["attacker"]["adv"])

    def test_undefended_candlelight_attack_keeps_incoming_advantage(self):
        skin, sheets, tracker = fixture("candlelight_dungeons")
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=3, source="march", category="ambient")
        with patch.object(_dice, "roll_d20", side_effect=[15, 4]) as roller:
            # LOR avoids the attacker's separate STR/DEX one-test penalty.
            action, _ = _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="LOR",
                opponent="holo", method="spell", stakes="harm", undefended=True)
        self.assertEqual(roller.call_count, 2)
        self.assertTrue(action["checks"]["attacker"]["adv"])
        self.assertNotIn("defender", action["checks"])

    def test_initiative_rolls_once_and_rejects_second_start(self):
        skin, sheets, tracker = fixture()
        with patch.object(_play.random, "randint", side_effect=[7, 7, 3, 9]) as roller:
            event = _play.start_combat(tracker, sheets, {"heroes": ["mara"], "foes": ["holo"]})
        self.assertEqual(roller.call_count, 4)
        self.assertEqual(event["order"], ["foes", "heroes"])
        with self.assertRaisesRegex(ValueError, "already active"):
            _play.start_combat(tracker, sheets, {"heroes": ["mara"], "foes": ["holo"]})

    def test_transaction_failure_restores_every_existing_byte(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            state = directory / "state"
            state.mkdir()
            a, b = state / "a", state / "b"
            a.write_text("original a")
            b.write_text("original b")
            real = _runtime.atomic_text
            failed = False
            def fail_once(path, text):
                nonlocal failed
                if path == b and not failed:
                    failed = True
                    raise OSError("injected write failure")
                return real(path, text)
            with patch.object(_runtime, "atomic_text", side_effect=fail_once), self.assertRaises(OSError):
                _runtime.commit_files(state, {a: "new a", b: "new b"})
            self.assertEqual((a.read_text(), b.read_text()), ("original a", "original b"))
            self.assertFalse((state / ".transaction.json").exists())

    def test_cli_deferred_settlement_is_deterministic_retryable_and_logged(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="clanfire",
                slug="campaign", title="Test", names=["Hero"], seed=2)
            files["state/trackers/session.yaml"]["telemetry_partial"] = True
            campaign_init.write_scaffold(directory, files)
            def call(*args, expected=0):
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    status = play.main(["--campaign", str(directory), "--json", *args])
                self.assertEqual(status, expected, error.getvalue())
                return json.loads(output.getvalue()) if status == 0 else error.getvalue()
            before = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
            options = ["--seed", "42", "--event-id", "one-test", "check", "--attribute", "MGT",
                       "--method", "brace", "--stakes", "fall", "--defer"]
            preview = call("--dry-run", *options)
            after = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            first = call(*options)
            self.assertFalse(first["events"][0]["history_complete"])
            self.assertEqual(preview["result"], first["result"])
            self.assertTrue(call(*options)["replayed"])
            self.assertIn("pending action", call("beat", "--label", "unrelated", expected=1))
            settlement = call("--event-id", "settlement", "settle", "--nudge", "-1")
            self.assertEqual(settlement["result"]["checks"]["attacker"]["raw_result"], 4)
            self.assertEqual(settlement["result"]["checks"]["attacker"]["result"], 3)
            self.assertTrue(call("--event-id", "settlement", "settle", "--nudge", "-1")["replayed"])
            self.assertIn("different command", call("--event-id", "settlement", "settle", expected=1))
            events = [json.loads(line) for line in (directory / "state/logs/session_001.jsonl").read_text().splitlines()]
            self.assertEqual(sum(e["type"] == "roll" for e in events), 1)
            self.assertEqual(sum(-e["amount"] for e in events if e["type"] == "luck"), 1)
            call("beat", "--perilous", "--label", "bridge crossed")
            call("session-close", "--label", "done")
            resumed = call("session", "--label", "resume")
            self.assertTrue(resumed["events"][0]["history_complete"])
            self.assertTrue((directory / "state/memory/session_002.yaml").exists())
            self.assertTrue((directory / "state/logs/session_002.md").exists())

    def test_preplay_roster_additions_fill_companionship_without_resetting_played_pool(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            skin, sheets, _ = fixture("twilight_of_the_northlands", ("one", "two", "three"))
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="twilight_of_the_northlands",
                slug="campaign", title="Test")
            campaign_init.write_scaffold(directory, files)
            _runtime.add_character(directory, "one", sheets["one"])
            _runtime.add_character(directory, "two", sheets["two"])
            state = _sslib.load_yaml(directory / "state/trackers/session.yaml")
            self.assertEqual(state["resources"]["party"]["companionship"]["current"], 2)
            self.assertFalse((directory / "state/logs/session_001.jsonl").exists())

            def call(*args):
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    status = play.main(["--campaign", str(directory), *args])
                self.assertEqual(status, 0, error.getvalue())
                return json.loads(output.getvalue())

            call("--character", "one", "resource", "--name", "companionship",
                 "--purpose", "nudge", "--source", "shared resolve")
            before = {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()}
            with self.assertRaisesRegex(ValueError, "close the current session"):
                _runtime.add_character(directory, "three", sheets["three"])
            self.assertEqual(before, {p.relative_to(directory): p.read_bytes() for p in directory.rglob("*") if p.is_file()})
            call("session-close", "--label", "end")
            log = directory / "state/logs/session_001.jsonl"
            closed_log = log.read_bytes()
            _runtime.add_character(directory, "three", sheets["three"])
            self.assertEqual(log.read_bytes(), closed_log)
            state = _sslib.load_yaml(directory / "state/trackers/session.yaml")
            pool = state["resources"]["party"]["companionship"]
            self.assertEqual((pool["current"], pool["max"]), (1, 3))
            self.assertEqual(state["resources"]["characters"]["one"]["companionship_nudge"]["used"], 1)
            first = playtest_summary.summarize_session([json.loads(line) for line in log.read_text().splitlines()])
            self.assertEqual(first["party_size"], 2)
            next_session = call("session", "--label", "new ally")
            start = next_session["events"][0]
            self.assertEqual(start["type"], "session_start")
            self.assertEqual(start["party_size"], 3)
            self.assertEqual(set(start["initial_luck"]), {"one", "two", "three"})


if __name__ == "__main__":
    unittest.main()
