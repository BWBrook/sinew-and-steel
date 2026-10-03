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
import advance
import campaign_init
import play
import playtest_summary
import validate_campaign


def fixture(slug="free_traders_of_the_drift_marches", actors=("mara", "holo")):
    skin = _sslib.load_manifest()["skins"][slug]
    sheets = {actor: _characters.build_sheet(skin_slug=slug, skin=skin, name=actor,
              attributes={key: 10 for key in skin["attributes"]}, stamina=5,
              build_points_budget=6, build_points_used=0) for actor in actors}
    tracker = {"schema_version": 2, "scene": 0, "session": 1, "beat": 0,
               "pressure": _pressure.new_pressure(skin, list(actors)),
               "resources": _resources.new_resources(skin, list(actors)), "clocks": {}}
    return skin, sheets, tracker



def campaign_with(folder, slug, names):
    """A scaffolded campaign whose characters have every attribute at 10."""
    directory = Path(folder) / "campaign"
    campaign_init.write_scaffold(directory, campaign_init.build_scaffold(
        _sslib.load_manifest(), skin_slug=slug, slug="campaign", title="Test"))
    _, sheets, _ = fixture(slug, tuple(names))
    for name in names:
        _runtime.add_character(directory, name, sheets[name])
    return directory


def cli(test, directory, *args, expected=0):
    output, error = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
        status = play.main(["--campaign", str(directory), "--json", *args])
    test.assertEqual(status, expected, error.getvalue())
    return json.loads(output.getvalue()) if status == 0 else error.getvalue()


class PlayRuntimeTests(unittest.TestCase):
    def test_edge_above_two_is_legal_and_priced(self):
        # Heroic Act or a boon can lift a brutal weapon to edge +3.
        skin, sheets, tracker = fixture()
        with patch.object(_dice, "roll_d20", side_effect=[3, 15]):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="STR",
                opponent="holo", defender_attribute="DEX", method="heroic cleave",
                stakes="drive him back", edge=3, soak=1)
        result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertEqual(result["damage"], 1 + 3 + 7 // 5 - 1)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="STR",
                opponent="holo", defender_attribute="DEX", method="x", stakes="x", edge=-1)

    def test_defender_pays_no_toll_only_the_acting_character_does(self):
        # Author ruling (2 Oct 2026): tolls fall on tests a character attempts, never on defence.
        skin, sheets, tracker = fixture()
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=3, source="jump", category="failure")
        with self.assertRaisesRegex(ValueError, "--toll luck"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, kind="opposed", actor="mara",
                attribute="EDU", opponent="holo", defender_attribute="SOC", method="argue", stakes="x")
        # Step 2 has fired for both, so each side rolls two dice for its Disadvantage.
        with patch.object(_dice, "roll_d20", side_effect=[6, 7, 8, 9]):
            _, events = _play.prepare_action(tracker, sheets, skin, kind="opposed", actor="mara",
                attribute="EDU", opponent="holo", defender_attribute="SOC", method="argue",
                stakes="lose the cargo", toll="luck")
        self.assertEqual((sheets["mara"]["pools"]["luck"]["current"], sheets["holo"]["pools"]["luck"]["current"]), (9, 10))
        self.assertEqual(tracker["pressure"]["tracks"]["party"]["current"], 3)
        self.assertEqual([e["actor"] for e in events if e.get("category") == "action_cost"], ["mara"])

    def test_deflection_pays_no_toll(self):
        skin, sheets, tracker = fixture("twilight_of_the_northlands", ("ana", "bo"))
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=3, source="barrow", category="ambient")
        with patch.object(_dice, "roll_d20", side_effect=[1, 15, 9]):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="ana", attribute="STR",
                opponent="bo", defender_attribute="NIM", method="spear", stakes="x", toll="luck",
                edge=1, soak=1, injury=True)
            result, events = _play.finish_action(tracker, sheets, skin)
        self.assertEqual(result.get("phase"), "deflection")
        self.assertEqual(sheets["bo"]["pools"]["luck"]["current"], sheets["bo"]["pools"]["luck"]["max"])
        self.assertEqual(tracker["pressure"]["tracks"]["party"]["current"], 3)

    def test_no_nudge_roll_refuses_nudges_on_the_casters_die(self):
        skin, sheets, tracker = fixture()
        with patch.object(_dice, "roll_d20", side_effect=[12]):
            _play.prepare_action(tracker, sheets, skin, kind="check", actor="mara", attribute="EDU",
                method="Wyrd", stakes="history buckles", no_nudge=True)
        with self.assertRaisesRegex(ValueError, "no-nudge"):
            _play.finish_action(deepcopy(tracker), deepcopy(sheets), skin, nudge=-2)
        result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertFalse(result["success"])

    def test_opposed_test_in_combat_uses_the_combatants_action(self):
        skin, sheets, tracker = fixture()
        _play.start_combat(tracker, sheets, {"crew": ["mara"], "rivals": ["holo"]}, order=["crew", "rivals"])
        with self.assertRaisesRegex(ValueError, "earlier side"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, kind="opposed", actor="holo",
                attribute="SOC", opponent="mara", defender_attribute="SOC", method="taunt", stakes="x")
        with patch.object(_dice, "roll_d20", side_effect=[5, 15]):
            _play.prepare_action(tracker, sheets, skin, kind="opposed", actor="mara", attribute="SOC",
                opponent="holo", defender_attribute="SOC", method="intimidate", stakes="he backs off")
        _play.finish_action(tracker, sheets, skin)
        self.assertEqual(tracker["combat"]["acted"], ["mara"])
        with self.assertRaisesRegex(ValueError, "already acted"):
            _play.prepare_action(tracker, sheets, skin, kind="attack", actor="mara", attribute="STR",
                opponent="holo", defender_attribute="DEX", method="punch", stakes="x", edge=0)

    def test_custodian_levers_are_reported_from_their_step(self):
        skin = _sslib.load_manifest()["skins"]["iron_and_ruin"]
        pressure = _pressure.new_pressure(skin, ["yara"])
        _pressure.change(pressure, skin, ["yara"], amount=4, source="wyrd", category="action_cost", actor="yara")
        levers = _pressure.modifiers(pressure, skin, "yara", "WIL", ["risky"])["custodian_levers"]
        self.assertEqual(len(levers), 2)
        self.assertTrue(any("step4" in lever and "backlash" in lever for lever in levers))

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

    def test_new_session_memory_carries_threads_npcs_and_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="clanfire",
                slug="campaign", title="Test", names=["Hero"], seed=2)
            campaign_init.write_scaffold(directory, files)
            memory = directory / "state/memory/session_001.yaml"
            data = yaml.safe_load(memory.read_text())
            data.update(summary=["wolf driven off"], threads=["who watches the birch-line?"],
                        npcs=["Old Ma"], secrets=["the strangers are scouts"])
            memory.write_text(yaml.safe_dump(data, sort_keys=False))
            for args in (["session-close", "--label", "one"], ["session", "--label", "two"]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(play.main(["--campaign", str(directory), *args]), 0)
            carried = yaml.safe_load((directory / "state/memory/session_002.yaml").read_text())
            self.assertEqual(carried["summary"], [])
            self.assertEqual((carried["threads"], carried["npcs"], carried["secrets"]),
                             (["who watches the birch-line?"], ["Old Ma"], ["the strangers are scouts"]))

    def test_names_resolve_case_insensitively_and_resources_by_display_name(self):
        skin = _sslib.load_manifest()["skins"]["clanfire"]
        self.assertEqual(_resources.resolve_id(skin, "Totem Mark"), "totem_mark")
        self.assertEqual(_resources.resolve_id(skin, "totem_mark"), "totem_mark")
        with self.assertRaisesRegex(ValueError, "unknown skin resource"):
            _resources.resolve_id(skin, "Not A Resource")
        sheets = {"grak": {"name": "Grak"}, "tarra": {"name": "Tarra the Ember-Singer"}}
        self.assertEqual(_runtime.actor_key("Grak", sheets), "grak")
        self.assertEqual(_runtime.actor_key("tarra the ember-singer", sheets), "tarra")

    def test_interrupted_transaction_blocks_readers_until_status_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="clanfire",
                slug="campaign", title="Test", names=["Hero"], seed=2)
            campaign_init.write_scaffold(directory, files)
            tracker = directory / "state/trackers/session.yaml"
            original = tracker.read_text()
            # A crash after the journal and one write leaves torn state behind.
            journal = directory / "state/.transaction.json"
            journal.write_text(json.dumps([{"path": str(tracker.resolve()), "before": original}]))
            tracker.write_text("scene: torn\n")
            with self.assertRaisesRegex(ValueError, "interrupted transaction"):
                _runtime.ensure_recovered(directory)
            report = validate_campaign.validate_campaign(str(directory), _sslib.load_manifest())
            self.assertIn("interrupted transaction", report.errors[0])
            error = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
                self.assertEqual(play.main(["--campaign", str(directory), "--dry-run", "status"]), 1)
            self.assertIn("status", error.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(play.main(["--campaign", str(directory), "status"]), 0)
            self.assertEqual(tracker.read_text(), original)
            self.assertFalse(journal.exists())
            _runtime.ensure_recovered(directory)

    def test_session_close_refuses_an_active_combat(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="clanfire",
                slug="campaign", title="Test", names=["Hero"], seed=2)
            campaign_init.write_scaffold(directory, files)
            def call(*args):
                error = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
                    return play.main(["--campaign", str(directory), *args]), error.getvalue()
            hero = next((directory / "state/characters").glob("*.yaml")).stem
            self.assertEqual(call("npc", "--id", "wolf", "--stat", "MGT=10", "--stamina", "3")[0], 0)
            self.assertEqual(call("combat-start", "--side", f"pcs={hero}", "--side", "foes=npc:wolf",
                                  "--order", "pcs,foes")[0], 0)
            status, error = call("session-close", "--label", "mid-fight")
            self.assertEqual(status, 1)
            self.assertIn("combat-end", error)
            self.assertEqual(call("combat-end", "--reason", "wolf fled")[0], 0)
            self.assertEqual(call("session-close", "--label", "done")[0], 0)

    def test_event_ids_are_case_insensitive_and_never_reused_across_sessions(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "campaign"
            files = campaign_init.build_scaffold(_sslib.load_manifest(), skin_slug="clanfire",
                slug="campaign", title="Test", names=["Hero"], seed=2)
            campaign_init.write_scaffold(directory, files)
            def call(*args, expected=0):
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    status = play.main(["--campaign", str(directory), "--json", *args])
                self.assertEqual(status, expected, error.getvalue())
                return json.loads(output.getvalue()) if status == 0 else error.getvalue()
            call("--event-id", "Scene-End", "beat", "--label", "scene end")
            self.assertTrue(call("--event-id", "scene-end", "beat", "--label", "scene end")["replayed"])
            call("session-close", "--label", "one")
            call("session", "--label", "two")
            self.assertIn("already used in session 1",
                          call("--event-id", "scene-end", "beat", "--label", "scene end", expected=1))

    def test_raising_luck_at_a_milestone_leaves_a_full_pool(self):
        skin, sheets, _ = fixture()
        sheet = sheets["mara"]
        sheet["pools"]["luck"]["current"] = 3
        sheet = _characters.award_milestone(sheet, skin, "m1", label="ridge held", boon="ally")
        sheet = _characters.raise_stat(sheet, skin, skin["luck_key"])
        luck = sheet["pools"]["luck"]
        self.assertEqual((luck["current"], luck["max"]), (11, 11))

    def test_absolute_character_paths_must_stay_inside_the_campaign(self):
        with tempfile.TemporaryDirectory() as folder:
            characters = Path(folder) / "state/characters"
            characters.mkdir(parents=True)
            inside, outside = characters / "hero.yaml", Path(folder) / "elsewhere.yaml"
            inside.write_text("name: Hero\n")
            outside.write_text("name: Stranger\n")
            self.assertEqual(_sslib.resolve_character_file(characters, str(inside)), inside)
            with self.assertRaisesRegex(ValueError, "inside"):
                _sslib.resolve_character_file(characters, str(outside))

    def test_a_failed_rite_forces_one_crisis_below_five(self):
        # Candlelight's Arcanum: +2 Fatigue upfront; a failed cast brings a crisis, never two.
        skin, sheets, tracker = fixture("candlelight_dungeons", ("vex", "orla"))
        pressure, actors = tracker["pressure"], list(sheets)
        _pressure.change(pressure, skin, actors, amount=2, source="Arcanum", category="action_cost", actor="vex")
        with self.assertRaisesRegex(ValueError, "needs --forced"):
            _pressure.crisis(deepcopy(pressure), skin, actors, target="vex", table_result=[2], description="x")
        record, reset = _pressure.crisis(pressure, skin, actors, target="vex", table_result=[2],
                                         description="The ward collapses", forced=True)
        self.assertEqual((record["forced"], record["at_threshold"], reset["before"], reset["after"]), (True, False, 2, 0))
        _pressure.change(pressure, skin, actors, amount=3, source="delve", category="ambient")
        _pressure.change(pressure, skin, actors, amount=2, source="Arcanum", category="action_cost", actor="vex")
        record, _ = _pressure.crisis(pressure, skin, actors, target="vex", table_result=[3],
                                     description="One crisis for both causes", forced=True)
        self.assertTrue(record["at_threshold"])
        self.assertEqual((len(pressure["crises"]), pressure["tracks"]["party"]["cycle"]), (2, 2))
        # Whispers' Unspeakable resets only the caster's personal Insanity.
        skin, sheets, tracker = fixture("whispers_in_the_fog", ("ada", "eli"))
        pressure, actors = tracker["pressure"], list(sheets)
        _pressure.change(pressure, skin, actors, amount=1, source="dread", category="ambient", actor="eli")
        _pressure.change(pressure, skin, actors, amount=2, source="Unspeakable", category="action_cost", actor="ada")
        _pressure.crisis(pressure, skin, actors, target="ada", table_result=[1], description="Break",
                         actor="ada", forced=True)
        self.assertEqual((pressure["tracks"]["ada"]["current"], pressure["tracks"]["eli"]["current"]), (0, 1))
        with tempfile.TemporaryDirectory() as folder:
            directory = campaign_with(folder, "candlelight_dungeons", ["vex"])
            cli(self, directory, "--character", "vex", "pressure", "--gain", "2", "--category", "action_cost",
                "--source", "Arcanum")
            receipt = cli(self, directory, "--character", "vex", "pressure", "--crisis", "--forced",
                          "--table-result", "2", "--source", "Failed Arcanum: the ward collapses")
            crisis = next(event for event in receipt["events"] if event["type"] == "crisis")
            self.assertEqual((crisis["target"], crisis["forced"]), ("vex", True))

    def test_a_crisis_test_rolls_while_its_crisis_is_pending_and_pays_no_toll(self):
        # Service Duct Blues result 4: "test SYS or lose a key system until repaired".
        skin, sheets, tracker = fixture("service_duct_blues", ("kit", "sol"))
        _pressure.change(tracker["pressure"], skin, list(sheets), amount=5, source="reactor", category="ambient", actor="kit")
        options = dict(kind="check", actor="kit", attribute="SYS", method="patch the scrubbers", stakes="lose a key system")
        with self.assertRaisesRegex(ValueError, "pending crisis"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, **options)
        with self.assertRaisesRegex(ValueError, "pays no costs"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, **options, crisis_test=True, toll="luck")
        luck = sheets["kit"]["pools"]["luck"]["current"]
        with patch.object(_dice, "roll_d20", side_effect=[4, 6]):
            _play.prepare_action(tracker, sheets, skin, **options, crisis_test=True)
            _, events = _play.finish_action(tracker, sheets, skin)
        self.assertEqual((sheets["kit"]["pools"]["luck"]["current"], tracker["pressure"]["tracks"]["party"]["current"]), (luck, 5))
        self.assertTrue(next(event for event in events if event["type"] == "roll")["crisis_test"])
        _pressure.crisis(tracker["pressure"], skin, list(sheets), target="kit", table_result=[4],
                         description="Nanite alarm: SYS held; no system lost")
        with self.assertRaisesRegex(ValueError, "needs a pending crisis"):
            _play.prepare_action(tracker, sheets, skin, **options, crisis_test=True)

    def test_beast_bond_beads_pay_for_a_nudge_instead_of_luck(self):
        skin, sheets, tracker = fixture("clanfire", ("grak", "tarra"))
        tracker["resources"]["characters"]["grak"]["beast_bond"]["current"] = 3
        sheets["grak"]["pools"]["luck"]["current"] = 0
        with patch.object(_dice, "roll_d20", side_effect=[12]):
            _play.prepare_action(tracker, sheets, skin, kind="check", actor="grak", attribute="MGT",
                method="the wolf drags the elk down", stakes="lose the herd")
        with self.assertRaisesRegex(ValueError, "cannot pay for a nudge"):
            _play.finish_action(deepcopy(tracker), deepcopy(sheets), skin, nudge=-2, fund="totem_mark")
        result, events = _play.finish_action(tracker, sheets, skin, nudge=-2, fund="Beast Bond")
        self.assertTrue(result["success"])
        self.assertEqual((result["checks"]["attacker"]["result"],
                          tracker["resources"]["characters"]["grak"]["beast_bond"]["current"],
                          sheets["grak"]["pools"]["luck"]["current"]), (10, 1, 0))
        roll = next(event for event in events if event["type"] == "roll")
        self.assertEqual(roll["nudges"], [{"payer": "grak", "delta": -2, "funding": "beast_bond"}])

    def test_advancement_logs_every_luck_change_and_reminds_about_beast_beads(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = campaign_with(folder, "clanfire", ["grak", "tarra"])
            def call(*args):
                output = io.StringIO()
                argv = ["advance.py", "--campaign", str(directory), "--character", "grak", "--json", *args]
                with patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
                    self.assertEqual(advance.main(), 0, output.getvalue())
                return json.loads(output.getvalue())
            awarded = call("award", "--id", "hunt", "--boon", "Wolf pup")
            self.assertIn("--name beast_bond --recover --amount 3", " ".join(awarded["result"]["reminders"]))
            raised = call("raise", "--stat", "INS")
            self.assertEqual([(event["source"], event["amount"]) for event in raised["events"] if event["type"] == "luck"],
                             [("advancement:raise", 1)])
            call("award", "--id", "camp", "--boon", "A safe cave")
            other = call("raise", "--stat", "MGT")
            self.assertFalse([event for event in other["events"] if event["type"] == "luck"])

    def test_a_check_declared_as_a_combat_action_uses_the_turn_and_its_guards(self):
        skin, sheets, tracker = fixture()
        _play.start_combat(tracker, sheets, {"crew": ["mara"], "foes": ["holo"]}, ["crew", "foes"])
        options = dict(kind="check", attribute="EDU", method="reroute power", stakes="lose the shields")
        with self.assertRaisesRegex(ValueError, "earlier side"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, actor="holo", **options, combat_action=True)
        with patch.object(_dice, "roll_d20", side_effect=[3, 4]):
            _play.prepare_action(tracker, sheets, skin, actor="mara", **options)
            _play.finish_action(tracker, sheets, skin)
            self.assertEqual(tracker["combat"]["acted"], [])  # a plain check is a free reaction
            _play.prepare_action(tracker, sheets, skin, actor="mara", **options, combat_action=True)
            _play.finish_action(tracker, sheets, skin)
        self.assertEqual(tracker["combat"]["acted"], ["mara"])
        with self.assertRaisesRegex(ValueError, "already acted"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, actor="mara", **options, combat_action=True)
        sheets["holo"]["pools"]["stamina"]["current"] = 0
        with self.assertRaisesRegex(ValueError, "zero Stamina"):
            _play.combat_preflight(tracker, sheets, "holo")
        with tempfile.TemporaryDirectory() as folder:
            directory = campaign_with(folder, "clanfire", ["grak", "tarra"])
            cli(self, directory, "npc", "--id", "wolf", "--stat", "MGT=10", "--stamina", "3")
            cli(self, directory, "combat-start", "--side", "clan=grak,tarra", "--side", "pack=npc:wolf", "--order", "clan,pack")
            self.assertIn("earlier side", cli(self, directory, "pass", "--actor", "npc:wolf", "--reason", "x", expected=1))

    def test_the_caster_of_an_unnudgeable_roll_cannot_buy_down_the_resister(self):
        skin, sheets, tracker = fixture()
        with patch.object(_dice, "roll_d20", side_effect=[8, 9]):
            _play.prepare_action(tracker, sheets, skin, kind="opposed", actor="mara", attribute="EDU",
                opponent="holo", defender_attribute="SOC", method="Wyrd", stakes="a city forgets", no_nudge=True)
        for payer, side in (("mara", "defender"), ("holo", "attacker")):
            with self.assertRaisesRegex(ValueError, "no-nudge"):
                _play.finish_action(deepcopy(tracker), deepcopy(sheets), skin, nudge=2, nudge_target=side, payer=payer)
        result, _ = _play.finish_action(tracker, sheets, skin, nudge=-1, nudge_target="defender", payer="holo")
        self.assertEqual((result["checks"]["defender"]["result"], result["outcome"]["winner"]), (8, "defender"))

    def test_a_success_only_luck_cost_is_set_aside_then_paid_or_released(self):
        # Candlelight's Greater Spell costs 1 Fortune coin only if it succeeds.
        skin, sheets, tracker = fixture("candlelight_dungeons", ("vex", "orla"))
        sheets["vex"]["pools"]["luck"]["current"] = 1
        options = dict(kind="check", actor="vex", attribute="LOR", method="Greater Spell", stakes="the ward fails")
        with self.assertRaisesRegex(ValueError, "set aside"):
            _play.prepare_action(deepcopy(tracker), deepcopy(sheets), skin, **options, success_luck_cost=2)
        with patch.object(_dice, "roll_d20", side_effect=[11]):
            _play.prepare_action(tracker, sheets, skin, **options, success_luck_cost=1)
        with self.assertRaisesRegex(ValueError, "set aside"):
            _play.finish_action(deepcopy(tracker), deepcopy(sheets), skin, nudge=-1)
        result, _ = _play.finish_action(tracker, sheets, skin)
        self.assertFalse(result["success"])
        self.assertEqual(sheets["vex"]["pools"]["luck"]["current"], 1)  # released on failure
        with patch.object(_dice, "roll_d20", side_effect=[7]):
            _play.prepare_action(tracker, sheets, skin, **options, success_luck_cost=1)
        result, events = _play.finish_action(tracker, sheets, skin)
        self.assertTrue(result["success"])
        self.assertEqual(sheets["vex"]["pools"]["luck"]["current"], 0)  # paid once on success
        self.assertIn("Greater Spell (success cost)", [event.get("source") for event in events if event["type"] == "luck"])

    def test_readers_wait_for_a_writer_to_finish(self):
        import fcntl
        import threading
        with tempfile.TemporaryDirectory() as folder:
            directory = campaign_with(folder, "clanfire", ["grak", "tarra"])
            lock = directory / "state/.runtime.lock"
            self.assertTrue(lock.exists())
            entered = threading.Event()
            def reader():
                with _runtime.campaign_snapshot(directory):
                    entered.set()
            with lock.open("a") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                thread = threading.Thread(target=reader)
                thread.start()
                self.assertFalse(entered.wait(0.2))
                fcntl.flock(handle, fcntl.LOCK_UN)
            thread.join(2)
            self.assertTrue(entered.is_set())

    def test_a_character_retires_between_sessions_and_leaves_the_roster(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = campaign_with(folder, "twilight_of_the_northlands", ["ana", "bo", "cy"])
            cli(self, directory, "--character", "ana", "resource", "--name", "companionship",
                "--purpose", "nudge", "--source", "shared resolve")
            self.assertIn("close the current session",
                          cli(self, directory, "--character", "cy", "retire", "--reason", "fell at the ford", expected=1))
            cli(self, directory, "session-close", "--label", "end")
            retired = cli(self, directory, "--character", "cy", "retire", "--reason", "fell at the ford")
            self.assertEqual(retired["roster"], ["ana", "bo"])
            self.assertFalse((directory / "state/characters/cy.yaml").exists())
            kept = _sslib.load_yaml(directory / "state/characters/retired/cy.yaml")
            self.assertEqual(kept["retired"], {"reason": "fell at the ford", "session": 1})
            state = _sslib.load_yaml(directory / "state/trackers/session.yaml")
            pool = state["resources"]["party"]["companionship"]
            self.assertEqual((pool["current"], pool["max"]), (2, 2))
            self.assertNotIn("cy", state["resources"]["characters"])
            start = cli(self, directory, "session", "--label", "after the ford")["events"][0]
            self.assertEqual(start["party_size"], 2)

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
