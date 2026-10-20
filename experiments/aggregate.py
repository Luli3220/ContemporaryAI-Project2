"""Per-instance medians; independent-seed bootstrap (never timing repeats as n)."""
from collections import defaultdict
import random
from statistics import mean, median, stdev
from .metrics import read_csv, write_csv

METRICS = ['expanded', 'generated', 'popped', 'stale_pops', 'max_frontier',
           'visited_nodes', 'evaluated_leaves', 'cutoff_events', 'pruned_siblings',
           'ordering_probes', 'runtime_ms', 'wall_ms', 'optimal_cost', 'path_steps']
CONFIG = ['experiment', 'grid_size', 'density', 'scenario', 'high_ratio', 'branch',
          'depth', 't1_value', 'algorithm', 'reachable']


def bootstrap_ci(values):
    if len(values) == 1 or min(values) == max(values):
        return mean(values), mean(values)
    rng = random.Random(20261019)
    means = sorted(mean(rng.choices(values, k=len(values))) for _ in range(1000))
    return means[24], means[974]


def aggregate(root):
    all_rows, case_rows, summaries = [], [], []
    for name in ('maze', 'weighted', 'tree', 'treasure', 'sensitivity'):
        all_rows.extend(read_csv(root / 'raw' / f'{name}.csv'))
    groups = defaultdict(list)
    for row in all_rows:
        groups[(row['case_id'], row['algorithm'])].append(row)
    for rows in groups.values():
        case = {k: rows[0].get(k, '') for k in CONFIG + ['case_id', 'seed', 'best_target']}
        case['repeats'] = len(rows)
        for metric in METRICS:
            values = [float(r[metric]) for r in rows if r.get(metric, '') != '']
            case[metric] = median(values) if values else ''
        case_rows.append(case)
    grouped = defaultdict(list)
    for case in case_rows:
        grouped[tuple(case.get(k, '') for k in CONFIG)].append(case)
    for key, cases in grouped.items():
        summary = dict(zip(CONFIG, key))
        summary['instances'] = len(cases)
        for metric in METRICS:
            values = [c[metric] for c in cases if c[metric] != '' and abs(c[metric]) != float('inf')]
            if not values:
                continue
            summary[metric + '_mean'] = mean(values)
            summary[metric + '_sd'] = stdev(values) if len(values) > 1 else 0
        # CIs on main counters and wall time only, preserving paired case population.
        for metric in ('expanded', 'visited_nodes', 'wall_ms'):
            values = [c[metric] for c in cases if c[metric] != '']
            if values:
                lo, hi = bootstrap_ci(values)
                summary[metric + '_ci_low'], summary[metric + '_ci_high'] = lo, hi
        summaries.append(summary)
    write_csv(root / 'tables' / 'per_case.csv', case_rows)
    write_csv(root / 'tables' / 'summary.csv', summaries)
    # Paired reductions computed per seed, then bootstrap those seed-level differences.
    pairs = []
    for base in case_rows:
        exp = base['experiment']
        baseline = 'zero' if exp in ('maze', 'weighted') else 'minimax'
        metric = 'expanded' if exp in ('maze', 'weighted') else 'visited_nodes'
        if base['algorithm'] != baseline or exp == 'sensitivity':
            continue
        for candidate in case_rows:
            if candidate['case_id'] != base['case_id'] or candidate['algorithm'] == baseline:
                continue
            pairs.append({**{k: candidate.get(k, '') for k in CONFIG + ['case_id', 'seed']},
                'metric': metric, 'baseline_nodes': base[metric], 'candidate_nodes': candidate[metric],
                'reduction': (base[metric]-candidate[metric])/base[metric] if base[metric] else 0,
                'wall_ratio': candidate['wall_ms']/base['wall_ms']})
    write_csv(root / 'tables' / 'paired.csv', pairs)
    grouped_pairs = defaultdict(list)
    for pair in pairs:
        grouped_pairs[tuple(pair.get(k, '') for k in CONFIG)].append(pair)
    paired_summary = []
    for key, rows in grouped_pairs.items():
        reductions = [r['reduction'] for r in rows]
        lo, hi = bootstrap_ci(reductions)
        paired_summary.append({**dict(zip(CONFIG, key)), 'instances': len(rows),
            'reduction_mean': mean(reductions), 'reduction_ci_low': lo, 'reduction_ci_high': hi,
            'wall_ratio_median': median(r['wall_ratio'] for r in rows)})
    write_csv(root / 'tables' / 'paired_summary.csv', paired_summary)
    return case_rows, summaries
