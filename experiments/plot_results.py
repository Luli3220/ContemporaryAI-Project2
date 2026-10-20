"""All figures are regenerated from persisted CSV/JSON, no hand-entered results."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .metrics import read_csv
from .cases import WEIGHTED

COLORS = {'zero':'#718096', 'manhattan':'#176b87', 'adjusted':'#176b87',
          'minimax':'#718096', 'original':'#176b87', 'reverse':'#d38b32', 'heuristic':'#a74365'}


def plot_all(root):
    out = root / 'figures'
    out.mkdir(parents=True, exist_ok=True)
    data = read_csv(root / 'tables' / 'summary.csv')
    cases = read_csv(root / 'tables' / 'per_case.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False,
                         'axes.spines.right':False, 'figure.dpi':140, 'savefig.dpi':180})

    def save(fig, name):
        fig.savefig(out / (name + '.png'), bbox_inches='tight')
        fig.savefig(out / (name + '.svg'), bbox_inches='tight')
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for ax, density in zip(axes.flat, (0, .1, .2, .3)):
        for method in ('zero', 'manhattan'):
            rows = sorted([r for r in data if r['experiment']=='maze' and float(r['density'])==density
                and r['algorithm']==method and r['reachable']=='True'], key=lambda r:int(r['grid_size']))
            x = [int(r['grid_size']) for r in rows]
            y = [float(r['expanded_mean']) for r in rows]
            error = [[float(r['expanded_mean'])-float(r['expanded_ci_low']) for r in rows],
                     [float(r['expanded_ci_high'])-float(r['expanded_mean']) for r in rows]]
            ax.errorbar(x, y, yerr=error, marker='o', capsize=3, label=method, color=COLORS[method])
        ax.set(title=f'Obstacle probability = {density:.0%}', xlabel='Grid side length (cells)', ylabel='Expanded nodes')
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.18)
        ax.legend()
    fig.suptitle('Maze: reachable instances, seed-bootstrap 95% confidence intervals')
    save(fig, 'maze_scaling')

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, scenario in zip(axes, ('base','zero','obstacles')):
        for method in ('zero', 'adjusted'):
            rows = sorted([r for r in data if r['experiment']=='weighted' and r['scenario']==scenario
                and float(r['high_ratio'])==.4 and r['algorithm']==method and r['reachable']=='True'],
                key=lambda r:int(r['grid_size']))
            ax.errorbar([int(r['grid_size']) for r in rows], [float(r['expanded_mean']) for r in rows],
                yerr=[float(r['expanded_sd']) for r in rows], marker='o', capsize=3, label=method, color=COLORS[method])
        ax.set(title=scenario, xlabel='Grid side length (cells)', ylabel='Expanded nodes (mean +/- SD)')
        ax.set_ylim(bottom=0)
        ax.legend()
    fig.suptitle('Weighted routing: high-cost probability 40%, reachable instances')
    save(fig, 'weighted_scaling')

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, branch in zip(axes, (2,3,4)):
        for method in ('minimax','original','reverse','heuristic'):
            rows = sorted([r for r in data if r['experiment']=='tree' and int(r['branch'])==branch
                and r['algorithm']==method], key=lambda r:int(r['depth']))
            ax.errorbar([int(r['depth']) for r in rows], [float(r['visited_nodes_mean']) for r in rows],
                yerr=[float(r['visited_nodes_sd']) for r in rows], marker='o', capsize=3,
                color=COLORS[method], label=method)
        ax.set(title=f'Branching factor = {branch}', xlabel='Depth (plies)', ylabel='Visited nodes (mean +/- SD)')
        ax.set_ylim(bottom=0)
        ax.legend()
    fig.suptitle('Game trees: node ordering changes search work, not minimax value')
    save(fig, 'tree_scaling')

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for method in ('minimax','original','reverse','heuristic'):
        rows = sorted([r for r in cases if r['experiment']=='treasure' and r['algorithm']==method],
                      key=lambda r:int(r['depth']))
        x = [int(r['depth']) for r in rows]
        for ax, metric, label in zip(axes, ('visited_nodes','wall_ms'), ('Visited nodes','Median wall time (ms)')):
            ax.plot(x, [float(r[metric]) for r in rows], marker='o', color=COLORS[method], label=method)
            ax.set(xlabel='Horizon (treasure decisions)', ylabel=label, ylim=(0,None))
            ax.legend()
    # Setting a lower limit also freezes autoscaling; include every method explicitly.
    for ax in axes:
        ymax = max(max(line.get_ydata()) for line in ax.lines)
        ax.set_ylim(0, ymax * 1.12)
    fig.suptitle('Treasure game: search only, routing precomputation excluded')
    save(fig, 'treasure_search')

    roots = read_csv(root / 'raw' / 'root_actions.csv')
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    x = np.arange(4)
    for depth, offset, color in ((2,-.18,'#176b87'), (4,.18,'#a74365')):
        rows = [r for r in roots if int(r['depth']) == depth]
        vals = [float(r['value']) for r in rows]
        bars = ax.bar(x+offset, vals, width=.35, label=f'H={depth}', color=color)
        ax.bar_label(bars, padding=3)
    ax.set_xticks(x, ['T1','T2','T3','T4'])
    ax.set(xlabel='A first treasure', ylabel='Minimax utility (Score A - Score B)',
           title='Exact root-action values under optimal opposition')
    ax.axhline(0, color='#222', linewidth=.6)
    ax.margins(y=.18)
    ax.legend()
    save(fig, 'root_actions')

    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    for depth, color in ((2,'#176b87'),(4,'#a74365')):
        rows = sorted([r for r in cases if r['experiment']=='sensitivity' and int(r['depth'])==depth
            and r['algorithm']=='original'], key=lambda r:int(r['t1_value']))
        ax.plot([int(r['t1_value']) for r in rows], [float(r['optimal_cost']) for r in rows],
                marker='o', color=color, label=f'H={depth}')
        for r in rows:
            ax.annotate(r['best_target'], (int(r['t1_value']), float(r['optimal_cost'])),
                        xytext=(0,-16 if depth==4 else 10), textcoords='offset points', ha='center', fontsize=8)
    ax.set(xlabel='T1 value (other parameters fixed)', ylabel='Optimal utility',
           title='Sensitivity: depth and treasure value interact')
    ax.set_xticks(range(0,19,2))
    ax.margins(y=.23)
    ax.legend()
    save(fig, 'sensitivity')

    # Weighted official path loaded from recorded results; add the full numeric cost per cell.
    official = json.loads((root / 'raw' / 'official.json').read_text(encoding='utf-8'))
    path = official['weighted_path']
    costs = np.array([[0 if isinstance(v,str) else v for v in row] for row in WEIGHTED])
    fig, ax = plt.subplots(figsize=(6, 5), constrained_layout=True)
    heat = ax.imshow(costs, cmap='YlGnBu', vmin=0, vmax=8)
    for r, row in enumerate(WEIGHTED):
        for c, value in enumerate(row):
            ax.text(c, r, str(value), ha='center', va='center', color='white' if costs[r,c]>=6 else '#18222b')
    ax.plot([p[1] for p in path], [p[0] for p in path], color='#db5551', linewidth=2.5, marker='o', alpha=.8)
    ax.set(xlabel='Column', ylabel='Row', title='Official weighted example: seven paid cells, then free E')
    fig.colorbar(heat, ax=ax, label='Entry cost')
    save(fig, 'weighted_path')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'results'
    plot_all(root / 'quick' if args.quick else root)
