#!/usr/bin/env python3
import argparse
import json
import random
import sys


def roll_d20():
    return random.randint(1, 20)


def resolve_check(stat, adv=False, dis=False):
    rolls = [roll_d20()]
    if adv or dis:
        rolls.append(roll_d20())

    if adv:
        chosen = min(rolls)
    elif dis:
        chosen = max(rolls)
    else:
        chosen = rolls[0]

    success = chosen <= stat
    margin = stat - chosen
    crit = None
    if chosen == 1:
        crit = "nat1"
    elif chosen == 20:
        crit = "nat20"

    return {
        "stat": stat,
        "rolls": rolls,
        "result": chosen,
        "success": success,
        "margin": margin,
        "crit": crit,
        "adv": bool(adv),
        "dis": bool(dis),
    }


def command_check(args):
    data = resolve_check(args.stat, adv=args.adv, dis=args.dis)
    return data


def command_opposed(args):
    attacker = resolve_check(args.attacker, adv=args.adv_attacker, dis=args.dis_attacker)
    defender = resolve_check(args.defender, adv=args.adv_defender, dis=args.dis_defender)

    outcome = {
        "winner": None,
        "reason": None,
    }

    if attacker["success"] and not defender["success"]:
        outcome["winner"] = "attacker"
        outcome["reason"] = "attacker_success_only"
    elif defender["success"] and not attacker["success"]:
        outcome["winner"] = "defender"
        outcome["reason"] = "defender_success_only"
    elif attacker["success"] and defender["success"]:
        if attacker["margin"] > defender["margin"]:
            outcome["winner"] = "attacker"
            outcome["reason"] = "higher_margin"
        elif defender["margin"] > attacker["margin"]:
            outcome["winner"] = "defender"
            outcome["reason"] = "higher_margin"
        else:
            outcome["winner"] = "defender"
            outcome["reason"] = "tie_margins_defender"
    else:
        outcome["winner"] = "defender"
        outcome["reason"] = "both_failed_defender"

    return {
        "attacker": attacker,
        "defender": defender,
        "outcome": outcome,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll d20 checks for Sinew & Steel.")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible rolls")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Single roll-under check")
    check.add_argument("--stat", type=int, required=True)
    check.add_argument("--adv", action="store_true")
    check.add_argument("--dis", action="store_true")

    opposed = subparsers.add_parser("opposed", help="Opposed roll-under check")
    opposed.add_argument("--attacker", type=int, required=True)
    opposed.add_argument("--defender", type=int, required=True)
    opposed.add_argument("--adv-attacker", action="store_true")
    opposed.add_argument("--dis-attacker", action="store_true")
    opposed.add_argument("--adv-defender", action="store_true")
    opposed.add_argument("--dis-defender", action="store_true")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    if args.command == "check":
        if args.adv and args.dis:
            print("error: choose only one of --adv or --dis", file=sys.stderr)
            return 1
        data = command_check(args)
    else:
        if args.adv_attacker and args.dis_attacker:
            print("error: choose only one of --adv-attacker or --dis-attacker", file=sys.stderr)
            return 1
        if args.adv_defender and args.dis_defender:
            print("error: choose only one of --adv-defender or --dis-defender", file=sys.stderr)
            return 1
        data = command_opposed(args)

    if args.pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
