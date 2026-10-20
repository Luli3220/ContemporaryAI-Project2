"""Audit this raw batch against independent oracles, derived tables and hashes."""
import argparse
from collections import defaultdict
import json
from math import isclose, isfinite
import re
from statistics import median, mean, stdev
from .metrics import read_csv, shuffled_order
from .aggregate import FAMILIES, METRICS, CONFIG
from .analysis import ablation_tables, timing_tables, execution_orders
from .batch import BASE, digest
from .cases import maze_case, weighted_case, VALUES
from .references import bfs_distance, dijkstra_cost, enumerated_game
from .verify_official import verify


def same_records(expected, actual):
    assert len(expected)==len(actual),(len(expected),len(actual))
    for a,b in zip(expected,actual):
        for k in set(a)|set(b):
            av,bv=a.get(k,''),b.get(k,'')
            if isinstance(av,(int,float)) and not isinstance(av,bool):
                assert isclose(float(av),float(bv),rel_tol=1e-10,abs_tol=1e-12),(k,av,bv)
            else:
                assert str(av)==str(bv),(k,av,bv)


def audit(root):
    env=json.loads((root/'raw/environment.json').read_text(encoding='utf-8'))
    quick=env['mode']=='quick'
    for path,expected in env['source_sha256'].items():
        assert digest(BASE/path)==expected,f'source hash changed: {path}'
    manifest=json.loads((root/'raw/batch_manifest.json').read_text(encoding='utf-8'))
    assert manifest['run_id']==env['run_id'] and manifest['mode']==env['mode']
    for path,expected in manifest['files'].items():
        assert digest(BASE/path)==expected,f'batch artifact changed: {path}'
    official=json.loads((root/'raw/official.json').read_text(encoding='utf-8'))
    verify(official)
    all_rows=[]
    counts={}
    per_method=defaultdict(list)
    per_case=defaultdict(list)
    oracle_cache={}
    expected_methods={'maze':{'zero','manhattan'},'weighted':{'zero','adjusted'},
        **{k:{'minimax','original','reverse','heuristic'} for k in ('tree','treasure','sensitivity')},
        'maze_ablation':{f'{h}__{t}' for h in ('zero','manhattan') for t in ('f_h_fifo','f_fifo')}}
    for family in FAMILIES:
        rows=read_csv(root/'raw'/f'{family}.csv')
        assert rows and all(r['correctness_passed']=='True' and r['run_id']==env['run_id'] for r in rows)
        counts[family]=len(rows)
        for r in rows:
            assert r['experiment']==family
            assert isfinite(float(r['wall_ms'])) and float(r['wall_ms'])>=float(r['runtime_ms'])>=0
            per_method[(r['case_id'],r['algorithm'])].append(r)
            per_case[r['case_id']].append(r)
            if family in ('maze','maze_ablation','weighted'):
                n,seed=int(r['grid_size']),int(r['seed'])
                key=('weighted',n,seed,r['high_ratio'],r['density'],r['scenario']) if family=='weighted' else ('maze',n,seed,r['density'])
                if key not in oracle_cache:
                    grid=(weighted_case(n,float(r['high_ratio']),seed,obstacle=float(r['density']),zero=r['scenario']=='zero')
                          if family=='weighted' else maze_case(n,float(r['density']),seed))
                    oracle_cache[key]=(dijkstra_cost(grid,(0,0),(n-1,n-1)) if family=='weighted'
                                       else bfs_distance(grid,(0,0),(n-1,n-1)))
                assert float(r['optimal_cost'])==oracle_cache[key],key
            elif family in ('treasure','sensitivity'):
                key=(family,r['depth'],r.get('t1_value',''))
                if key not in oracle_cache:
                    values={**VALUES}
                    if family=='sensitivity':
                        values['T1']=int(r['t1_value'])
                    oracle_cache[key]=enumerated_game(official['distance_matrix'],values,int(r['depth']))[0]
                assert float(r['optimal_cost'])==oracle_cache[key],key
        all_rows.extend(rows)
    expected_counts=({'maze':48,'weighted':60,'tree':72,'treasure':56,'sensitivity':160,'maze_ablation':96}
                     if quick else {'maze':1920,'weighted':2400,'tree':2160,'treasure':840,'sensitivity':2400,'maze_ablation':3840})
    assert counts==expected_counts==env['measurement_counts'],counts
    for rows in per_method.values():
        family=rows[0]['experiment']
        repeats=(2 if quick else 30) if family in ('treasure','sensitivity') else (1 if quick else 3)
        assert len(rows)==repeats and {int(r['repeat']) for r in rows}==set(range(repeats))
        for metric in ('optimal_cost','path_steps','expanded','generated','popped','stale_pops',
                       'visited_nodes','evaluated_leaves','cutoff_events','pruned_siblings','best_target'):
            assert len({r.get(metric,'') for r in rows})==1,(family,metric)
    for rows in per_case.values():
        family=rows[0]['experiment']
        assert {r['algorithm'] for r in rows}==expected_methods[family]
        assert len({float(r['optimal_cost']) for r in rows})==1
        if family in ('treasure','sensitivity','maze_ablation'):
            groups=defaultdict(list)
            for r in rows:
                groups[int(r['round'])].append(r)
            methods=['minimax','original','reverse','heuristic']
            if family=='maze_ablation':
                from .maze_ablation import METHODS
                methods=METHODS
            for round_id,round_rows in groups.items():
                order,seed=shuffled_order(methods,rows[0]['case_id'],round_id)
                actual=sorted(round_rows,key=lambda r:int(r['order_index']))
                assert [r['algorithm'] for r in actual]==order and len(actual)==4
                for i,r in enumerate(actual):
                    assert int(r['order_index'])==i and int(r['order_seed'])==seed
                    assert r['execution_order']=='|'.join(order)
        if family=='maze_ablation':
            a=per_method[(rows[0]['case_id'],'zero__f_fifo')][0]
            b=per_method[(rows[0]['case_id'],'zero__f_h_fifo')][0]
            for metric in ('expanded','generated','max_frontier','popped','stale_pops'):
                assert a[metric]==b[metric],metric
    cases=read_csv(root/'tables/per_case.csv')
    assert len(cases)==len(per_method)
    for c in cases:
        rows=per_method[(c['case_id'],c['algorithm'])]
        assert int(c['repeats'])==len(rows)
        for metric in METRICS:
            values=[float(r[metric]) for r in rows if r.get(metric,'')!='']
            if values:
                assert isclose(float(c[metric]),median(values),rel_tol=1e-12,abs_tol=1e-12),(c['case_id'],metric)
    summaries=read_csv(root/'tables/summary.csv')
    groups=defaultdict(list)
    for c in cases:
        groups[tuple(c.get(k,'') for k in CONFIG)].append(c)
    assert len(groups)==len(summaries)
    for s in summaries:
        group=groups[tuple(s.get(k,'') for k in CONFIG)]
        assert int(s['instances'])==len(group)
        for metric in METRICS:
            values=[float(c[metric]) for c in group if c.get(metric,'')!='' and isfinite(float(c[metric]))]
            if values:
                assert isclose(float(s[metric+'_mean']),mean(values),rel_tol=1e-10,abs_tol=1e-12),metric
                assert isclose(float(s[metric+'_sd']),stdev(values) if len(values)>1 else 0,rel_tol=1e-10,abs_tol=1e-12),metric
    lookup={(c['case_id'],c['algorithm']):c for c in cases}
    for r in read_csv(root/'tables/paired.csv'):
        baseline='zero' if r['experiment'] in ('maze','weighted') else 'minimax'
        a,b=lookup[(r['case_id'],baseline)],lookup[(r['case_id'],r['algorithm'])]
        av,bv=float(a[r['metric']]),float(b[r['metric']])
        assert float(r['baseline_nodes'])==av and float(r['candidate_nodes'])==bv
        assert isclose(float(r['reduction']),(av-bv)/av if av else 0,abs_tol=1e-12)
        assert isclose(float(r['wall_ratio']),float(b['wall_ms'])/float(a['wall_ms']),rel_tol=1e-12)
    expected=ablation_tables(cases,summaries)
    expected.update(timing_tables(all_rows))
    for name,rows in expected.items():
        same_records(rows,read_csv(root/'tables'/f'{name}.csv'))
    scheduled=[r for r in all_rows if r['experiment'] in ('treasure','sensitivity','maze_ablation')]
    scheduled.sort(key=lambda r:{'maze_ablation':0,'treasure':1,'sensitivity':2}[r['experiment']])
    same_records(execution_orders(scheduled),read_csv(root/'raw/measurement_order.csv'))
    for name in ('maze_scaling','weighted_scaling','weighted_path','tree_scaling',
                 'treasure_search','root_actions','sensitivity','maze_ablation','treasure_timing'):
        for suffix in ('png','svg'):
            assert (root/'figures'/f'{name}.{suffix}').stat().st_size>1000
    if not quick:
        report=BASE/'report/report.md'
        content=report.read_text(encoding='utf-8')
        assert env['run_id'] in content and str(sum(counts.values())) in content
        for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',content):
            assert (report.parent/target).is_file(),target
    result={'schema_version':2,'run_id':env['run_id'],'mode':env['mode'],
        'measurement_counts':counts,'total_measurements':sum(counts.values()),
        'deterministic_repeats':True,'method_optima_equal':True,'independent_oracles_verified':True,
        'execution_order_verified':True,'raw_to_tables_verified':True,'batch_hashes_verified':True,
        'source_hashes_verified':True,'png_count':9,'svg_count':9,'status':'passed'}
    (root/'raw/audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true')
    args=parser.parse_args()
    audit(BASE/'results/quick' if args.quick else BASE/'results')
