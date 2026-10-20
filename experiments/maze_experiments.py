import random
from search_algorithms import AStarStats, maze_search
from .cases import maze_case
from .references import bfs_distance
from .metrics import measure, path_output


def run(quick=False):
    rows = []
    for n in ([10, 20] if quick else [10, 20, 40, 80]):
        for density in (0, .1, .2, .3):
            for seed in range(3 if quick else 20):
                grid = maze_case(n, density, seed)
                goal = (n - 1, n - 1)
                expected = bfs_distance(grid, (0, 0), goal)
                methods = ['zero', 'manhattan']
                random.Random(seed).shuffle(methods)
                for h in methods:
                    config = {'experiment': 'maze', 'case_id': f'maze_{n}_{density}_{seed}',
                              'grid_size': n, 'density': density, 'seed': seed, 'algorithm': h}
                    rows += measure(lambda st: maze_search((0, 0), goal, grid, heuristic=h, stats=st),
                                    AStarStats, config, 1 if quick else 3, path_output, expected)
    return rows
