"""Independent exact/economic stress tests, derived from the authored rules.

Historical pre-cap creation economy. Rerunning reproduces the uncapped
baseline, not the 1 October 2026 eight-point refund cap. See README.md.

Run: uv run --extra analysis python tools/analysis/independent_economy.py
No imports from the earlier analysis or live harness. Figures need matplotlib;
enumeration uses numpy to keep the full labelled creation space inexpensive.
"""
from __future__ import annotations

import csv
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[2] / "docs" / "independent_engine"


def succeeds(raw: int, final: int, target: int) -> bool:
    return raw == 1 or (raw != 20 and final <= target)


def attack_wins(a: int, d: int, attack: int, defence: int,
                afinal: int | None = None, dfinal: int | None = None) -> bool:
    af, df = a if afinal is None else afinal, d if dfinal is None else dfinal
    aw, dw = succeeds(a, af, attack), succeeds(d, df, defence)
    return aw and (not dw or attack - af > defence - df)


def faces(mode: str = "straight") -> dict[int, F]:
    if mode == "straight":
        return {r: F(1, 20) for r in range(1, 21)}
    counts = dict.fromkeys(range(1, 21), 0)
    choose = min if mode == "adv" else max
    for a, b in product(range(1, 21), repeat=2):
        counts[choose(a, b)] += 1
    return {r: F(n, 400) for r, n in counts.items()}


@lru_cache(None)
def exchange(attack: int, defence: int, edge: int, soak: int,
             amode: str = "straight", dmode: str = "straight") -> tuple[F, F, F]:
    hit = damage = critical_damage = F(0)
    for a, pa in faces(amode).items():
        for d, pd in faces(dmode).items():
            if attack_wins(a, d, attack, defence):
                raw_damage = 1 + edge + max(0, attack - a) // 5
                hurt = raw_damage + 1 if a == 1 else max(1, raw_damage - soak)
                hit += pa * pd
                damage += pa * pd * hurt
                critical_damage += pa * pd * hurt * (a == 1)
    return hit, damage, critical_damage


@lru_cache(None)
def min_flip_cost(a: int, d: int, attack: int, defence: int, role: str) -> int | None:
    """Cheapest post-roll change across both dice giving the player's side a win.

    Natural faces stay locked; reaching 1/20 by spending is not natural.
    Splitting can be necessary: a weak attacker may need both to succeed and
    to spoil a stronger defender's roll. Enumerate both adjusted faces.
    """
    desired = role == "attack"
    if attack_wins(a, d, attack, defence) == desired:
        return 0
    best = None
    afaces = (a,) if a in (1,20) else range(1,21)
    dfaces = (d,) if d in (1,20) else range(1,21)
    for af,df in product(afaces,dfaces):
        cost = abs(af-a)+abs(df-d)
        if (best is None or cost<best) and attack_wins(a,d,attack,defence,af,df)==desired:
            best = cost
    return best


@lru_cache(None)
def rescue_costs(kind: str, threshold: int = 3) -> dict[int, F]:
    costs: dict[int, F] = {}
    if kind == "check":
        for r in range(1, 21):
            deficit = r-12
            c = deficit if r != 20 and 0 < deficit <= threshold else 0
            costs[c] = costs.get(c, F(0)) + F(1, 20)
    else:
        for a, d in product(range(1, 21), repeat=2):
            c = min_flip_cost(a, d, 12, 12, kind)
            c = c if c is not None and c <= threshold else 0
            costs[c] = costs.get(c, F(0)) + F(1, 400)
    return costs


def luck_path(maximum: int, kind: str, beats: int = 32, activity: F = F(3, 5),
              rest: int = 6, milestone: int = 0, ability_cost: int = 0) -> list[tuple[float, float]]:
    """Finite pool, one possible roll per beat; costs paid before nudging.

    ability_cost is an additional sink on an active beat, paid if affordable.
    This measures pool depletion, not whether an unaffordable spell resolves.
    Rest/refill occur after a beat. Milestone is a deterministic interval here,
    deliberately varied rather than inferred from 'perilous' fiction.
    """
    state = {maximum: F(1)}
    trajectory = []
    costs = rescue_costs(kind)
    for beat in range(1, beats+1):
        nxt: dict[int, F] = {}
        for tokens, prob in state.items():
            nxt[tokens] = nxt.get(tokens, F(0)) + prob*(1-activity)
            for cost, chance in costs.items():
                after = tokens - ability_cost if tokens >= ability_cost else tokens
                remaining = after - cost if cost <= after else after
                nxt[remaining] = nxt.get(remaining, F(0)) + prob*activity*chance
        state = {}
        for tokens, prob in nxt.items():
            target = maximum if milestone and beat % milestone == 0 else min(maximum, tokens + int(bool(rest and beat % rest == 0)))
            state[target] = state.get(target, F(0)) + prob
        assert sum(state.values()) == 1
        trajectory.append((float(sum(t*p for t, p in state.items())),
                           float(sum(p for t, p in state.items() if t <= 1))))
    return trajectory


def pressure(beats: int, rate: F, purge: F = F(0), burst: int = 1) -> tuple[float, float]:
    """Specified toy pacing process: tick, resolve at 5/reset, then possible purge."""
    state = {(0, 0): F(1)}
    for _ in range(beats):
        nxt: dict[tuple[int, int], F] = {}
        for (level, crises), p in state.items():
            for tick, q in ((0, 1-rate), (burst, rate)):
                l, c = level+tick, crises
                if l >= 5:
                    l, c = 0, c+1
                for clear, r in ((0, 1-purge), (1, purge)):
                    key = max(0, l-clear), c
                    nxt[key] = nxt.get(key, F(0)) + p*q*r
        state = nxt
    assert sum(state.values()) == 1
    return float(sum(c*p for (_, c), p in state.items())), float(sum(p for (_, c), p in state.items() if c >= 1))


def table(path: str, rows: list[dict]) -> None:
    with (OUT/path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def creation() -> tuple[list[dict], list[dict]]:
    # Labelled five attributes: do not collapse permutations of roles.
    attrs = np.array(list(product(range(6, 17), repeat=5)), dtype=np.int16)
    score_cost = np.where(attrs >= 10, 2*(attrs-10), attrs-10).sum(axis=1)
    counts, extrema = [], []
    for budget in (0, 6, 12, 16):
        for tags in (0, 1, 2, 3):
            legal_count = peak_health = 0
            for stm in range(3, 10):
                cost = max(0, 2*(stm-5)) if stm >= 5 else stm-5
                valid = np.maximum(0, score_cost+cost)+2*tags <= budget
                legal_count += int(valid.sum())
                if stm == 9:
                    peak_health += int((valid & (attrs[:, 0] == 16)).sum())
            counts.append(dict(budget=budget,tags=tags,labelled_legal_builds=legal_count,
                               attack16_stamina9=peak_health))
    # An explicit utility family: signature share s; remaining four equal shares.
    # We preserve STM>=5 and Luck>=8: changes in those two resources are not priced
    # as if their only benefit were an ordinary test.
    budget = 6
    for stm in (5, 7, 9):
        for tags in (0, 1):
            valid = (np.maximum(0, score_cost+2*(stm-5))+2*tags <= budget) & (attrs[:, 4] >= 8)
            options = attrs[valid]
            for share in (0.2, 0.4, 0.6, 0.8):
                for niche in (0.0, 0.25, 0.5, 1.0):
                    p = options/20
                    signature = p[:, 0]+tags*niche*p[:, 0]*(1-p[:, 0])
                    utility = share*signature+(1-share)*p[:, 1:].mean(axis=1)
                    i = int(np.argmax(utility))
                    extrema.append(dict(stamina=stm,tags=tags,signature_share=share,niche_coverage=niche,
                                        scores="/".join(map(str,options[i])),mean_success=float(utility[i])))
    return counts, extrema


def controls() -> None:
    for score in range(6, 17):
        p = F(score,20)
        for mode, expected in (("straight",p),("adv",1-(1-p)**2),("dis",p*p)):
            assert sum(prob for r,prob in faces(mode).items() if succeeds(r,r,score)) == expected
    assert succeeds(1,1,0) and not succeeds(20,20,25)
    assert not attack_wins(5,5,10,10)
    assert not attack_wins(19,18,10,10)
    assert exchange(12,12,1,3)[1] < exchange(12,12,1,2)[1]
    # Baseline independent table value, 400 equiprobable opposed cells.
    assert exchange(10,10,1,0)[0] == F(145,400)
    assert exchange(16,16,1,0)[0] == F(184,400)
    assert min_flip_cost(7,2,6,16,"attack") == 16
    # Independently enumerate bounded signed moves to check the unrestricted
    # search for every equal-12 roll pair and both goals, budget up to 3.
    for a,d in product(range(1,21),repeat=2):
        for role in ("attack","defence"):
            cost = min_flip_cost(a,d,12,12,role)
            split = None
            for da,dd in product(range(-3,4),repeat=2):
                if abs(da)+abs(dd)>3 or not 1<=a+da<=20 or not 1<=d+dd<=20:
                    continue
                if (da and a in (1,20)) or (dd and d in (1,20)):
                    continue
                if attack_wins(a,d,12,12,a+da,d+dd)==(role=="attack"):
                    c=abs(da)+abs(dd)
                    split=c if split is None else min(split,c)
            assert (cost if cost is not None and cost<=3 else None)==split


def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    controls()
    counts, extrema = creation()
    table("creation_counts.csv",counts)
    table("creation_frontier.csv",extrema)
    outcomes=[]
    for a,d,e,s in product(range(6,17),range(6,17),range(3),range(4)):
        h,damage,critical=exchange(a,d,e,s)
        outcomes.append(dict(attack=a,defence=d,edge=e,soak=s,hit=float(h),
                             damage=float(damage),critical_damage=float(critical),
                             critical_share=float(critical/damage)))
    table("resolution_grid.csv",outcomes)
    nudge=[]
    for a,d,role in product((6,10,12,16),(6,10,12,16),("attack","defence")):
        costs=[min_flip_cost(x,y,a,d,role) for x,y in product(range(1,21),repeat=2)]
        for cap in (0,1,2,3,6):
            wins=sum(c is not None and c<=cap for c in costs)/400
            spend=sum(c for c in costs if c is not None and c<=cap)/400
            nudge.append(dict(attack=a,defence=d,role=role,cap=cap,win=wins,mean_spend=spend))
    table("informed_nudges.csv",nudge)
    luck=[]
    for maximum,kind,rest,milestone,ability in product((6,8,12),("check","attack","defence"),(0,6),(0,4,8),(0,1)):
        path=luck_path(maximum,kind,rest=rest,milestone=milestone,ability_cost=ability)
        luck.append(dict(maximum=maximum,kind=kind,rest=rest,milestone=milestone,ability_cost=ability,
                         tokens16=path[15][0],low16=path[15][1],tokens32=path[31][0],low32=path[31][1],
                         mean_low=float(np.mean([x[1] for x in path])),
                         min_expected=min(x[0] for x in path)))
    table("luck_sensitivity.csv",luck)
    pacing=[]
    for beats,rate,purge,burst in product((12,20,32),(F(1,5),F(1,3),F(1,2)),(F(0),F(1,10)),(1,2)):
        crises,any_crisis=pressure(beats,rate,purge,burst)
        pacing.append(dict(beats=beats,tick=float(rate),purge=float(purge),burst=burst,
                           expected_crises=crises,p_any=any_crisis))
    table("pressure_sensitivity.csv",pacing)
    fig,axs=plt.subplots(2,2,figsize=(11,8),layout="constrained")
    for soak in range(4):
        axs[0,0].plot(range(6,17),[float(exchange(a,10,1,soak)[1]) for a in range(6,17)],label=f"soak {soak}")
    axs[0,0].set(title="Blade vs defence 10",xlabel="Attack attribute",ylabel="Expected damage / attack")
    axs[0,0].legend()
    for kind,ability,label in (("check",0,"Checks"),("attack",0,"Opposed attacks"),("attack",1,"Opposed + 1 token cost")):
        path=luck_path(8,kind,ability_cost=ability)
        axs[0,1].plot(range(1,33),[x[0] for x in path],label=label)
    axs[0,1].set(title="Luck 8; 60% active beats; rest every 6; no refill",xlabel="Beat",ylabel="Expected remaining tokens")
    axs[0,1].legend(fontsize=8)
    for stm in (5,7,9):
        rows=[r for r in extrema if r['stamina']==stm and r['tags']==0 and r['niche_coverage']==0]
        axs[1,0].plot([r['signature_share'] for r in rows],[r['mean_success'] for r in rows],marker='o',label=f"STM {stm}")
    axs[1,0].set(title="Best 6-point build; Luck ≥8; no tags",xlabel="Share of checks using signature stat",ylabel="Mean success (other four equally frequent)")
    axs[1,0].legend()
    for burst,purge,label in ((1,F(0),"Single ticks"),(1,F(1,10),"Single ticks, 10% purge"),(2,F(0),"Double ticks")):
        values=[pressure(b,F(1,3),purge,burst)[0] for b in (12,20,32)]
        axs[1,1].plot((12,20,32),values,marker='o',label=label)
    axs[1,1].set(title="Pressure event on one beat in three",xlabel="Session beats",ylabel="Expected crises")
    axs[1,1].legend(fontsize=8)
    fig.savefig(OUT/"economy.png",dpi=160)
    plt.close(fig)
    summary={'controls':'passed','labelled_space':11**5*7,'resolution_cells':len(outcomes),
             'creation_counts':counts,'luck_cases':len(luck),'pacing_cases':len(pacing),
             'rule_of_thumb':'Conditional means and hypothetical utility functions are not playtest win rates.'}
    (OUT/'economy_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='creation_counts'},indent=2))


if __name__=='__main__':
    main()
