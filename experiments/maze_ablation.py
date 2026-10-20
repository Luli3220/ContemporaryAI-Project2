"""Paired 2x2 heuristic / queue tie-breaking ablation on the original maze cases."""
from search_algorithms import AStarStats, maze_search
from .cases import maze_case
from .references import bfs_distance
from .metrics import measure_interleaved, path_output

METHODS = tuple(f'{h}__{tie}' for h in ('zero', 'manhattan') for tie in ('f_h_fifo', 'f_fifo'))


def run(quick=False):
    rows = []
    for n in ([10, 20] if quick else [10, 20, 40, 80]):
        for density in (0, .1, .2, .3):
            for seed in range(3 if quick else 20):
                grid = maze_case(n, density, seed)
                goal = (n - 1, n - 1)
                expected = bfs_distance(grid, (0, 0), goal)
                calls = {}
                for method in METHODS:
                    h, tie = method.split('__')
                    calls[method] = lambda st, h=h, tie=tie: maze_search(
                        (0, 0), goal, grid, heuristic=h, tie_breaking=tie, stats=st)
                observations = measure_interleaved(calls, AStarStats,
                    {'experiment': 'maze_ablation', 'case_id': f'ablation_{n}_{density}_{seed}',
                     'grid_size': n, 'density': density, 'seed': seed},
                    1 if quick else 3, path_output, expected)
                for row in observations:
                    row['heuristic'], row['tie_breaking'] = row['algorithm'].split('__')
                rows.extend(observations)
    return rows
