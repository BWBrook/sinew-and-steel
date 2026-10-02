"""Hand-calculated telemetry timelines, independent of runtime event creation."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import playtest_summary as summary


class Timeline:
    def __init__(self, skin="clanfire", party_size=2):
        self.events = []
        self.skin, self.party_size = skin, party_size

    def add(self, kind, beat=0, **values):
        self.events.append({"schema_version": 1, "sequence": len(self.events) + 1,
                            "session": 1, "beat": beat, "scene": 0,
                            "skin": self.skin, "party_size": self.party_size,
                            "event_id": values.pop("event_id", f"command-{len(self.events)}"),
                            "seed": None, "type": kind, **values})
        return self

    def start(self, luck=None, pressure=None):
        return self.add("session_start", initial_luck=luck if luck is not None else {"a": 5, "b": 1},
                        initial_pressure=pressure if pressure is not None else {"scope": "party", "tracks": {"party": {"current": 3}}})

    def roll(self, actor, beat, attribute, method, pressure, luck, **values):
        return self.add("roll", beat, actor=actor, role=values.pop("role", "attacker"),
                        attribute=attribute, method=method, pressure_at_start=pressure,
                        luck_current=luck, luck_spent=values.pop("luck_spent", 0),
                        target=12, advantage_sources=[], disadvantage_sources=[],
                        check={"rolls": [8], "result": 8, "margin": 4, "success": True}, **values)


def shared_timeline():
    # Beats are recorded as each scene ends (skills/run_session.md), so events
    # carry the number of beats completed so far.
    timeline = Timeline().start()
    timeline.add("pressure", 0, track="party", before=3, after=4, category="action_cost", source="risky toll")
    timeline.roll("a", 0, "MGT", "spear", 3, 5)  # Snapshot precedes the toll.
    timeline.add("raw_roll", 0, action={"checks": {"attacker": {"rolls": [11]}}})
    timeline.add("luck", 0, actor="a", before=5, after=2, source="nudge", category="nudge", event_id="opposed-nudge")
    timeline.roll("a", 0, "MGT", "spear", 4, 2, luck_spent=3, event_id="opposed-nudge")
    timeline.roll("b", 0, "REF", "dodge", 4, 1, role="defender", event_id="opposed-nudge")
    timeline.roll("npc:wolf", 0, "FLT", "bite", None, 0)
    timeline.add("beat", 1, perilous=True, luck={"a": 2, "b": 1})
    timeline.add("luck", 1, actor="a", before=2, after=1, source="ward", category="action_cost")
    timeline.roll("a", 1, "INT", "read sigils", 4, 1)
    timeline.roll("b", 1, "REF", "dodge", 4, 1)
    timeline.add("pressure", 1, track="party", before=4, after=5, category="failure", source="rite")
    timeline.add("crisis", 1, track="party", target="a", table_result=[3])
    timeline.add("pressure", 1, track="party", before=5, after=0, category="crisis_reset", source="crisis:1")
    timeline.add("beat", 2, perilous=False, luck={"a": 1, "b": 1})
    timeline.add("luck", 2, actor="a", before=1, after=3, source="milestone", category="recovery")
    timeline.add("pressure", 2, track="party", before=0, after=4, category="ambient", source="storm")
    timeline.roll("a", 2, "INT", "search", 4, 3)
    timeline.add("beat", 3, perilous=True, luck={"a": 3, "b": 1})
    timeline.add("beat", 4, perilous=True, luck={"a": 3, "b": 1})
    timeline.add("session_end", 4)
    return timeline.events


class PlaytestSummaryTests(unittest.TestCase):
    def test_hand_calculated_shared_timeline(self):
        report = summary.summarize_session(shared_timeline())
        self.assertTrue(report["completed"])
        self.assertEqual((report["recorded_beats"], report["perilous_beats"], report["midpoint_beat"]), (4, 3, 2))
        self.assertEqual(report["crises_per_20_recorded_beats"], 5)
        self.assertEqual(report["crisis_targets"], {"a": 1})
        a, b = report["characters"]["a"], report["characters"]["b"]
        self.assertEqual((a["initial_luck"], a["minimum_luck_first_half"]), (5, 1))
        self.assertTrue(a["newly_reached_one_or_less_by_midpoint"])
        self.assertFalse(a["initially_low"])
        self.assertEqual((b["initial_luck"], b["minimum_luck_first_half"]), (1, 1))
        self.assertTrue(b["initially_low"])
        self.assertTrue(b["reached_one_or_less_by_midpoint"])
        self.assertFalse(b["newly_reached_one_or_less_by_midpoint"])
        self.assertEqual((a["luck_spent"], a["luck_recovered"]), (4, 2))
        self.assertEqual(a["luck_spent_by_source"], {"nudge": 3, "ward": 1})
        self.assertEqual(report["pc_rolls"], 6)
        self.assertEqual(report["npc_rolls_excluded"], 1)
        self.assertEqual(a["roll_share_by_attribute"], {"INT": {"count": 2, "share": .5}, "MGT": {"count": 2, "share": .5}})
        self.assertEqual(a["roll_share_by_method"]["spear"], {"count": 2, "share": .5})
        self.assertEqual(b["pc_rolls"], 2)  # Both opposed sides count, despite a shared event_id.
        self.assertEqual(report["roll_share_by_attribute"]["REF"], {"count": 2, "share": 1 / 3})

        red = report["red_line"]
        self.assertEqual(red["affected_pc_rolls"], 5)
        first, second = red["windows"]
        self.assertEqual((first["affected_pc_rolls"], first["rolls_by_actor"]), (4, {"a": 2, "b": 2}))
        self.assertEqual(first["end_reason"], "crisis_reset")
        self.assertFalse(first["right_censored"])
        self.assertTrue(first["exceeds_roll_threshold"])
        self.assertEqual(second["affected_pc_rolls"], 1)
        self.assertTrue(second["right_censored"])
        self.assertEqual(red["ongoing_censored_windows"], 1)
        self.assertEqual(red["windows_above_threshold"], 1)
        self.assertFalse(summary.summarize_session(shared_timeline(), red_line_rolls=4)["red_line"]["windows"][0]["exceeds_roll_threshold"])

    def test_personal_red_lines_are_actor_specific_and_open_at_session_start(self):
        timeline = Timeline("whispers_in_the_fog").start({"a": 6, "b": 6}, {"scope": "character", "tracks": {"a": {"current": 4}, "b": {"current": 1}}})
        timeline.add("beat", 1, perilous=True)
        timeline.roll("b", 1, "FRT", "resist fear", 1, 6)
        timeline.add("pressure", 1, track="b", before=1, after=4, category="failure")
        timeline.roll("a", 1, "SCH", "read ritual", 4, 6)
        timeline.roll("b", 1, "FRT", "resist fear", 4, 6)
        timeline.add("pressure", 1, track="a", before=4, after=0, category="purge")
        timeline.roll("b", 1, "FRT", "resist fear", 4, 6)
        timeline.add("beat", 2, perilous=False)
        timeline.add("session_end", 2)
        report = summary.summarize_session(timeline.events, red_line_rolls=1)
        a, b = report["red_line"]["windows"]
        self.assertEqual((a["track"], a["actor"], a["affected_pc_rolls"]), ("a", "a", 1))
        self.assertEqual(a["start_reason"], "session_start")
        self.assertTrue(a["left_censored"])
        self.assertFalse(a["right_censored"])
        self.assertEqual((b["track"], b["affected_pc_rolls"]), ("b", 2))
        self.assertTrue(b["right_censored"])
        self.assertTrue(b["exceeds_roll_threshold"])

    def test_no_beats_and_unclosed_sessions_are_explicitly_unavailable(self):
        timeline = Timeline(party_size=1).start({"a": 8})
        timeline.add("luck", actor="a", before=8, after=0, source="nudge", category="nudge")
        timeline.roll("a", 0, "MGT", "climb", 3, 0, luck_spent=8)
        report = summary.summarize_session(timeline.events)
        self.assertFalse(report["completed"])
        self.assertIn("missing session_end", report["incomplete_reasons"])
        self.assertIsNone(report["midpoint_beat"])
        self.assertIsNone(report["crises_per_20_recorded_beats"])
        a = report["characters"]["a"]
        self.assertEqual(a["luck_spent"], 8)
        self.assertIsNone(a["minimum_luck_first_half"])
        self.assertIsNone(a["reached_one_or_less_by_midpoint"])

    def test_migrated_session_stays_incomplete_even_after_an_explicit_end(self):
        events = shared_timeline()
        events[0]["history_complete"] = False
        report = summary.summarize_session(events)
        self.assertFalse(report["completed"])
        self.assertIn("session began before structured telemetry", report["incomplete_reasons"])

    def test_missing_pressure_snapshot_is_not_inferred_from_current_track(self):
        timeline = Timeline(party_size=1).start({"a": 5}, {"scope": "party", "tracks": {"party": {"current": 4}}})
        timeline.roll("a", 0, "Deflection", "deflect injurious blow", None, 5)
        timeline.events[-1].pop("pressure_at_start")
        report = summary.summarize_session(timeline.events)
        self.assertEqual(report["red_line"]["missing_pressure_snapshot_rolls"], 1)
        self.assertEqual(report["red_line"]["affected_pc_rolls"], 0)
        self.assertEqual(report["red_line"]["windows"][0]["affected_pc_rolls"], 0)

    def test_midpoint_uses_last_recorded_beat_number_without_inventing_beats(self):
        timeline = Timeline(party_size=1).start({"a": 5})
        timeline.add("luck", 1, actor="a", before=5, after=2, source="cost")
        timeline.add("beat", 2, perilous=True)
        timeline.add("luck", 2, actor="a", before=2, after=1, source="later cost")
        timeline.add("beat", 5, perilous=False)
        timeline.add("session_end", 5)
        report = summary.summarize_session(timeline.events)
        self.assertEqual((report["recorded_beats"], report["last_recorded_beat"], report["midpoint_beat"]), (2, 5, 2))
        self.assertEqual(report["characters"]["a"]["minimum_luck_first_half"], 2)
        self.assertFalse(report["characters"]["a"]["newly_reached_one_or_less_by_midpoint"])

    def test_luck_initially_low_can_be_distinguished_from_later_recovery(self):
        timeline = Timeline(party_size=1).start({"a": 0})
        timeline.add("luck", 0, actor="a", before=0, after=4, source="rest")
        timeline.add("beat", 1, perilous=False, luck={"a": 4})
        timeline.add("beat", 2, perilous=False, luck={"a": 4})
        timeline.add("session_end", 2)
        a = summary.summarize_session(timeline.events)["characters"]["a"]
        self.assertTrue(a["initially_low"])
        self.assertEqual(a["minimum_luck_first_half"], 0)
        self.assertFalse(a["newly_reached_one_or_less_by_midpoint"])
        self.assertEqual(a["luck_recovered"], 4)

    def test_duplicate_sequences_fail_and_missing_sequences_remain_incomplete(self):
        events = shared_timeline()
        duplicated = deepcopy(events)
        duplicated.insert(4, deepcopy(duplicated[3]))
        with self.assertRaisesRegex(ValueError, "double-count"):
            summary.summarize_session(duplicated)
        events.pop(4)
        report = summary.summarize_session(events)
        self.assertFalse(report["completed"])
        self.assertTrue(any("missing event sequence" in reason for reason in report["incomplete_reasons"]))

    def test_missing_initial_snapshot_does_not_invent_initial_luck(self):
        timeline = Timeline(party_size=1)
        timeline.add("luck", actor="a", before=3, after=1, source="observed cost")
        timeline.add("beat", 1, perilous=False).add("beat", 2, perilous=False).add("session_end", 2)
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_log(Path(temp) / "partial.jsonl", timeline.events)
            report = summary.summarize_files([path])
        session = report["sessions"][0]
        self.assertFalse(session["completed"])
        a = session["characters"]["a"]
        self.assertIsNone(a["initial_luck"])
        self.assertIsNone(a["newly_reached_one_or_less_by_midpoint"])
        self.assertEqual(a["minimum_luck_first_half"], 1)
        self.assertIn("observed <=1 by midpoint; initial Luck unavailable", summary.format_summary(report))

    def write_log(self, path, events):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        return path

    def test_aggregates_separate_mixed_skins_parties_and_incomplete_histories(self):
        solo = Timeline(party_size=1).start({"solo": 7})
        solo.add("beat", 1, perilous=True).add("beat", 2, perilous=False).add("session_end", 2)
        horror = Timeline("whispers_in_the_fog").start({"a": 5, "b": 5})
        horror.add("beat", 1, perilous=True).add("crisis", 1, target="a", table_result=[1]).add("beat", 2, perilous=True).add("session_end", 2)
        unfinished = Timeline().start().add("beat", 1, perilous=True).add("crisis", 1, target="b", table_result=[2])
        no_beats = Timeline().start().add("crisis", target="b", table_result=[4]).add("session_end")
        with tempfile.TemporaryDirectory() as temp:
            paths = [self.write_log(Path(temp) / f"{index}.jsonl", events) for index, events in enumerate((shared_timeline(), solo.events, horror.events, unfinished.events, no_beats.events))]
            report = summary.summarize_files(paths + paths[:1])  # Same file is never counted twice.
        self.assertEqual(report["session_counts"], {"total": 5, "completed": 4, "incomplete": 1})
        rows = {(row["skin"], row["party_size"]): row for row in report["completed_evidence"]["by_skin_and_party_size"]}
        self.assertEqual(set(rows), {("clanfire", 1), ("clanfire", 2), ("whispers_in_the_fog", 2)})
        row = rows[("clanfire", 2)]
        self.assertEqual((row["sessions"], row["crises"], row["rate_eligible_crises"], row["recorded_beats"]), (2, 2, 1, 4))
        self.assertEqual(row["crises_per_20_recorded_beats"], 5)
        self.assertEqual(row["sessions_without_beats"], 1)
        self.assertEqual(row["newly_low_by_midpoint"], 1)
        self.assertEqual(rows[("clanfire", 1)]["crises_per_20_recorded_beats"], 0)
        self.assertEqual(rows[("whispers_in_the_fog", 2)]["crises_per_20_recorded_beats"], 10)
        incomplete = report["incomplete_observations"]["by_skin_and_party_size"][0]
        self.assertEqual((incomplete["sessions"], incomplete["crises"]), (1, 1))

    def test_midpoint_excludes_the_scene_after_the_midpoint_beat(self):
        # Three scenes: only the first is "by mid-session" (floor(3/2) = 1 beat).
        timeline = Timeline(party_size=1).start({"a": 5})
        timeline.add("beat", 1, perilous=True, luck={"a": 5})
        timeline.add("luck", 1, actor="a", before=5, after=1, source="scene two cost")
        timeline.add("beat", 2, perilous=True, luck={"a": 1})
        timeline.add("beat", 3, perilous=False, luck={"a": 1}).add("session_end", 3)
        a = summary.summarize_session(timeline.events)["characters"]["a"]
        self.assertEqual(a["minimum_luck_first_half"], 5)
        self.assertFalse(a["reached_one_or_less_by_midpoint"])

    def test_cli_accepts_campaign_or_repeated_files_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = Path(temp) / "sample"
            log = self.write_log(campaign / "state/logs/session_001.jsonl", shared_timeline())
            (campaign / "campaign.yaml").write_text("skin: clanfire\n", encoding="utf-8")
            before = {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()}
            for arguments in (["--campaign", str(campaign)], ["--file", str(log), "--file", str(log)]):
                result = subprocess.run([sys.executable, str(ROOT / "tools/playtest_summary.py"), *arguments, "--json", "--red-line-rolls", "4"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["session_counts"]["total"], 1)
                self.assertEqual(report["sessions"][0]["red_line"]["windows_above_threshold"], 0)
            after = {str(path): path.read_bytes() for path in campaign.rglob("*") if path.is_file()}
            self.assertEqual(before, after)

    def test_invalid_json_and_schema_fail_with_source_context(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "broken.jsonl"
            path.write_text('{"schema_version":', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "broken.jsonl:1: invalid JSON"):
                summary.summarize_files([path])
        events = shared_timeline()
        events[0]["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "schema_version 1"):
            summary.summarize_session(events)
        events = shared_timeline()
        events[0]["initial_pressure"]["tracks"] = []
        with self.assertRaisesRegex(ValueError, "Pressure tracks must be a mapping"):
            summary.summarize_session(events)


if __name__ == "__main__":
    unittest.main()
