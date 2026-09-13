"""Engine atlas: exact sweep of every interaction in the Sinew & Steel engine.

Writes figures to docs/engine_atlas/figures/ and data tables to
docs/engine_atlas/tables.md. The commentary lives in docs/engine_atlas.md.

Run from the repo root:
    uv run --extra analysis python tools/analysis/atlas.py
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (  # noqa: E402
    DIE,
    build_cost,
    damage_dist,
    damage_for,
    die_dist,
    expected_damage,
    expected_exchanges_to_drop,
    is_success,
    luck_test,
    margin_bonus,
    margin_dist_on_success,
    nudge_policy,
    opposed_outcomes,
    p_attacker_wins,
    p_success,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "engine_atlas"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

SCORES = list(range(6, 17))
TIERS = [
    # name, score, STM, edge, soak
    ("Peasant", 8, 3, 0, 0),
    ("Soldier", 10, 4, 1, 1),
    ("Elite", 12, 5, 1, 1),
    ("Monster", 14, 6, 2, 1),
    ("Nemesis", 16, 7, 2, 3),
]
TABLES: list[str] = []


def f(x, nd=2) -> str:
    return f"{float(x):.{nd}f}"


def pct(x, nd=1) -> str:
    return f"{float(x) * 100:.{nd}f}%"


def table(title: str, header: list[str], rows: list[list[str]]) -> None:
    TABLES.append(f"### {title}\n")
    TABLES.append("| " + " | ".join(header) + " |")
    TABLES.append("|" + "---|" * len(header))
    for r in rows:
        TABLES.append("| " + " | ".join(r) + " |")
    TABLES.append("")


def savefig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / f"{name}.png", dpi=130)
    plt.close()


plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3})


# ---------------------------------------------------------------------------
# 1. Single tests
# ---------------------------------------------------------------------------
def section_success() -> None:
    xs = list(range(3, 21))
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for mode, label in (("straight", "straight"), ("advantage", "Advantage"), ("disadvantage", "Disadvantage")):
        ys = [float(p_success(a, mode)) * 100 for a in xs]
        axes[0].plot(xs, ys, marker="o", ms=3, label=label)
    axes[0].axvspan(6, 16, color="grey", alpha=0.08, label="legal range 6-16")
    axes[0].set_xlabel("attribute"); axes[0].set_ylabel("P(success) %"); axes[0].set_title("Chance to succeed")
    axes[0].legend(fontsize=8)
    # marginal value of +1 and value of Advantage over straight
    adv_gain = [(float(p_success(a, "advantage") - p_success(a))) * 100 for a in xs]
    dis_loss = [(float(p_success(a) - p_success(a, "disadvantage"))) * 100 for a in xs]
    axes[1].plot(xs, adv_gain, marker="o", ms=3, label="Advantage gain (pp)")
    axes[1].plot(xs, dis_loss, marker="s", ms=3, label="Disadvantage loss (pp)")
    axes[1].axhline(5, color="k", ls="--", lw=0.8, label="+1 attribute = 5 pp")
    axes[1].set_xlabel("attribute"); axes[1].set_ylabel("percentage points"); axes[1].set_title("What Advantage is worth")
    axes[1].legend(fontsize=8)
    savefig("01_success_curves")

    rows = []
    for a in SCORES:
        rows.append([str(a), pct(p_success(a)), pct(p_success(a, "advantage")), pct(p_success(a, "disadvantage")),
                     f((p_success(a, "advantage") - p_success(a)) * 100, 1), f((p_success(a) - p_success(a, "disadvantage")) * 100, 1)])
    table("Single test: success by attribute", ["attr", "straight", "Adv", "Dis", "Adv gain (pp)", "Dis loss (pp)"], rows)


# ---------------------------------------------------------------------------
# 2. Margin bonus
# ---------------------------------------------------------------------------
def section_margin() -> None:
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    for mode, ls in (("straight", "-"), ("advantage", "--")):
        p1 = [float(sum(p for m, p in margin_dist_on_success(a, mode).items() if margin_bonus(m) >= 1)) * 100 for a in SCORES]
        p2 = [float(sum(p for m, p in margin_dist_on_success(a, mode).items() if margin_bonus(m) >= 2)) * 100 for a in SCORES]
        ax.plot(SCORES, p1, ls=ls, marker="o", ms=3, color="C0", label=f"+1 or more ({mode})")
        ax.plot(SCORES, p2, ls=ls, marker="s", ms=3, color="C3", label=f"+2 ({mode})")
    ax.set_xlabel("attribute"); ax.set_ylabel("% of successful hits"); ax.set_title("Margin bonus: share of hits that earn +1 / +2 damage")
    ax.legend(fontsize=8)
    savefig("02_margin_bonus")

    rows = []
    for a in SCORES:
        md = margin_dist_on_success(a)
        e = sum(margin_bonus(m) * p for m, p in md.items())
        rows.append([str(a), f(sum(m * p for m, p in md.items())), f(e, 3),
                     pct(sum(p for m, p in md.items() if margin_bonus(m) >= 1)),
                     pct(sum(p for m, p in md.items() if margin_bonus(m) >= 2))])
    table("Margin on a successful test", ["attr", "E[margin]", "E[bonus]", "P(bonus>=1)", "P(bonus>=2)"], rows)


# ---------------------------------------------------------------------------
# 3. Opposed tests
# ---------------------------------------------------------------------------
def section_opposed() -> None:
    combos = [("straight", "straight", "no Advantage"), ("advantage", "straight", "attacker Advantage"),
              ("straight", "advantage", "defender Advantage"), ("disadvantage", "straight", "attacker Disadvantage")]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4))
    for ax, (am, dm, title) in zip(axes, combos):
        grid = [[float(p_attacker_wins(a, d, am, dm)) * 100 for d in SCORES] for a in SCORES]
        im = ax.imshow(grid, origin="lower", cmap="RdYlGn", vmin=0, vmax=100, extent=[5.5, 16.5, 5.5, 16.5])
        for i, a in enumerate(SCORES):
            for j, d in enumerate(SCORES):
                if (a - 6) % 2 == 0 and (d - 6) % 2 == 0:
                    ax.text(d, a, f"{grid[i][j]:.0f}", ha="center", va="center", fontsize=6)
        ax.set_xlabel("defender attribute"); ax.set_ylabel("attacker attribute"); ax.set_title(title, fontsize=9)
    fig.colorbar(im, ax=axes, fraction=0.015, label="attacker wins %")
    plt.savefig(FIG / "03_opposed_grid.png", dpi=130, bbox_inches="tight"); plt.close()

    rows = []
    for s in SCORES:
        o = opposed_outcomes(s, s)
        rows.append([f"{s} vs {s}", pct(o["attacker"]), pct(o["both_fail"]), pct(o["both_succeed_dfn"]),
                     pct(p_attacker_wins(s, s, "advantage", "straight")), pct(p_attacker_wins(s, s, "straight", "advantage"))])
    table("Symmetric opposed tests", ["matchup", "attacker wins", "both fail (defender)", "tie or lower margin (defender)",
                                     "attacker with Adv", "defender with Adv"], rows)


# ---------------------------------------------------------------------------
# 4. Damage
# ---------------------------------------------------------------------------
def section_damage() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharey=True)
    for ax, edge in zip(axes, (0, 1, 2)):
        for soak in range(4):
            ys = [float(expected_damage(a, 10, edge, soak)) for a in SCORES]
            ax.plot(SCORES, ys, marker="o", ms=3, label=f"soak {soak}")
        ax.set_title(f"edge +{edge}"); ax.set_xlabel("attacker attribute")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("expected damage per exchange (defender 10)")
    savefig("04_expected_damage")

    # damage distribution panel for a standard exchange
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.0), sharey=True)
    for ax, soak in zip(axes, range(4)):
        dd = damage_dist(12, 10, 1, soak)
        ks = sorted(dd); ax.bar(ks, [float(dd[k]) * 100 for k in ks], color="C0")
        ax.set_title(f"att 12, edge +1 vs soak {soak}"); ax.set_xlabel("damage"); ax.set_xticks(range(0, 6))
    axes[0].set_ylabel("% of exchanges")
    savefig("05_damage_distribution")

    rows = []
    for a in SCORES:
        row = [str(a), pct(p_attacker_wins(a, 10))]
        for edge in (0, 1, 2):
            row.append(" / ".join(f(expected_damage(a, 10, edge, s)) for s in range(4)))
        rows.append(row)
    table("Expected damage per exchange vs defender 10 (soak 0 / 1 / 2 / 3)", ["attr", "P(hit)", "edge +0", "edge +1", "edge +2"], rows)

    rows = []
    for name, score, stm, edge, soak in TIERS:
        base = expected_damage(score, 10, edge, 0)
        rows.append([f"{name} ({score}, +{edge})"] + [pct(expected_damage(score, 10, edge, s) / base, 0) for s in (1, 2, 3)])
    table("What armour is worth: expected damage as share of unarmoured", ["attacker", "soak 1", "soak 2", "soak 3"], rows)


# ---------------------------------------------------------------------------
# 5. Time to kill, race ratios, survival curves, parties
# ---------------------------------------------------------------------------
def survival_curve(stamina: int, att: int, dfn: int, edge: int, soak: int, n_max: int = 15) -> list[float]:
    dd = damage_dist(att, dfn, edge, soak)
    state = {stamina: Fraction(1)}
    alive = []
    for _ in range(n_max):
        nxt: dict[int, Fraction] = {}
        for s, p in state.items():
            if s <= 0:
                nxt[0] = nxt.get(0, Fraction(0)) + p
                continue
            for d, q in dd.items():
                ns = max(0, s - d)
                nxt[ns] = nxt.get(ns, Fraction(0)) + p * q
        state = nxt
        alive.append(float(sum(p for s, p in state.items() if s > 0)))
    return alive


def party_rounds(n_pcs: int, stamina: int, att: int, dfn: int, edge: int, soak: int):
    """Expected rounds for n attackers (identical) to drop a target; exact via n-fold convolution."""
    single = damage_dist(att, dfn, edge, soak)
    conv = {0: Fraction(1)}
    for _ in range(n_pcs):
        nxt: dict[int, Fraction] = {}
        for a, p in conv.items():
            for b, q in single.items():
                nxt[a + b] = nxt.get(a + b, Fraction(0)) + p * q
        conv = nxt
    p0 = conv.get(0, Fraction(0))
    E: dict[int, Fraction] = {s: Fraction(0) for s in range(-60, 1)}
    for s in range(1, stamina + 1):
        acc = Fraction(1)
        for d, p in conv.items():
            if d >= 1:
                acc += p * E[max(s - d, -60)]
        E[s] = acc / (1 - p0)
    return E[stamina]


def section_ttk() -> None:
    pcs = [10, 12, 14, 16]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    for name, score, stm, edge, soak in TIERS:
        ys = [float(expected_exchanges_to_drop(stm, a, score - 2, 1, soak)) for a in pcs]
        axes[0].plot(pcs, ys, marker="o", ms=3, label=name)
    axes[0].set_yscale("log"); axes[0].set_xlabel("PC attribute (edge +1)"); axes[0].set_ylabel("exchanges to drop NPC (log)")
    axes[0].set_title("PC dropping each tier"); axes[0].legend(fontsize=8)
    for soak, ls in ((0, "-"), (1, "--"), (2, ":")):
        ys = [float(expected_exchanges_to_drop(5, score, 10, edge, soak)) for _, score, _, edge, _ in TIERS]
        axes[1].plot([t[0] for t in TIERS], ys, ls=ls, marker="o", ms=3, label=f"PC soak {soak}")
    axes[1].set_yscale("log"); axes[1].set_ylabel("exchanges to drop a STM-5 PC (log)"); axes[1].set_title("Each tier dropping a PC")
    axes[1].legend(fontsize=8)
    savefig("06_time_to_kill")

    rows = []
    for name, score, stm, edge, soak in TIERS:
        pc = expected_exchanges_to_drop(stm, 12, score - 2, 1, soak)
        npc = expected_exchanges_to_drop(5, score, 12, edge, 1)
        rows.append([name, f(pc), f(npc), f(pc / npc)])
    table("Race: PC (att 12, edge +1, STM 5, soak 1) vs tier; ratio > 1 means the NPC wins", ["tier", "PC needs", "NPC needs", "ratio"], rows)

    # survival curves
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    for name, score, stm, edge, soak in TIERS:
        ax.plot(range(1, 16), [v * 100 for v in survival_curve(5, score, 10, edge, 1)], marker="o", ms=3, label=name)
    ax.set_xlabel("exchanges taken"); ax.set_ylabel("P(PC still standing) %"); ax.set_title("Survival of a STM-5 PC in hide (soak 1) under repeated attack")
    ax.legend(fontsize=8)
    savefig("07_survival_curves")

    rows = []
    for n in (1, 2, 3, 4):
        row = [str(n)]
        for name, score, stm, edge, soak in TIERS[2:]:
            rounds = party_rounds(n, stm, 12, score - 2, 1, soak)
            dealt = rounds * expected_damage(score, 10, edge, 1)
            row.append(f"{f(rounds)} rounds, {f(dealt)} STM taken")
        rows.append(row)
    table("Party of N (att 12, edge +1, soak 1) vs Elite / Monster / Nemesis: expected rounds and party Stamina lost",
          ["PCs", "Elite", "Monster", "Nemesis"], rows)


# ---------------------------------------------------------------------------
# 6. Luck economics and pool dynamics
# ---------------------------------------------------------------------------
def luck_pool_trajectory_exact(luck: int, attribute: int, threshold: int, beats: int, roll_prob: float, rest_every: int):
    state = {luck: 1.0}
    traj = []
    for b in range(1, beats + 1):
        nxt: dict[int, float] = {}
        for tok, p in state.items():
            nxt[tok] = nxt.get(tok, 0.0) + p * (1 - roll_prob)
            for r in range(1, DIE + 1):
                q = p * roll_prob / DIE
                spend = 0
                if not is_success(r, attribute) and r != DIE:
                    deficit = r - attribute
                    if 0 < deficit <= threshold and deficit <= tok:
                        spend = deficit
                nt = tok - spend
                nxt[nt] = nxt.get(nt, 0.0) + q
        if b % rest_every == 0:
            rested: dict[int, float] = {}
            for t, p in nxt.items():
                nt = min(luck, t + 1)
                rested[nt] = rested.get(nt, 0.0) + p
            nxt = rested
        state = nxt
        traj.append((sum(t * p for t, p in state.items()), sum(p for t, p in state.items() if t <= 1)))
    return traj


def section_luck() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.4))
    # nudge value curve
    for a in (8, 10, 12, 14):
        ps, costs = zip(*[nudge_policy(a, n) for n in range(0, 7)])
        axes[0].plot([float(c) for c in costs], [float(p) * 100 for p in ps], marker="o", ms=3, label=f"attr {a}")
    axes[0].set_xlabel("expected tokens spent per check"); axes[0].set_ylabel("P(success) %"); axes[0].set_title("Rescue policy: success bought per token")
    axes[0].legend(fontsize=8)
    # luck test odds
    axes[1].plot(range(0, 17), [float(luck_test(t)) * 100 for t in range(0, 17)], marker="o", ms=3)
    axes[1].set_xlabel("current tokens"); axes[1].set_ylabel("P(Luck test) %"); axes[1].set_title("Luck test succeeds on roll <= current tokens")
    # pool trajectory
    for luck, thr, color in ((8, 2, "C0"), (8, 3, "C1"), (12, 3, "C2")):
        traj = luck_pool_trajectory_exact(luck, 12, thr, 16, roll_prob=0.6, rest_every=6)
        axes[2].plot(range(1, 17), [t[0] for t in traj], color=color, label=f"Luck {luck}, rescue <= {thr}")
        axes[2].plot(range(1, 17), [t[1] * luck for t in traj], color=color, ls=":", lw=1)
    axes[2].set_xlabel("beats (60% roll a check; rest every 6)"); axes[2].set_ylabel("expected tokens (solid)")
    axes[2].set_title("Pool over a session; dotted = P(pool <= 1) x Luck"); axes[2].legend(fontsize=7)
    savefig("08_luck_economy")

    rows = []
    for luck in (6, 8, 10, 12):
        for thr in (2, 3):
            traj = luck_pool_trajectory_exact(luck, 12, thr, 16, roll_prob=0.6, rest_every=6)
            rows.append([str(luck), str(thr), f(traj[7][0]), pct(traj[7][1]), f(traj[15][0]), pct(traj[15][1])])
    table("Luck pool after 8 and 16 beats (attribute 12, 60% of beats roll, rest every 6 beats)",
          ["Luck", "rescue deficit <=", "E[tokens] @8", "P(<=1) @8", "E[tokens] @16", "P(<=1) @16"], rows)

    # opposed test luck timing (informed vs blind), attacker 12 vs 12, budget 3
    d_dist = die_dist()
    base = p_attacker_wins(12, 12)
    p_inf, cost_inf = Fraction(0), Fraction(0)
    for a in range(1, DIE + 1):
        for d, pd in d_dist.items():
            p = Fraction(1, DIE) * pd
            d_ok = is_success(d, 12); md = 12 - d
            for spend in range(0, 4):
                a_eff = a if a in (1, DIE) else a - spend
                if a_eff < 1:
                    break
                a_ok = is_success(a_eff, 12); ma = 12 - a_eff
                if (a_ok and not d_ok) or (a_ok and d_ok and ma > md):
                    p_inf += p; cost_inf += p * spend
                    break
    table("Luck in opposed tests (12 vs 12, up to 3 tokens, both dice read first as the rules say)",
          ["policy", "attacker wins", "tokens per exchange", "pp per token"],
          [["no spending", pct(base), "0", "-"], ["spend to win when affordable", pct(p_inf), f(cost_inf, 3), f((p_inf - base) / cost_inf * 100, 1)]])


# ---------------------------------------------------------------------------
# 7. Creation economy and powerbuilding
# ---------------------------------------------------------------------------
def legal_builds(budget: int):
    out = []
    for attrs in product(range(6, 17), repeat=5):
        c_attr = sum(2 * (a - 10) if a >= 10 else (a - 10) for a in attrs)
        for stm in range(3, 10):
            c = c_attr + (2 * (stm - 5) if stm >= 5 else (stm - 5))
            if c == budget:
                out.append((attrs, stm))
    return out


def section_builds() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    rows = []
    for budget, color in ((0, "C3"), (6, "C0"), (12, "C1"), (16, "C2")):
        builds = legal_builds(budget)
        tops = [max(b[0]) for b in builds]
        counts = [tops.count(v) / len(tops) * 100 for v in SCORES]
        axes[0].plot(SCORES, counts, marker="o", ms=3, color=color, label=f"{budget} points ({len(builds):,} builds)")
        n16 = sum(1 for t in tops if t == 16)
        rows.append([str(budget), f"{len(builds):,}", f"{sum(tops)/len(tops):.2f}", f"{n16:,}", pct(n16 / len(builds))])
    axes[0].set_xlabel("highest attribute in the build"); axes[0].set_ylabel("% of legal builds"); axes[0].set_title("Where the legal builds sit, by budget")
    axes[0].legend(fontsize=7)
    table("Legal builds by budget (exact score cost; no tags)", ["budget", "legal builds", "mean top attribute", "builds with a 16", "share with a 16"], rows)

    # tag vs +1: break-even niche rolls per session
    rows = []
    for a in SCORES:
        gain = float(p_success(a, "advantage") - p_success(a)) * 100
        rows.append([str(a), f"{gain:.1f}", f"{gain / 5:.1f}"])
        axes[1].bar(a, gain / 5, color="C0")
    axes[1].axhline(1, color="k", ls="--", lw=0.8)
    axes[1].set_xlabel("attribute the tag would apply to"); axes[1].set_ylabel("stat rolls per niche roll at parity")
    axes[1].set_title("Tag (Advantage in a niche) vs +1 to the stat: break-even ratio")
    savefig("09_builds_and_tags")
    table("Tag vs +1 attribute at equal cost (2 build points)", ["attr", "Advantage gain (pp) per niche roll", "stat rolls one niche roll is worth"], rows)

    # effective competence for archetypes under steerability
    rows = []
    archetypes = {
        "flat": ([11, 11, 11, 10, 10], 5),
        "signature 12": ([12, 11, 10, 10, 10], 5),
        "spike 14, dump STM": ([14, 10, 10, 10, 10], 3),
        "spike 16, dump Luck+STM": ([16, 10, 10, 10, 6], 3),
        "spike 16, dump three": ([16, 8, 8, 8, 10], 5),
    }
    for name, (attrs, stm) in archetypes.items():
        assert build_cost(attrs, stm) == 6, (name, build_cost(attrs, stm))
        row = [name, f"{attrs} STM {stm}"]
        for steer in (0.2, 0.4, 0.6):
            best = max(attrs); others = [x for x in attrs if x != best] or [best]
            eff = steer * float(p_success(best)) + (1 - steer) * sum(float(p_success(x)) for x in others) / len(others)
            row.append(pct(eff))
        row.append(f(expected_exchanges_to_drop(stm, 12, 10, 1, 1)))
        rows.append(row)
    table("Archetypes at 6 points: effective success when 20/40/60% of rolls use the best stat; exchanges an Elite needs to drop them",
          ["build", "scores", "20%", "40%", "60%", "Elite drops in"], rows)


# ---------------------------------------------------------------------------
# 8. Advancement
# ---------------------------------------------------------------------------
def section_advancement() -> None:
    # Grak-like start: MGT 12, others 10, STM 7, Luck 8, spend +2/milestone on MGT to 16, then STM to 9, then second stat
    milestones = list(range(0, 13))
    mgt, second, stm = 12, 10, 7
    rows = []; ttk_e = []; ttk_n = []; p_prim = []
    for k in milestones:
        rows.append([str(k), str(mgt), str(second), str(stm), pct(p_success(mgt)),
                     f(expected_exchanges_to_drop(5, mgt, 10, 1, 1)), f(expected_exchanges_to_drop(7, mgt, 14, 1, 3)),
                     f(expected_exchanges_to_drop(stm, 16, 10, 2, 1))])
        ttk_e.append(float(expected_exchanges_to_drop(5, mgt, 10, 1, 1)))
        ttk_n.append(float(expected_exchanges_to_drop(7, mgt, 14, 1, 3)))
        p_prim.append(float(p_success(mgt)) * 100)
        # spend 2 points
        if mgt < 16:
            mgt += 1
        elif stm < 9:
            stm += 1
        elif second < 16:
            second += 1
    table("Advancement path: +2 points per milestone on the signature stat, then Stamina, then a second stat",
          ["milestones", "MGT", "2nd", "STM", "P(MGT test)", "drops Elite in", "drops Nemesis in", "Nemesis drops PC in"], rows)
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.plot(milestones, ttk_e, marker="o", ms=3, label="exchanges to drop an Elite")
    ax.plot(milestones, ttk_n, marker="s", ms=3, label="exchanges to drop a Nemesis")
    ax.set_xlabel("milestones (each +2 build points; roughly every 3-4 perilous beats)"); ax.set_ylabel("exchanges")
    ax.axvline(4, color="grey", ls="--", lw=0.8); ax.text(4.1, max(ttk_n) * 0.9, "signature stat hits 16", fontsize=8)
    ax.set_title("Power curve under advancement (PC edge +1)"); ax.legend(fontsize=8)
    savefig("10_advancement")


# ---------------------------------------------------------------------------
# 9. Pressure fuse
# ---------------------------------------------------------------------------
def pressure_chain(p_tick: float, beats: int, tax_at_4: float = 0.0):
    """Distribution of beats until the fuse first hits 5, with an optional extra
    per-beat tick probability once at step 4 (the 'risky test costs +1' tax)."""
    state = {0: 1.0}
    first_hit = []
    crises_expected = 0.0
    for b in range(1, beats + 1):
        nxt: dict[int, float] = {}
        hit = 0.0
        for s, p in state.items():
            q = p_tick + (tax_at_4 if s == 4 else 0.0)
            q = min(q, 1.0)
            if s + 1 >= 5:
                hit += p * q
                nxt[0] = nxt.get(0, 0.0) + p * q  # crisis then reset
            else:
                nxt[s + 1] = nxt.get(s + 1, 0.0) + p * q
            nxt[s] = nxt.get(s, 0.0) + p * (1 - q)
        crises_expected += hit
        first_hit.append(hit)
        state = nxt
    return first_hit, crises_expected


def section_pressure() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    rows = []
    for p in (0.15, 0.25, 0.35, 0.5):
        hits, crises = pressure_chain(p, 40)
        # first-crisis distribution: use fresh chain without reset accounting -> approximate via negative binomial
        # exact first-passage: probability that the 5th tick lands on beat b
        from math import comb
        fp = [comb(b - 1, 4) * p ** 5 * (1 - p) ** (b - 5) if b >= 5 else 0 for b in range(1, 41)]
        axes[0].plot(range(1, 41), [v * 100 for v in fp], label=f"p(tick)={p}")
        mean = 5 / p
        cum = 0; p10 = p90 = None
        for b, v in enumerate(fp, start=1):
            cum += v
            if p10 is None and cum >= 0.10: p10 = b
            if p90 is None and cum >= 0.90: p90 = b
        _, crises20 = pressure_chain(p, 20)
        _, crises20_tax = pressure_chain(p, 20, tax_at_4=0.3)
        rows.append([str(p), f"{mean:.1f}", str(p10), str(p90), f"{crises20:.2f}", f"{crises20_tax:.2f}"])
    axes[0].set_xlabel("beat of first crisis"); axes[0].set_ylabel("%"); axes[0].set_title("When the fuse first blows (5 ticks from 0)")
    axes[0].legend(fontsize=8)
    for p in (0.15, 0.25, 0.35, 0.5):
        _, c = zip(*[(0, pressure_chain(p, b)[1]) for b in range(1, 41)])
        axes[1].plot(range(1, 41), c, label=f"p(tick)={p}")
    axes[1].set_xlabel("beats"); axes[1].set_ylabel("expected crises so far"); axes[1].set_title("Crises accumulate (fuse resets to 0)")
    axes[1].legend(fontsize=8)
    savefig("11_pressure_fuse")
    table("Pressure fuse: beats to first crisis and crises per 20-beat session (tax = +30% tick chance while at 4)",
          ["P(+1 per beat)", "mean beats to crisis", "10th pct", "90th pct", "crises / 20 beats", "with step-4 tax"], rows)


# ---------------------------------------------------------------------------
# 10. Skin modules that add procedures
# ---------------------------------------------------------------------------
def section_skins() -> None:
    rows = []
    for a in (10, 12, 14, 16):
        ps = float(p_success(a))
        # Candlelight spell tiers: Spell costs 1 coin or +1 Fatigue on success, +1 Fatigue on failure -> E[Fatigue] if paying with Fatigue
        rows.append([str(a), pct(ps), "1.00", f"{ps * 1 + (1 - ps) * 2:.2f}", f"2.00, plus backlash and a crisis roll on failure ({pct(1 - ps)})"])
    table("Candlelight spellcraft, paying every cost with Fatigue: expected Fatigue per cast", ["LOR/FTH", "P(success)", "Spell", "Greater Spell", "Arcanum"], rows)

    rows = []
    for soak in range(4):
        defl = 10 + 2 * soak
        rows.append([str(soak), str(defl), pct(1 - p_success(defl))])
    table("Twilight injurious blows: P(Injured) on a Deflection test of 10 + 2 x soak", ["soak", "Deflection", "P(Injured)"], rows)

    rows = []
    for edu in (8, 10, 12, 14):
        pf = 1 - float(p_success(edu))
        rows.append([str(edu), pct(pf), f"{pf * 2:.2f}", "5.0%", f"{pf:.2f}"])
    table("Free Traders jump leg with one crew member filling both Astrogator and Engineer roles",
          ["EDU", "P(fail a role)", "E[Strain] per jump", "P(misjump) (natural 20)", "E[Hull ticks] per jump"], rows)

    # Fatal tag reach: how often does a tier land a hit at all (that is the Fatal trigger rate)
    rows = []
    for name, score, stm, edge, soak in TIERS:
        rows.append([name, pct(p_attacker_wins(score, 10)), pct(p_attacker_wins(score, 10, "straight", "advantage"))])
    table("Fatal tag: chance per exchange that a tier lands the hit at all (defender 10 / defender with Advantage)", ["tier", "P(hit)", "P(hit) vs Adv defence"], rows)


# ---------------------------------------------------------------------------
# 11. Cliff scan: every discrete threshold in the engine
# ---------------------------------------------------------------------------
def section_cliffs() -> None:
    rows = [
        ["d20 granularity", "every attribute point", "5 pp of success", "inherent to the die; smooth"],
        ["natural 1 / 20", "5% each, at every attribute", "auto-success / auto-fail", "floor at attribute <= 1 and ceiling at >= 19 are outside the 6-16 range"],
        ["Advantage value", "peaks at attribute 10", f"{f((p_success(10,'advantage')-p_success(10))*100,1)} pp; only {f((p_success(16,'advantage')-p_success(16))*100,1)} pp at 16", "Advantage is worth 5 stat points at 10 and 3 at 16"],
        ["margin bonus +1", "margin 5; needs attribute >= 7", f"{pct(sum(p for m,p in margin_dist_on_success(7).items() if margin_bonus(m)>=1))} of hits at 7, {pct(sum(p for m,p in margin_dist_on_success(16).items() if margin_bonus(m)>=1))} at 16", "first step reachable by almost every PC"],
        ["margin bonus +2", "margin 10; needs attribute >= 12", f"{pct(sum(p for m,p in margin_dist_on_success(12).items() if margin_bonus(m)>=2))} of hits at 12, {pct(sum(p for m,p in margin_dist_on_success(16).items() if margin_bonus(m)>=2))} at 16", "a real step for 11 -> 12, worth +1 damage on 1 in 12 hits"],
        ["margin bonus +3", "margin 15; needs attribute 17", "unreachable", "the 16 ceiling caps ordinary hits at +2"],
        ["damage floor", "soak >= 1 + edge + bonus", "mail = plate against weak blows", f"Peasant fist: soak 1, 2, 3 all leave {f(expected_damage(8,10,0,2),3)} per exchange"],
        ["defender wins ties and double failures", "all opposed tests", f"attacker {pct(p_attacker_wins(10,10))} at 10 v 10, {pct(p_attacker_wins(6,6))} at 6 v 6", "stated design choice; steepest at low scores"],
        ["Luck test", "roll <= current tokens", "each token spent = -5 pp on later Luck tests", "smooth, but pool 0-1 both give 5% (natural 1 only)"],
        ["attribute ceiling 16", "lifetime", "P(success) caps at 80%", "advancement then spreads sideways"],
        ["Stamina ceiling 9", "lifetime", "an Elite needs ~1.8x the exchanges vs STM 5", "see advancement table"],
        ["tag price", "2 points flat", "worth more when the stat is low", "see tag parity table: parity at ~5 stat rolls per niche roll at 10, ~3 at 16"],
    ]
    table("Cliff scan: every discrete threshold, where it sits, how big it is", ["threshold", "where", "size", "note"], rows)


def main() -> None:
    section_success()
    section_margin()
    section_opposed()
    section_damage()
    section_ttk()
    section_luck()
    section_builds()
    section_advancement()
    section_pressure()
    section_skins()
    section_cliffs()
    (OUT / "tables.md").write_text(
        "# Engine atlas: data tables\n\nGenerated by `tools/analysis/atlas.py`. Exact enumeration unless a table says otherwise.\n\n"
        + "\n".join(TABLES),
        encoding="utf-8",
    )
    print(f"ok: wrote {len(list(FIG.glob('*.png')))} figures and tables.md to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
