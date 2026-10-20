"""Run course regressions, full controlled experiments, plots and report."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter
from . import maze_experiments, weighted_experiments, game_tree_experiments, treasure_experiments
from .aggregate import aggregate
from .demo import official_results
from .metrics import write_csv

BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    root = BASE / 'results' / 'quick' if args.quick else BASE / 'results'
    (root / 'raw').mkdir(parents=True, exist_ok=True)
    results = official_results()
    assert len(results['maze_path'])-1 == 7 and results['weighted_cost'] == 7
    assert results['tree'] == {'minimax':5, 'alpha_beta':5}
    assert results['treasure']['2']['alpha_beta'] == {'best_target':'T2','best_value':-1}
    assert results['treasure']['4']['alpha_beta'] == {'best_target':'T3','best_value':3}
    (root / 'raw' / 'official.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    environment = {'python':sys.version, 'executable':sys.executable, 'platform':platform.platform(),
        'processor':platform.processor(), 'logical_cpus':os.cpu_count(), 'mode':'quick' if args.quick else 'full',
        'seeds':list(range(3 if args.quick else 20)), 'repeats':1 if args.quick else 3,
        'treasure_repeats':2 if args.quick else 30, 'bootstrap_seed':20261019,
        'bootstrap_resamples':1000,
        'dependencies':{x:importlib.metadata.version(x) for x in ('pytest','matplotlib','numpy')},
        'source_sha256':{str(p.relative_to(BASE)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src','experiments','tests') for p in sorted((BASE/folder).rglob('*.py'))}}
    start = perf_counter()
    for name, module in [('maze', maze_experiments), ('weighted', weighted_experiments), ('tree', game_tree_experiments)]:
        print(f'Running {name} ...', flush=True)
        rows = module.run(args.quick)
        write_csv(root / 'raw' / f'{name}.csv', rows)
        print(f'  {len(rows)} validated observations', flush=True)
    rows, roots, sensitivity, times, variations = treasure_experiments.run(args.quick)
    for name, data in [('treasure',rows), ('root_actions',roots), ('sensitivity',sensitivity), ('routing_times',times)]:
        write_csv(root / 'raw' / f'{name}.csv', data)
    (root / 'raw' / 'principal_variations.json').write_text(json.dumps(variations, indent=2), encoding='utf-8')
    print('Aggregating paired observations ...', flush=True)
    aggregate(root)
    environment['experiment_elapsed_seconds'] = perf_counter() - start
    (root / 'raw' / 'environment.json').write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding='utf-8')
    from .plot_results import plot_all
    plot_all(root)
    if not args.quick:
        from .write_report import write_report
        write_report(root)
        from .audit_results import audit
        audit(root)
    print(f'Complete: {root}', flush=True)


if __name__ == '__main__':
    main()
