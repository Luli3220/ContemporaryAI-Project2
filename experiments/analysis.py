"""Factorial contrasts and paired, round-level timing uncertainty from saved CSV."""
from collections import defaultdict
import hashlib
from statistics import mean, median
import numpy as np
from .aggregate import bootstrap_ci
from .metrics import read_csv, write_csv

TIMING_RESAMPLES = 5000
BLOCK_LENGTH = 3
PAIRS = (('original', 'reverse'), ('original', 'heuristic'), ('reverse', 'heuristic'))
ABLATION_METRICS = ('expanded', 'generated', 'max_frontier', 'wall_ms')


def ablation_tables(cases, summary):
    selected = [r for r in cases if r['experiment'] == 'maze_ablation']
    grouped = defaultdict(dict)
    for row in selected:
        grouped[row['case_id']][row['algorithm']] = row
    contrasts = []
    for methods in grouped.values():
        comparisons = [
            ('heuristic_at_f_h_fifo', 'zero__f_h_fifo', 'manhattan__f_h_fifo'),
            ('heuristic_at_f_fifo', 'zero__f_fifo', 'manhattan__f_fifo'),
            ('tie_at_zero', 'zero__f_fifo', 'zero__f_h_fifo'),
            ('tie_at_manhattan', 'manhattan__f_fifo', 'manhattan__f_h_fifo')]
        for contrast, baseline, candidate in comparisons:
            a, b = methods[baseline], methods[candidate]
            for metric in ABLATION_METRICS:
                av, bv = float(a[metric]), float(b[metric])
                contrasts.append({**{k: a[k] for k in ('case_id', 'grid_size', 'density', 'seed', 'reachable')},
                    'contrast': contrast, 'baseline': baseline, 'candidate': candidate, 'metric': metric,
                    'baseline_value': av, 'candidate_value': bv, 'delta': bv-av,
                    'reduction': (av-bv)/av if av else 0})
        a = methods['zero__f_h_fifo']
        for metric in ABLATION_METRICS:
            delta = ((float(methods['manhattan__f_h_fifo'][metric])-float(a[metric])) -
                     (float(methods['manhattan__f_fifo'][metric])-float(methods['zero__f_fifo'][metric])))
            contrasts.append({**{k: a[k] for k in ('case_id','grid_size','density','seed','reachable')},
                'contrast': 'interaction', 'baseline': '', 'candidate': '', 'metric': metric,
                'baseline_value': '', 'candidate_value': '', 'delta': delta, 'reduction': ''})
    groups = defaultdict(list)
    keys = ('grid_size','density','reachable','contrast','metric')
    for row in contrasts:
        groups[tuple(row[k] for k in keys)].append(row)
    effects = []
    for key, rows in groups.items():
        deltas = [r['delta'] for r in rows]
        lo, hi = bootstrap_ci(deltas)
        result = {**dict(zip(keys,key)), 'instances':len(rows), 'delta_mean':mean(deltas),
                  'delta_ci_low':lo, 'delta_ci_high':hi}
        if rows[0]['contrast'] != 'interaction':
            values = [r['reduction'] for r in rows]
            lo, hi = bootstrap_ci(values)
            result.update(reduction_mean=mean(values), reduction_ci_low=lo, reduction_ci_high=hi)
        effects.append(result)
    return {'ablation_per_case': selected,
            'ablation_summary': [r for r in summary if r['experiment']=='maze_ablation'],
            'ablation_contrasts':contrasts, 'ablation_effects':effects}


def median_interval(values, *, seed, block_length=1):
    """Percentile CI, resampling paired round deltas (optionally circular blocks)."""
    values = np.asarray(values, dtype=float)
    if not len(values):
        raise ValueError('at least one paired observation is required')
    rng = np.random.default_rng(seed)
    n = len(values)
    block_length = min(block_length, n)
    if block_length == 1:
        indices = rng.integers(0,n,size=(TIMING_RESAMPLES,n))
    else:
        starts = rng.integers(0,n,size=(TIMING_RESAMPLES,(n+block_length-1)//block_length))
        indices = ((starts[:,:,None]+np.arange(block_length)) % n).reshape(TIMING_RESAMPLES,-1)[:,:n]
    medians = np.median(values[indices],axis=1)
    lo, hi = np.quantile(medians,(.025,.975))
    return float(lo), float(hi)


def timing_tables(raw_rows):
    cases = defaultdict(lambda: defaultdict(dict))
    for r in raw_rows:
        if r['experiment'] in ('treasure','sensitivity'):
            cases[(r['experiment'],r['case_id'])][r['algorithm']][int(r['round'])] = r
    pairs, summaries = [], []
    for (experiment,case_id), methods in cases.items():
        for baseline,candidate in PAIRS:
            rounds = sorted(methods[baseline])
            if rounds != sorted(methods[candidate]):
                raise ValueError(f'unpaired timing rounds: {case_id}')
            group = []
            for round_id in rounds:
                a,b = methods[baseline][round_id],methods[candidate][round_id]
                av,bv = float(a['wall_ms']),float(b['wall_ms'])
                row = {'experiment':experiment,'case_id':case_id,'depth':a['depth'],
                    't1_value':a.get('t1_value',''),'baseline':baseline,'candidate':candidate,
                    'round':round_id,'baseline_order_index':a['order_index'],
                    'candidate_order_index':b['order_index'],'baseline_wall_ms':av,'candidate_wall_ms':bv,
                    'delta_ms':bv-av,'ratio':bv/av}
                group.append(row)
            deltas = [r['delta_ms'] for r in group]
            seed = int.from_bytes(hashlib.sha256(f'20261020:{case_id}:{baseline}:{candidate}'.encode()).digest()[:8],'big')
            lo,hi = median_interval(deltas,seed=seed)
            blo,bhi = median_interval(deltas,seed=seed,block_length=BLOCK_LENGTH)
            win = mean(r['delta_ms']<0 for r in group)
            stable = len(group)>=20 and hi<0 and bhi<0 and win>=.75
            conclusion = 'stable_faster' if stable else ('slower' if lo>0 and blo>0 else 'uncertain')
            if len(group)<20:
                conclusion = 'quick_only'
            summaries.append({'experiment':experiment,'case_id':case_id,'depth':group[0]['depth'],
                't1_value':group[0]['t1_value'],'baseline':baseline,'candidate':candidate,'rounds':len(group),
                'baseline_median_ms':median(r['baseline_wall_ms'] for r in group),
                'candidate_median_ms':median(r['candidate_wall_ms'] for r in group),
                'difference_of_medians_ms':median(r['candidate_wall_ms'] for r in group)-median(r['baseline_wall_ms'] for r in group),
                'paired_median_delta_ms':median(deltas),'paired_delta_ci_low':lo,'paired_delta_ci_high':hi,
                'block_delta_ci_low':blo,'block_delta_ci_high':bhi,'block_length':min(BLOCK_LENGTH,len(group)),
                'median_ratio':median(r['ratio'] for r in group),'candidate_faster_fraction':win,
                'conclusion':conclusion})
            pairs.extend(group)
    return {'treasure_timing_pairs':pairs,'treasure_timing_summary':summaries}


def analyze(root):
    tables = ablation_tables(read_csv(root/'tables/per_case.csv'),read_csv(root/'tables/summary.csv'))
    tables.update(timing_tables(read_csv(root/'raw/treasure.csv')+read_csv(root/'raw/sensitivity.csv')))
    for name,rows in tables.items():
        write_csv(root/'tables'/f'{name}.csv',rows)


def execution_orders(rows):
    groups = {}
    for r in rows:
        if 'execution_order' in r:
            key = (r['experiment'],r['case_id'],r['round'])
            groups.setdefault(key,{k:r.get(k,'') for k in
                ('run_id','experiment','case_id','depth','t1_value','grid_size','density','seed',
                 'round','order_seed','execution_order')})
    return list(groups.values())
