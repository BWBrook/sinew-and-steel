#!/usr/bin/env python3
"""Independent, reproducible checks for the Sinew & Steel skin audit.

This script intentionally derives its calculations from the published rules and
the Delvekit generator API.  It does not import or depend on the engine-atlas
analysis.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import _delvekit  # noqa: E402


def straight_success(score: int) -> float:
    """Published straight roll-under probability for legal PC scores."""
    if not 1 <= score <= 19:
        raise ValueError("score must be between 1 and 19")
    return score / 20.0


def advantage_success(score: int) -> float:
    p = straight_success(score)
    return 1.0 - (1.0 - p) ** 2


def reroll_success(p_check: float) -> float:
    """Chance of success when one failed check may be rerolled once."""
    return 1.0 - (1.0 - p_check) ** 2


def pct(p: float) -> str:
    return f"{100.0 * p:.4f}%"


def exact_results() -> dict[str, Any]:
    scan_rows = []
    for score in (10, 13, 16):
        p_quick = advantage_success(score)
        p_deep = straight_success(score)
        scan_rows.append(
            {
                "SYS": score,
                "quick_success": p_quick,
                "deep_success": p_deep,
                "quick_at_least_one_in_4": 1.0 - (1.0 - p_quick) ** 4,
                "quick_expected_data_points_in_4": 4.0 * p_quick,
            }
        )

    trade_rows = []
    for score in (8, 10, 12, 14, 16):
        p_expertise = advantage_success(score)
        p_broker = reroll_success(p_expertise)
        q_first = 1.0 - p_expertise
        q_final = 1.0 - p_broker
        trade_rows.append(
            {
                "trade_score": score,
                "expertise_success": p_expertise,
                "expertise_plus_broker_success": p_broker,
                "expected_shares_per_unconstrained_port_call": p_broker,
                "expected_calls_to_gain_10_shares": 10.0 / p_broker,
                "expected_knack_costs_per_call": q_first,
                "expected_final_failures_per_call": q_final,
            }
        )

    temporal_rows = []
    for score in (10, 13, 16):
        for advantage in (False, True):
            p = advantage_success(score) if advantage else straight_success(score)
            temporal_rows.append(
                {
                    "INT": score,
                    "advantage": advantage,
                    "one_attempt_success": p,
                    "success_within_3_repeatable_attempts": 1.0 - (1.0 - p) ** 3,
                    "expected_failures_before_success_if_repeatable": (1.0 - p) / p,
                }
            )

    pressure_rows = []
    for start in (3, 4):
        for gain in (2, 3):
            total = start + gain
            crises = total // 5
            pressure_rows.append(
                {
                    "start": start,
                    "gain": gain,
                    "crises": crises,
                    "final_if_overflow_discarded": 0 if total >= 5 else total,
                    "final_if_overflow_carried": total % 5,
                }
            )

    # Twilight assemblies: each speaker contributes -1, 0, 1, or 2.
    # At score 12 the exact per-speaker probabilities are 1/20, 7/20,
    # 11/20, and 1/20 respectively.
    assembly_rows = []
    contribution = {-1: 1 / 20, 0: 7 / 20, 1: 11 / 20, 2: 1 / 20}
    for speakers in range(1, 7):
        distribution = {0: 1.0}
        for _ in range(speakers):
            updated: dict[int, float] = {}
            for subtotal, subtotal_p in distribution.items():
                for value, value_p in contribution.items():
                    updated[subtotal + value] = updated.get(subtotal + value, 0.0) + subtotal_p * value_p
            distribution = updated
        assembly_rows.append(
            {
                "speakers": speakers,
                "petty_threshold_3": sum(p for total, p in distribution.items() if total >= 3),
                "great_threshold_5": sum(p for total, p in distribution.items() if total >= 5),
                "expected_points": 0.6 * speakers,
            }
        )

    role_rows = []
    for score in (10, 12, 14):
        p = straight_success(score)
        role_rows.append(
            {
                "score": score,
                "one_test_failure": 1.0 - p,
                "at_least_one_failure_across_3_roles": 1.0 - p**3,
                "all_3_succeed": p**3,
            }
        )

    return {
        "scanner": scan_rows,
        "trade": trade_rows,
        "temporal_intervention": temporal_rows,
        "pressure_overflow": pressure_rows,
        "twilight_assembly": assembly_rows,
        "three_role_travel": role_rows,
        "rest_loop": {
            "assumption": "Each short rest restores +1 Luck and +1 Stamina; no mandatory cost is imposed.",
            "start": {"luck": 4, "luck_max": 12, "stamina": 1, "stamina_max": 5},
            "rests_to_full_both": max(12 - 4, 5 - 1),
            "end": {"luck": 12, "stamina": 5},
        },
    }


def delvekit_simulation(n: int, seed_base: int) -> dict[str, Any]:
    results: dict[str, Any] = {}
    bounds = {name: config["rooms"] for name, config in _delvekit.SIZE_CONFIG.items()}

    for size in ("tiny", "medium", "large"):
        for difficulty in ("soft", "medium", "hard"):
            counts: Counter[str] = Counter()
            feature_sum = 0
            for offset in range(n):
                data = _delvekit.generate_dungeon(
                    seed=seed_base + offset,
                    size=size,
                    difficulty=difficulty,
                )
                rooms = data["rooms"]
                flags = {
                    "key": bool(data["keys"]),
                    "factions": bool(data["factions"]),
                    "solo": bool(data["solo_monsters"]),
                    "boss": bool(data["bosses"]),
                    "trap": any(room["trap_tags"] for room in rooms),
                    "puzzle": any(room["puzzle_tags"] for room in rooms),
                    "weird_npc": bool(data["weird_npcs"]),
                }
                feature_sum += sum(flags.values())
                counts.update({name: int(value) for name, value in flags.items()})
                lo, hi = bounds[size]
                counts["room_bound_failures"] += int(not lo <= len(rooms) <= hi)
                counts["multiple_trap_rooms"] += int(
                    sum(bool(room["trap_tags"]) for room in rooms) > 1
                )
                counts["nonbinary_faction_counts"] += int(len(data["factions"]) not in (0, 2))
                counts["start_not_discovered"] += int("1" not in data["player_map"]["discovered_rooms"])

            key = f"{size}/{difficulty}"
            results[key] = {
                "n": n,
                "mean_feature_classes": feature_sum / n,
                "feature_rates": {
                    name: counts[name] / n
                    for name in ("key", "factions", "solo", "boss", "trap", "puzzle", "weird_npc")
                },
                "invariant_failures": {
                    name: counts[name]
                    for name in (
                        "room_bound_failures",
                        "multiple_trap_rooms",
                        "nonbinary_faction_counts",
                        "start_not_discovered",
                    )
                },
                "binomial_mc_se_upper_bound": math.sqrt(0.25 / n),
            }
    return results


def markdown_report(payload: dict[str, Any]) -> str:
    exact = payload["exact"]
    lines = [
        "# Independent skin calculations",
        "",
        "The exact counterfactual sections preserve the pre-repair literal readings used by the audit. The Delvekit section always measures the generator in the working tree where this script is run.",
        "",
    ]

    lines.extend(
        [
            "## Service Duct scanner: baseline repeated-scan counterfactual (exact)",
            "",
            "| SYS | Quick success | Deep success | >=1 Quick success in 4 | Expected Quick data points in 4 |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in exact["scanner"]:
        lines.append(
            f"| {row['SYS']} | {pct(row['quick_success'])} | {pct(row['deep_success'])} | "
            f"{pct(row['quick_at_least_one_in_4'])} | {row['quick_expected_data_points_in_4']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Free Trader port calls: baseline unconstrained-trade counterfactual (exact)",
            "",
            "Assumes the free Expertise applies to the trade stat, Merchant Broker is used only after a failed first check, and a successful call chooses +1 Ship Share.",
            "",
            "| Score | Expertise success | With Broker | Shares/call | Calls per +10 Shares | Knack costs/call | Final failures/call |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in exact["trade"]:
        lines.append(
            f"| {row['trade_score']} | {pct(row['expertise_success'])} | "
            f"{pct(row['expertise_plus_broker_success'])} | "
            f"{row['expected_shares_per_unconstrained_port_call']:.4f} | "
            f"{row['expected_calls_to_gain_10_shares']:.3f} | "
            f"{row['expected_knack_costs_per_call']:.4f} | "
            f"{row['expected_final_failures_per_call']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Time Odyssey historical interventions: baseline unchanged-retry counterfactual (exact)",
            "",
            "| INT | Advantage | One attempt | Success within 3 if retries are allowed | Expected failed attempts before success |",
            "|---:|:---:|---:|---:|---:|",
        ]
    )
    for row in exact["temporal_intervention"]:
        lines.append(
            f"| {row['INT']} | {'yes' if row['advantage'] else 'no'} | "
            f"{pct(row['one_attempt_success'])} | "
            f"{pct(row['success_within_3_repeatable_attempts'])} | "
            f"{row['expected_failures_before_success_if_repeatable']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Pressure overflow interpretation sensitivity (exact)",
            "",
            "| Start | Gain | Crises | Final if overflow discarded | Final if overflow carried |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for row in exact["pressure_overflow"]:
        lines.append(
            f"| {row['start']} | +{row['gain']} | {row['crises']} | "
            f"{row['final_if_overflow_discarded']} | {row['final_if_overflow_carried']} |"
        )

    lines.extend(
        [
            "",
            "## Twilight baseline group assemblies at HRT 12 (exact)",
            "",
            "No Hope/Companionship spend; natural 1 contributes +2 and natural 20 contributes -1.",
            "",
            "| Speaking PCs | Expected points | P(threshold 3) | P(threshold 5) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in exact["twilight_assembly"]:
        lines.append(
            f"| {row['speakers']} | {row['expected_points']:.2f} | "
            f"{pct(row['petty_threshold_3'])} | {pct(row['great_threshold_5'])} |"
        )

    lines.extend(
        [
            "",
            "## Baseline compulsory three-role travel/jump burden (exact)",
            "",
            "Assumes three independent straight tests at the same score; this contrasts with a one-test leg.",
            "",
            "| Score | One-test failure | >=1 failure across 3 roles | All 3 succeed |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in exact["three_role_travel"]:
        lines.append(
            f"| {row['score']} | {pct(row['one_test_failure'])} | "
            f"{pct(row['at_least_one_failure_across_3_roles'])} | {pct(row['all_3_succeed'])} |"
        )

    rest = exact["rest_loop"]
    lines.extend(
        [
            "",
            "## Baseline no-cost rest-loop witness (deterministic)",
            "",
            f"Under the stated no-mandatory-cost assumption, Luck {rest['start']['luck']}/{rest['start']['luck_max']} and Stamina {rest['start']['stamina']}/{rest['start']['stamina_max']} both refill after **{rest['rests_to_full_both']}** short rests.",
            "",
            "## Delvekit seeded generator audit (current working tree)",
            "",
            f"Seed base `{payload['parameters']['seed_base']}`; `{payload['parameters']['delve_seeds']}` generated sites per size/difficulty cell.",
            "",
            "| Cell | Key | Factions | Solo | Boss | Trap | Puzzle | Weird NPC | Mean feature classes | Invariant failures |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for cell, row in payload["delvekit"].items():
        rates = row["feature_rates"]
        inv = sum(row["invariant_failures"].values())
        lines.append(
            f"| {cell} | {pct(rates['key'])} | {pct(rates['factions'])} | "
            f"{pct(rates['solo'])} | {pct(rates['boss'])} | {pct(rates['trap'])} | "
            f"{pct(rates['puzzle'])} | {pct(rates['weird_npc'])} | "
            f"{row['mean_feature_classes']:.3f} | {inv} |"
        )
    lines.append("")
    lines.append(
        "Maximum binomial Monte Carlo standard error per cell is "
        f"{100.0 * next(iter(payload['delvekit'].values()))['binomial_mc_se_upper_bound']:.3f} percentage points."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delve-seeds", type=int, default=1000)
    parser.add_argument("--seed-base", type=int, default=20260920)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args()
    if args.delve_seeds < 1:
        parser.error("--delve-seeds must be positive")

    payload = {
        "parameters": {"delve_seeds": args.delve_seeds, "seed_base": args.seed_base},
        "exact": exact_results(),
        "delvekit": delvekit_simulation(args.delve_seeds, args.seed_base),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(markdown_report(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
