"""Run course regressions, full controlled experiments, plots and report."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import gc
import uuid
from datetime import datetime, timezone
from time import perf_counter
from . import maze_experiments, weighted_experiments, game_tree_experiments, treasure_experiments, maze_ablation
from .demo import official_results
from .metrics import write_csv
from .metrics import ORDER_SEED, WARMUP_ROUNDS
from .analysis import execution_orders, TIMING_RESAMPLES, BLOCK_LENGTH
from .verify_official import verify
from .rebuild_results import rebuild

BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    root = BASE / 'results' / 'quick' if args.quick else BASE / 'results'
    (root / 'raw').mkdir(parents=True, exist_ok=True)
    results = official_results()
    verify(results)
    (root / 'raw' / 'official.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    source_files=[p for folder in ('src','experiments','tests','scripts') for p in sorted((BASE/folder).rglob('*.py'))]
    source_files += [BASE/'requirements-repro.txt',BASE/'requirements.txt',BASE/'pyproject.toml',
                     BASE/'.github/workflows/ci.yml']
    environment = {'schema_version':2,'run_id':run_id,'started_at_utc':datetime.now(timezone.utc).isoformat(),
        'python':sys.version, 'executable':sys.executable, 'platform':platform.platform(),
        'processor':platform.processor(), 'logical_cpus':os.cpu_count(), 'mode':'quick' if args.quick else 'full',
        'seeds':list(range(3 if args.quick else 20)), 'repeats':1 if args.quick else 3,
        'treasure_repeats':2 if args.quick else 30, 'bootstrap_seed':20261019,
        'bootstrap_resamples':1000,
        'order_seed':ORDER_SEED,'warmup_rounds':WARMUP_ROUNDS,'timing_bootstrap_resamples':TIMING_RESAMPLES,
        'timing_block_length':BLOCK_LENGTH,'gc_enabled':gc.isenabled(),
        'timing_schedule':'interleaved seeded shuffle per case and round',
        'tie_breaking_default':'f_h_fifo',
        'dependencies':{x:importlib.metadata.version(x) for x in ('pytest','matplotlib','numpy')},
        'source_sha256':{p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}}
    start = perf_counter()
    scheduled=[]
    counts={}
    def save(name,rows):
        for row in rows:
            row['run_id']=run_id
        write_csv(root/'raw'/f'{name}.csv',rows)
        counts[name]=len(rows)
        scheduled.extend(rows if name in ('treasure','sensitivity','maze_ablation') else [])
    for name, module in [('maze', maze_experiments), ('weighted', weighted_experiments),
                         ('tree', game_tree_experiments),('maze_ablation',maze_ablation)]:
        print(f'Running {name} ...', flush=True)
        rows = module.run(args.quick)
        save(name,rows)
        print(f'  {len(rows)} validated observations', flush=True)
    rows, roots, sensitivity, times, variations = treasure_experiments.run(args.quick)
    for name, data in [('treasure',rows), ('root_actions',roots), ('sensitivity',sensitivity), ('routing_times',times)]:
        save(name,data)
    save('root_responses',treasure_experiments.root_responses(results['distance_matrix']))
    write_csv(root/'raw/measurement_order.csv',execution_orders(scheduled))
    (root / 'raw' / 'principal_variations.json').write_text(json.dumps(variations, indent=2), encoding='utf-8')
    print('Aggregating and auditing paired observations ...', flush=True)
    environment['experiment_elapsed_seconds'] = perf_counter() - start
    environment['measurement_counts']={k:counts[k] for k in ('maze','weighted','tree','treasure','sensitivity','maze_ablation')}
    (root / 'raw' / 'environment.json').write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding='utf-8')
    rebuild(root)
    from .audit_results import audit
    audit(root)
    print(f'Complete: {root}', flush=True)


if __name__ == '__main__':
    main()
