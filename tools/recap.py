#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import yaml

import _sslib

ROOT = Path(__file__).resolve().parents[1]
SESSION_RE = re.compile(r"session_(\d{3})\.ya?ml$")


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def save_yaml(path: Path, data: dict):
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def find_latest_session(memory_dir: Path) -> Path | None:
    latest = None
    latest_num = -1
    for p in memory_dir.glob("session_*.yaml"):
        match = SESSION_RE.search(p.name)
        if not match:
            continue
        num = int(match.group(1))
        if num > latest_num:
            latest_num = num
            latest = p
    return latest


def next_session_path(memory_dir: Path) -> Path:
    latest = find_latest_session(memory_dir)
    if not latest:
        return memory_dir / "session_001.yaml"
    match = SESSION_RE.search(latest.name)
    num = int(match.group(1)) if match else 0
    return memory_dir / f"session_{num + 1:03d}.yaml"


def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.strip() == "":
            return []
        return [value]
    return [value]


def update_tracker(
    tracker_path: Path,
    scene_inc: int | None,
    pressure_inc: int | None,
    clock_incs,
    clock_sets,
    clamp: bool = True,
):
    data = load_yaml(tracker_path)
    changed_paths: list[str] = []
    if scene_inc is not None:
        scene = data.get("scene", 0)
        if not isinstance(scene, int):
            raise ValueError("tracker scene is not an integer")
        data["scene"] = scene + scene_inc

    clocks = data.setdefault("clocks", {})

    def apply_clock(name, inc=None, set_value=None):
        clock = clocks.setdefault(name, {})
        clock.setdefault("name", name)
        clock.setdefault("current", 0)
        clock.setdefault("max", 5)
        current = clock.get("current", 0)
        if not isinstance(current, int):
            raise ValueError(f"clock {name} current is not an integer")
        if set_value is not None:
            current = set_value
        if inc is not None:
            current += inc
        clock["current"] = current
        changed_paths.append(f"clocks.{name}.current")

    if pressure_inc is not None:
        apply_clock("pressure", inc=pressure_inc)

    for name, inc in clock_incs:
        apply_clock(name, inc=inc)

    for name, value in clock_sets:
        apply_clock(name, set_value=value)

    if clamp:
        _sslib.clamp_currents(data, changed_paths)

    save_yaml(tracker_path, data)


def parse_kv(item: str):
    if "=" not in item:
        raise ValueError(f"Expected name=value, got '{item}'")
    key, value = item.split("=", 1)
    return key.strip(), value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a session recap to memory and update trackers.")
    parser.add_argument("--campaign", help="Campaign slug under campaigns/")
    parser.add_argument("--memory", help="Memory YAML file to update")
    parser.add_argument("--new", action="store_true", help="Create a new session file")

    parser.add_argument("--summary", action="append", default=[], help="Summary line (repeatable)")
    parser.add_argument("--thread", action="append", default=[], help="Open thread (repeatable)")
    parser.add_argument("--npc", action="append", default=[], help="NPC update (repeatable)")
    parser.add_argument("--secret", action="append", default=[], help="Secret note (repeatable)")

    parser.add_argument("--scene-inc", type=int, help="Increment scene counter")
    parser.add_argument("--pressure-inc", type=int, help="Increment pressure clock")
    parser.add_argument("--clock-inc", action="append", default=[], help="Clock increment name=delta")
    parser.add_argument("--clock-set", action="append", default=[], help="Clock set name=value")
    parser.add_argument("--tracker", help="Tracker YAML file (overrides campaign default)")
    parser.add_argument("--no-clamp", dest="clamp", action="store_false", help="Disable clock clamping")
    parser.set_defaults(clamp=True)

    args = parser.parse_args()

    memory_path = None
    tracker_path = None

    if args.memory:
        memory_path = Path(args.memory)
        if not memory_path.is_absolute():
            memory_path = ROOT / memory_path

    if args.campaign:
        campaign_dir = ROOT / "campaigns" / args.campaign
        if not campaign_dir.exists():
            print(f"error: campaign not found: {campaign_dir}", file=sys.stderr)
            return 1
        memory_dir = campaign_dir / "state" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        if memory_path is None:
            if args.new:
                memory_path = next_session_path(memory_dir)
            else:
                memory_path = find_latest_session(memory_dir) or next_session_path(memory_dir)

        tracker_path = campaign_dir / "state" / "trackers" / "session.yaml"

    if args.tracker:
        tracker_path = Path(args.tracker)
        if not tracker_path.is_absolute():
            tracker_path = ROOT / tracker_path

    if not memory_path:
        print("error: provide --memory or --campaign", file=sys.stderr)
        return 1

    data = load_yaml(memory_path)
    if "schema_version" not in data:
        data["schema_version"] = 1

    summaries = ensure_list(data.get("summary"))
    threads = ensure_list(data.get("threads"))
    npcs = ensure_list(data.get("npcs"))
    secrets = ensure_list(data.get("secrets"))

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in args.summary:
        summaries.append(f"[{timestamp}] {item}")
    threads.extend(args.thread)
    npcs.extend(args.npc)
    secrets.extend(args.secret)

    data["summary"] = summaries
    data["threads"] = threads
    data["npcs"] = npcs
    data["secrets"] = secrets

    save_yaml(memory_path, data)

    clock_incs = []
    for item in args.clock_inc:
        name, value = parse_kv(item)
        clock_incs.append((name, int(value)))

    clock_sets = []
    for item in args.clock_set:
        name, value = parse_kv(item)
        clock_sets.append((name, int(value)))

    if tracker_path and (args.scene_inc is not None or args.pressure_inc is not None or clock_incs or clock_sets):
        try:
            update_tracker(tracker_path, args.scene_inc, args.pressure_inc, clock_incs, clock_sets, clamp=args.clamp)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    print(f"recap saved to {memory_path}")
    if tracker_path and (args.scene_inc is not None or args.pressure_inc is not None or clock_incs or clock_sets):
        print(f"tracker updated: {tracker_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
