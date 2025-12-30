#!/usr/bin/env python3
import sys
from pathlib import Path
from subprocess import run

TOOLS = {
    "campaign_init": "campaign_init.py",
    "build_prompt": "build_prompt.py",
    "prompt": "build_prompt.py",
    "roll": "roll.py",
    "beat": "beat.py",
    "apply_roll": "apply_roll.py",
    "recap": "recap.py",
    "session_log": "session_log.py",
    "summary": "summary.py",
    "new_session": "new_session.py",
    "trackers": "trackers.py",
    "update_sheet": "update_sheet.py",
    "recalc_sheet": "recalc_sheet.py",
    "gen_character": "gen_character.py",
    "char_builder": "char_builder.py",
    "validate_repo": "validate_repo.py",
    "release_build": "release_build.py",
    "validate_campaign": "validate_campaign.py",
    "validate_sheet": "validate_sheet.py",
    "doctor": "doctor.py",
    "checkpoint": "checkpoint.py",
    "resume_pack": "resume_pack.py",
    "new_skin": "new_skin.py",
}


def print_help() -> None:
    print("Usage: python tools/ss.py <command> [args...]\n")
    print("Commands:")
    for key in sorted(TOOLS.keys()):
        print(f"  {key}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        return 0

    if sys.argv[1] in ("--list", "list"):
        for key in sorted(TOOLS.keys()):
            print(key)
        return 0

    command = sys.argv[1]
    script = TOOLS.get(command)
    if not script:
        print(f"error: unknown command '{command}'", file=sys.stderr)
        print_help()
        return 1

    tool_path = Path(__file__).resolve().parent / script
    args = [sys.executable, str(tool_path)] + sys.argv[2:]
    result = run(args)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
