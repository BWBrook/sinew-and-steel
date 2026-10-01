"""Render the saved independent results; performs no new simulation."""
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2] / "docs" / "independent_engine"


def main():
    rows = {r['scenario']: r for r in csv.DictReader((ROOT/'combat_results.csv').open())
            if r['section'] == 'simulation'}
    fig, axes = plt.subplots(2,2,figsize=(11,8),layout='constrained')
    tiers = ['peasant','soldier','elite','monster','nemesis']
    for build, label in [('balanced_dual','Balanced 12/12, STM 7'),
                         ('minmax_dual','Extreme 16/16, STM 9'),
                         ('floor8_dual','Restricted build: 16/16, STM 6, Hope 8')]:
        rr = [rows[f'duel_{build}_vs_{t}'] for t in tiers]
        y = np.array([float(r['p_pc_win'])*100 for r in rr])
        low = y-np.array([float(r['p_pc_win_ci_low'])*100 for r in rr])
        high = np.array([float(r['p_pc_win_ci_high'])*100 for r in rr])-y
        assert min(low.min(), high.min()) > -1e-10  # Wilson rounding at p=1
        low, high = np.maximum(0,low), np.maximum(0,high)
        axes[0,0].errorbar(range(5),y,yerr=[low,high],marker='o',capsize=3,label=label)
    axes[0,0].set(xticks=range(5),xticklabels=[x.title() for x in tiers],
                  title='Core duels: matched attribute reuse; Luck cap 2',ylabel='PC victory (%)',ylim=(0,103))
    axes[0,0].legend(fontsize=8,loc='lower left')
    for build,label in [('balanced_dual','Balanced 12/12, STM 7'),('minmax_dual','Extreme 16/16, STM 9')]:
        rr = [rows[f'hope_cap{cap}_{build}_vs_nemesis'] if cap!=2 else rows[f'duel_{build}_vs_nemesis'] for cap in (0,2,4,8)]
        axes[0,1].plot((0,2,4,8),[100*float(r['p_pc_win']) for r in rr],marker='o',label=label)
    axes[0,1].set(title='Nemesis duel: spending-policy sensitivity',xlabel='Maximum Luck spend per decision',ylabel='PC victory (%)',ylim=(0,103),xticks=(0,2,4,8))
    axes[0,1].legend(fontsize=8)
    stances=['vanguard','steady','watchful']
    rr=[rows[f'halvar_{s}_vs_monster_hope0'] for s in stances]
    for key,label in [('p_pc_win','Win the fight'),('p_hold_survival','Stand through 3 rounds')]:
        axes[1,0].plot(range(3),[100*float(r[key]) for r in rr],marker='o',label=label)
    axes[1,0].set(xticks=range(3),xticklabels=[s.title() for s in stances],ylim=(0,103),
                  title='Twilight: Halvar vs Monster; no Hope',ylabel='Probability (%)')
    axes[1,0].legend(fontsize=8)
    for i,(name,label) in enumerate([('skins_baseline.json','Before'),('skins_revised.json','Revised')]):
        d=json.loads((ROOT/name).read_text())['delvekit']['tiny/soft']
        axes[1,1].bar(np.arange(2)+(i-.5)*.3,[100*d['feature_rates'][x] for x in ('trap','solo')],width=.3,label=label)
    axes[1,1].axhline(25,color='grey',linestyle='--',label='Configured 25% chance')
    axes[1,1].set(xticks=(0,1),xticklabels=('Trap room','Roaming monster'),ylim=(0,65),
                  title='Tiny Soft delves: 1,000 matched seeds',ylabel='Sites containing feature (%)')
    axes[1,1].legend(fontsize=8)
    fig.savefig(ROOT/'combat_and_repairs.png',dpi=160)
    plt.close(fig)


if __name__=='__main__':
    main()
