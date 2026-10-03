#!/usr/bin/env python3
"""Read structured playtest logs and report descriptive reopen-trigger evidence.

This command never writes campaign state. It counts observed character-session
histories, not independent population samples, and keeps incomplete sessions
out of the completed evidence. A session's midpoint is the end of its first act;
without an act break there is no midpoint, and without beats no beat rate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import _runtime


ROOT = Path(__file__).resolve().parents[1]


def _integer(value, label: str, minimum: int = 0, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{label} must be an integer in {minimum}..{maximum if maximum is not None else 'unbounded'}")
    return value


def _pc(actor) -> bool:
    return isinstance(actor, str) and bool(actor) and not actor.startswith("npc:")


def _shares(values) -> dict:
    counts = Counter(values)
    total = sum(counts.values())
    return {key: {"count": count, "share": count / total} for key, count in sorted(counts.items())}


def _validate_events(events: list[dict], source: str) -> list[str]:
    if not events:
        raise ValueError(f"{source}: no telemetry events")
    issues = []
    previous = 0
    for index, event in enumerate(events, 1):
        where = f"{source}: event {index}"
        if not isinstance(event, dict) or event.get("schema_version") != 1:
            raise ValueError(f"{where}: expected telemetry schema_version 1")
        sequence = _integer(event.get("sequence"), f"{where} sequence", 1)
        if sequence <= previous:
            raise ValueError(f"{where}: repeated or out-of-order sequence would double-count events")
        if sequence != previous + 1:
            issues.append(f"missing event sequence before {sequence}")
        previous = sequence
        for field, minimum in (("session", 1), ("beat", 0), ("party_size", 0)):
            _integer(event.get(field), f"{where} {field}", minimum)
        if not isinstance(event.get("type"), str) or not isinstance(event.get("skin"), str):
            raise ValueError(f"{where}: event type and skin must be strings")
        if event["type"] in {"roll", "luck"} and (not isinstance(event.get("actor"), str) or not event["actor"]):
            raise ValueError(f"{where}: {event['type']} event must identify its actor")
        if event["type"] == "beat" and type(event.get("perilous")) is not bool:
            raise ValueError(f"{where}: beat must record whether it was perilous")
    for field in ("session", "skin", "party_size"):
        if len({event[field] for event in events}) != 1:
            raise ValueError(f"{source}: {field} changes within one session log; split the history before stratifying")
    starts = [event for event in events if event["type"] == "session_start"]
    ends = [event for event in events if event["type"] == "session_end"]
    if len(starts) > 1 or len(ends) > 1:
        raise ValueError(f"{source}: repeated session boundary")
    if not starts:
        issues.append("missing session_start")
    elif events[0]["type"] != "session_start":
        issues.append("session_start is not the first event")
    if starts:
        complete = starts[0].get("history_complete", True)
        if type(complete) is not bool:
            raise ValueError(f"{source}: history_complete must be a boolean")
        if not complete:
            issues.append("session began before structured telemetry")
    if not ends:
        issues.append("missing session_end")
    elif events[-1]["type"] != "session_end":
        raise ValueError(f"{source}: events occur after session_end")
    return issues


def _red_line(events: list[dict], initial: dict, threshold: int) -> dict:
    scope = initial.get("scope")
    if scope not in {"party", "character"}:
        keys = {event.get("track") for event in events if event["type"] == "pressure"}
        scope = "party" if keys == {"party"} else ("character" if keys and "party" not in keys else None)
    windows, active = [], {}

    def open_window(track, event, reason, left_censored=False):
        window = {
            "track": track, "actor": None if track == "party" else track,
            "start_sequence": event["sequence"], "start_beat": event["beat"],
            "start_reason": reason, "left_censored": left_censored,
            "end_sequence": None, "end_beat": None, "end_reason": None,
            "affected_pc_rolls": 0, "scenes": 1, "rolls_by_actor": {}, "right_censored": True,
        }
        windows.append(window)
        active[track] = window
        return window

    start = next((event for event in events if event["type"] == "session_start"), None)
    tracks = initial.get("tracks", {})
    if not isinstance(tracks, dict) or any(not isinstance(state, dict) for state in tracks.values()):
        raise ValueError("initial Pressure tracks must be a mapping of track states")
    for track, state in tracks.items():
        level = _integer(state.get("current"), f"initial Pressure {track}", 0, 5)
        if level >= 4 and start:
            open_window(track, start, "session_start", left_censored=True)

    high_rolls = missing_snapshots = unassigned = 0
    # A window touches the scene it opens in and each later scene it stays open
    # through. A beat ends a scene; the next scene counts once anything happens in
    # it, or once it too ends, so a session ending on a beat adds no empty scene.
    crossed = set()
    for event in events:
        if event["type"] == "beat":
            for track, window in active.items():
                if track in crossed:
                    window["scenes"] += 1
                crossed.add(track)
            continue
        if event["type"] == "session_end":
            continue
        for track in crossed & set(active):
            active[track]["scenes"] += 1
        crossed.clear()
        if event["type"] == "pressure":
            track = event.get("track")
            if not isinstance(track, str) or not track:
                raise ValueError("Pressure event has no track")
            before = _integer(event.get("before"), "Pressure before", 0, 5)
            after = _integer(event.get("after"), "Pressure after", 0, 5)
            if track not in active and before >= 4:
                open_window(track, event, "observed_in_progress", left_censored=True)
            if track not in active and after >= 4:
                open_window(track, event, "threshold_crossing")
            if track in active and after < 4:
                crossed.discard(track)
                window = active.pop(track)
                window.update(end_sequence=event["sequence"], end_beat=event["beat"],
                              end_reason=event.get("category"), right_censored=False)
        elif event["type"] == "roll" and _pc(event.get("actor")):
            snapshot = event.get("pressure_at_start")
            if snapshot is None:
                missing_snapshots += 1
                continue
            _integer(snapshot, "roll pressure_at_start", 0, 5)
            if snapshot < 4:
                continue  # An upfront cost may already have opened a window.
            high_rolls += 1
            actor = event["actor"]
            track = "party" if scope == "party" else (actor if scope == "character" else None)
            if track is None:
                unassigned += 1
                continue
            window = active.get(track) or open_window(track, event, "observed_in_progress", left_censored=True)
            window["affected_pc_rolls"] += 1
            window["rolls_by_actor"][actor] = window["rolls_by_actor"].get(actor, 0) + 1
    for window in windows:
        window["exceeds_roll_threshold"] = window["affected_pc_rolls"] > threshold
    return {
        "scope": scope, "roll_threshold": threshold, "affected_pc_rolls": high_rolls,
        "missing_pressure_snapshot_rolls": missing_snapshots,
        "unassigned_high_pressure_rolls": unassigned, "windows": windows,
        "ongoing_censored_windows": sum(window["right_censored"] for window in windows),
        "windows_above_threshold": sum(window["exceeds_roll_threshold"] for window in windows),
    }


def summarize_session(events: list[dict], source: str = "<memory>", red_line_rolls: int = 3) -> dict:
    _integer(red_line_rolls, "red-line roll threshold")
    issues = _validate_events(events, source)
    start = next((event for event in events if event["type"] == "session_start"), {})
    initial_luck = start.get("initial_luck", {})
    initial_pressure = start.get("initial_pressure", {})
    if not isinstance(initial_luck, dict) or not isinstance(initial_pressure, dict):
        raise ValueError(f"{source}: initial Luck and Pressure must be mappings")
    beats = [event for event in events if event["type"] == "beat"]
    beat_numbers = [event["beat"] for event in beats]
    if any(right <= left for left, right in zip(beat_numbers, beat_numbers[1:])):
        raise ValueError(f"{source}: repeated or out-of-order beat records")
    last_beat = max(beat_numbers) if beats else None
    # A session's midpoint is the end of its first act. A beat is recorded when its
    # scene ends, so the first half runs to and includes the first beat record that
    # ends an act (by sequence). Without an act break there is no midpoint.
    first_act_end = next((event for event in beats if event.get("act_end")), None)
    midpoint = first_act_end["beat"] if first_act_end else None
    cut = first_act_end["sequence"] if first_act_end else None
    rolls = [event for event in events if event["type"] == "roll" and _pc(event.get("actor"))]
    actors = set(initial_luck)
    actors.update(event["actor"] for event in events if event["type"] in {"roll", "luck"} and _pc(event.get("actor")))
    for event in beats:
        actors.update(actor for actor in event.get("luck", {}) if _pc(actor))
    actors = sorted(actor for actor in actors if _pc(actor))
    characters = {}
    for actor in actors:
        initial = initial_luck.get(actor)
        if initial is not None:
            _integer(initial, f"{source}: initial Luck for {actor}")
        observations = []
        if initial is not None and cut is not None:
            observations.append(initial)
        spent = recovered = 0
        spent_by_source, recovered_by_source = Counter(), Counter()
        for event in events:
            values = []
            if event["type"] == "luck" and event.get("actor") == actor:
                before = _integer(event.get("before"), f"{source}: Luck before for {actor}")
                after = _integer(event.get("after"), f"{source}: Luck after for {actor}")
                values = [before, after]
                loss, gain = max(0, before - after), max(0, after - before)
                spent += loss
                recovered += gain
                if loss:
                    spent_by_source[event.get("source", "<unrecorded>")] += loss
                if gain:
                    recovered_by_source[event.get("source", "<unrecorded>")] += gain
            elif event["type"] == "roll" and event.get("actor") == actor and event.get("luck_current") is not None:
                values = [_integer(event["luck_current"], f"{source}: roll Luck for {actor}")]
            elif event["type"] == "beat" and actor in event.get("luck", {}):
                values = [_integer(event["luck"][actor], f"{source}: beat Luck for {actor}")]
            if cut is not None and event["sequence"] <= cut:
                observations.extend(values)
        minimum = min(observations) if observations else None
        actor_rolls = [event for event in rolls if event["actor"] == actor]
        # Methods belong to the acting die; defence and Deflection dice only resist one.
        acting = [event for event in actor_rolls if event.get("role", "attacker") == "attacker"]
        characters[actor] = {
            "initial_luck": initial, "initially_low": initial <= 1 if initial is not None else None,
            "minimum_luck_first_half": minimum,
            "reached_one_or_less_by_midpoint": minimum <= 1 if minimum is not None else None,
            "newly_reached_one_or_less_by_midpoint": initial > 1 and minimum <= 1 if initial is not None and minimum is not None else None,
            "luck_spent": spent, "luck_recovered": recovered,
            "luck_spent_by_source": dict(sorted(spent_by_source.items())),
            "luck_recovered_by_source": dict(sorted(recovered_by_source.items())),
            "pc_rolls": len(actor_rolls),
            "acting_rolls": len(acting),
            "roll_share_by_role": _shares(event.get("role", "attacker") for event in actor_rolls),
            "roll_share_by_attribute": _shares(event.get("attribute") or "<unrecorded>" for event in actor_rolls),
            "roll_share_by_method": _shares(event.get("method") or "<unrecorded>" for event in acting),
        }
    crises = [event for event in events if event["type"] == "crisis"]
    # Realised gains, not requested ones: a gain at the cap adds nothing.
    gains = [event for event in events if event["type"] == "pressure" and event["after"] > event["before"]]
    gains_by_category, gains_by_source = Counter(), Counter()
    for event in gains:
        gains_by_category[event.get("category", "<unrecorded>")] += event["after"] - event["before"]
        gains_by_source[event.get("source", "<unrecorded>")] += event["after"] - event["before"]
    acting_rolls = [event for event in rolls if event.get("role", "attacker") == "attacker"]
    acts, act = [], {"act": 1, "beats": 0, "perilous_beats": 0, "pc_rolls": 0,
                     "pressure_gained": 0, "crises": 0, "ended": False}
    for event in events:
        if event["type"] == "roll" and _pc(event.get("actor")):
            act["pc_rolls"] += 1
        elif event["type"] == "pressure" and event["after"] > event["before"]:
            act["pressure_gained"] += event["after"] - event["before"]
        elif event["type"] == "crisis":
            act["crises"] += 1
        elif event["type"] == "beat":
            act["beats"] += 1
            act["perilous_beats"] += bool(event.get("perilous"))
            if event.get("act_end"):
                act["ended"] = True
                acts.append(act)
                act = {**act, "act": act["act"] + 1, "beats": 0, "perilous_beats": 0, "pc_rolls": 0,
                       "pressure_gained": 0, "crises": 0, "ended": False}
    if act["beats"] or act["pc_rolls"] or act["pressure_gained"] or act["crises"]:
        acts.append(act)  # the act still open when the log stops
    return {
        "source": source, "session": events[0]["session"], "skin": events[0]["skin"],
        "party_size": events[0]["party_size"], "completed": not issues,
        "incomplete_reasons": issues, "event_count": len(events),
        "recorded_beats": len(beats), "perilous_beats": sum(event["perilous"] for event in beats),
        "last_recorded_beat": last_beat, "midpoint_beat": midpoint,
        "acts": acts, "completed_acts": sum(item["ended"] for item in acts),
        "crises": len(crises), "crisis_targets": dict(sorted(Counter(event.get("target", "<unrecorded>") for event in crises).items())),
        "threshold_crises": sum(bool(event.get("at_threshold", True)) for event in crises),
        "forced_crises": sum(bool(event.get("forced")) for event in crises),
        "pressure_gained": sum(gains_by_category.values()),
        "pressure_gains_by_category": dict(sorted(gains_by_category.items())),
        "pressure_gains_by_source": dict(sorted(gains_by_source.items())),
        "crises_per_20_recorded_beats": 20 * len(crises) / len(beats) if beats else None,
        "characters": characters, "pc_rolls": len(rolls),
        "npc_rolls_excluded": sum(event["type"] == "roll" and str(event.get("actor", "")).startswith("npc:") for event in events),
        "roll_share_by_attribute": _shares(event.get("attribute") or "<unrecorded>" for event in rolls),
        "roll_share_by_method": _shares(event.get("method") or "<unrecorded>" for event in acting_rolls),
        "red_line": _red_line(events, initial_pressure, red_line_rolls),
    }


def _strata(sessions: list[dict]) -> list[dict]:
    groups = {}
    for session in sessions:
        groups.setdefault((session["skin"], session["party_size"]), []).append(session)
    rows = []
    for (skin, party_size), members in sorted(groups.items()):
        with_beats = [session for session in members if session["recorded_beats"]]
        beats = sum(session["recorded_beats"] for session in with_beats)
        rate_crises = sum(session["crises"] for session in with_beats)
        characters = [character for session in members for character in session["characters"].values()]
        eligible = [character for character in characters if character["minimum_luck_first_half"] is not None]
        above_one = [character for character in eligible if character["initially_low"] is False]
        rows.append({
            "skin": skin, "party_size": party_size, "sessions": len(members),
            "recorded_beats": beats, "perilous_beats": sum(session["perilous_beats"] for session in members),
            "crises": sum(session["crises"] for session in members),
            "rate_eligible_sessions": len(with_beats), "sessions_without_beats": len(members) - len(with_beats),
            "rate_eligible_crises": rate_crises,
            "crises_per_20_recorded_beats": 20 * rate_crises / beats if beats else None,
            "character_sessions": len(characters), "midpoint_available_character_sessions": len(eligible),
            "initially_low_character_sessions": sum(character["initially_low"] is True for character in characters),
            "initially_above_one_with_midpoint": len(above_one),
            "newly_low_by_midpoint": sum(character["newly_reached_one_or_less_by_midpoint"] is True for character in above_one),
            "pc_rolls": sum(session["pc_rolls"] for session in members),
            "red_line_windows": sum(len(session["red_line"]["windows"]) for session in members),
            "red_line_windows_above_threshold": sum(session["red_line"]["windows_above_threshold"] for session in members),
            "ongoing_censored_windows": sum(session["red_line"]["ongoing_censored_windows"] for session in members),
        })
    return rows


def summarize_files(paths, red_line_rolls: int = 3) -> dict:
    _integer(red_line_rolls, "red-line roll threshold")
    paths = list(dict.fromkeys(Path(path).expanduser().resolve() for path in paths))
    if not paths:
        raise ValueError("no session JSONL files found")
    summaries = []
    for path in paths:
        events = []
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{number}: invalid JSON: {exc.msg}") from exc
        summaries.append(summarize_session(events, str(path), red_line_rolls))
    completed = [session for session in summaries if session["completed"]]
    incomplete = [session for session in summaries if not session["completed"]]
    return {
        "schema_version": 1,
        "interpretation": "Descriptive logged observations; no population claim or automatic rules decision.",
        "definitions": {
            "midpoint": "The end of the session's first act: the first beat recorded with --act-end. Beats are recorded as their scenes end, so the first half runs to and includes that beat record, by event sequence. Unavailable without an act break.",
            "beat_denominator": "Count explicit beat events, not rolls or the largest beat number; omit sessions without beats from both rate numerator and denominator.",
            "completed": "Explicit session_start and session_end with an uninterrupted event sequence and no partial legacy history; incomplete sessions are separate.",
            "pc_rolls": "Each finalized PC roll, including opposed sides and Deflection; exclude raw_roll records and npc: actors.",
            "luck_spending": "Use before/after changes in luck events only; roll.luck_spent is not an additional expenditure.",
            "red_line": "Pressure >=4 until a pressure event lowers or resets it; affected rolls require pressure_at_start >=4. Each window reports its affected rolls and the scenes it touched: the scene it opened in and each later scene it stayed open through. Open windows are right-censored, including at session end.",
            "red_line_threshold": f"Provisional interpretation of 'few': more than {red_line_rolls} affected PC rolls observed in one window.",
        },
        "session_counts": {"total": len(summaries), "completed": len(completed), "incomplete": len(incomplete)},
        "completed_evidence": {"by_skin_and_party_size": _strata(completed)},
        "incomplete_observations": {"by_skin_and_party_size": _strata(incomplete)},
        "sessions": summaries,
    }


def format_summary(report: dict) -> str:
    counts = report["session_counts"]
    lines = [f"Descriptive playtest summary: {counts['completed']} completed, {counts['incomplete']} incomplete session(s).",
             report["interpretation"], report["definitions"]["red_line_threshold"]]
    for session in report["sessions"]:
        status = "completed" if session["completed"] else "INCOMPLETE: " + "; ".join(session["incomplete_reasons"])
        lines.append(f"\n{session['source']} — {session['skin']}, party {session['party_size']}, session {session['session']} ({status})")
        rate = session["crises_per_20_recorded_beats"]
        lines.append(f"  Beats: {session['recorded_beats']} ({session['perilous_beats']} perilous) in {session['completed_acts']} completed act(s); crises: {session['crises']}; per 20 beats: {rate if rate is not None else 'unavailable'}; midpoint: {'after beat ' + str(session['midpoint_beat']) if session['midpoint_beat'] is not None else 'unavailable (no act break)'}.")
        for actor, character in session["characters"].items():
            minimum = character["minimum_luck_first_half"]
            initial = character["initial_luck"]
            if minimum is None:
                low_text = "first-half Luck unavailable"
            elif character["initially_low"]:
                low_text = "initially <=1"
            elif character["newly_reached_one_or_less_by_midpoint"]:
                low_text = "newly <=1 by midpoint"
            elif character["reached_one_or_less_by_midpoint"]:
                low_text = "observed <=1 by midpoint; initial Luck unavailable"
            else:
                low_text = "not observed <=1 by midpoint"
            lines.append(f"  {actor}: initial Luck {initial if initial is not None else 'unavailable'}; first-half minimum {minimum if minimum is not None else 'unavailable'}; {low_text}; spent/recovered {character['luck_spent']}/{character['luck_recovered']}.")
        lines.append(f"  PC rolls: {session['pc_rolls']}; by attribute: " + ", ".join(f"{key} {value['count']} ({value['share']:.1%})" for key, value in session["roll_share_by_attribute"].items()))
        lines.append("  By method: " + ", ".join(f"{key!r} {value['count']} ({value['share']:.1%})" for key, value in session["roll_share_by_method"].items()))
        red = session["red_line"]
        lines.append(f"  Red-line windows: {len(red['windows'])}; above provisional threshold: {red['windows_above_threshold']}; ongoing/censored: {red['ongoing_censored_windows']}; missing roll snapshots: {red['missing_pressure_snapshot_rolls']}.")
    for label, field in (("Completed evidence", "completed_evidence"), ("Incomplete observations", "incomplete_observations")):
        for row in report[field]["by_skin_and_party_size"]:
            rate = row["crises_per_20_recorded_beats"]
            lines.append(f"\n{label} — {row['skin']}, party {row['party_size']}: {row['sessions']} session(s), {row['recorded_beats']} recorded beats ({row['perilous_beats']} perilous), crises/20 beats {rate if rate is not None else 'unavailable'}; {row['sessions_without_beats']} session(s) lack beat denominators.")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--campaign", help="Campaign slug or campaign directory; read state/logs/session_*.jsonl")
    sources.add_argument("--file", action="append", type=Path, help="One session JSONL file (repeatable)")
    parser.add_argument("--red-line-rolls", type=int, default=3, help="Provisional 'few rolls' threshold; flag windows strictly above it (default: 3)")
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable report")
    args = parser.parse_args(argv)
    try:
        paths = args.file
        if args.campaign:
            directory = Path(args.campaign).expanduser()
            if not directory.is_dir():
                directory = ROOT / "campaigns" / args.campaign
            if not (directory / "campaign.yaml").is_file():
                raise ValueError(f"campaign not found: {directory}")
            with _runtime.campaign_snapshot(directory):
                paths = sorted((directory / "state/logs").glob("session_*.jsonl"))
                report = summarize_files(paths, args.red_line_rolls)
        else:
            report = summarize_files(paths, args.red_line_rolls)
        print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else format_summary(report))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
