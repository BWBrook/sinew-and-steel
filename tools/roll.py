#!/usr/bin/env python3
import argparse
import json
import sys

import random

import _dice
import _sslib


def command_check(args):
    data = _dice.resolve_check(args.stat, adv=args.adv, dis=args.dis)
    if args.nudge:
        data = _dice.apply_nudge_to_check(data, args.nudge)
    return data


def command_opposed(args):
    return _dice.resolve_opposed(
        args.attacker,
        args.defender,
        adv_attacker=args.adv_attacker,
        dis_attacker=args.dis_attacker,
        adv_defender=args.adv_defender,
        dis_defender=args.dis_defender,
    )


def main() -> int:
    # Global flags are parsed separately so they can appear before or after the subcommand.
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--seed", type=int, help="Random seed for reproducible rolls")
    global_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    command_parser = argparse.ArgumentParser(description="Roll d20 checks for Sinew & Steel.")
    subparsers = command_parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Single roll-under check")
    check.add_argument("--stat", type=int, required=True)
    check.add_argument("--adv", action="store_true")
    check.add_argument("--dis", action="store_true")
    check.add_argument("--nudge", type=int, default=0, help="Nudge the chosen die result by N")

    opposed = subparsers.add_parser("opposed", help="Opposed roll-under check")
    opposed.add_argument("--attacker", type=int, required=True)
    opposed.add_argument("--defender", type=int, required=True)
    opposed.add_argument("--adv-attacker", action="store_true")
    opposed.add_argument("--dis-attacker", action="store_true")
    opposed.add_argument("--adv-defender", action="store_true")
    opposed.add_argument("--dis-defender", action="store_true")

    global_args, remaining = global_parser.parse_known_args()
    command_args = command_parser.parse_args(remaining)
    merged = vars(global_args).copy()
    merged.update(vars(command_args))
    args = argparse.Namespace(**merged)

    if args.seed is not None:
        random.seed(args.seed)

    if args.command == "check":
        if args.adv and args.dis:
            print("error: choose only one of --adv or --dis", file=sys.stderr)
            return 1
        try:
            data = command_check(args)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        if args.adv_attacker and args.dis_attacker:
            print("error: choose only one of --adv-attacker or --dis-attacker", file=sys.stderr)
            return 1
        if args.adv_defender and args.dis_defender:
            print("error: choose only one of --adv-defender or --dis-defender", file=sys.stderr)
            return 1
        data = command_opposed(args)

    data["schema_version"] = 1
    data["tool_version"] = _sslib.repo_version()

    if args.pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
