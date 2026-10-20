"""Check persisted records and delivery links without rerunning measurements."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from .metrics import read_csv


def audit(root):
    environment=json.loads((root/'raw/environment.json').read_text(encoding='utf-8'))
    for path, digest in environment.get('source_sha256',{}).items():
        assert hashlib.sha256((root.parent/path).read_bytes()).hexdigest()==digest, path
    counts = {}
    for name in ('maze','weighted','tree','treasure','sensitivity'):
        rows = read_csv(root/'raw'/f'{name}.csv')
        assert rows and all(r['correctness_passed']=='True' for r in rows), name
        groups = defaultdict(list)
        for row in rows:
            groups[(row['case_id'],row['algorithm'])].append(row)
            assert float(row['wall_ms']) >= float(row['runtime_ms']) >= 0
        for key, repeats in groups.items():
            for metric in ('optimal_cost','path_steps','expanded','generated','popped','stale_pops',
                           'visited_nodes','evaluated_leaves','cutoff_events','pruned_siblings','best_target'):
                assert len({r.get(metric,'') for r in repeats})==1, (key,metric)
        # All methods for a case must agree on exact optimum.
        costs=defaultdict(set)
        for row in rows:
            costs[row['case_id']].add(float(row['optimal_cost']))
        assert all(len(values)==1 for values in costs.values()), name
        counts[name]=len(rows)
    report = root.parent/'report/report.md'
    content=report.read_text(encoding='utf-8')
    for target in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',content):
        assert (report.parent/target).is_file(), target
    for name in ('maze_scaling','weighted_scaling','weighted_path','tree_scaling',
                 'treasure_search','root_actions','sensitivity'):
        for suffix in ('png','svg'):
            assert (root/'figures'/f'{name}.{suffix}').stat().st_size > 1000
    for module in ('astar','minimax','alpha_beta','treasure_game'):
        source=(root.parent/'src/search_algorithms'/f'{module}.py').read_text(encoding='utf-8')
        assert 'networkx' not in source.lower()
    result={'measurement_counts':counts,'total_measurements':sum(counts.values()),
            'deterministic_repeats':True,'method_optima_equal':True,'all_figure_links_exist':True,
            'source_hashes_verified':bool(environment.get('source_sha256')),
            'png_count':7,'svg_count':7,'status':'passed'}
    (root/'raw/audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    audit(Path(__file__).resolve().parents[1]/'results')
