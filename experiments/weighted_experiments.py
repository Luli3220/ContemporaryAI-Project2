import random
from search_algorithms import AStarStats, weighted_search
from .cases import weighted_case
from .references import dijkstra_cost
from .metrics import measure, path_output


def run(quick=False):
    rows = []
    scenarios = [('base', .1, 0, False), ('base', .4, 0, False), ('base', .7, 0, False),
                 ('zero', .4, 0, True), ('obstacles', .4, .2, False)]
    for n in ([10, 20] if quick else [10, 20, 40, 80]):
        for scenario, high, density, zero in scenarios:
            for seed in range(3 if quick else 20):
                grid = weighted_case(n, high, seed, obstacle=density, zero=zero)
                goal = (n - 1, n - 1)
                expected = dijkstra_cost(grid, (0, 0), goal)
                methods = ['zero', 'adjusted']
                random.Random(seed).shuffle(methods)
                for h in methods:
                    config = {'experiment': 'weighted', 'case_id': f'weighted_{n}_{scenario}_{high}_{seed}',
                        'grid_size': n, 'scenario': scenario, 'high_ratio': high, 'density': density,
                        'seed': seed, 'algorithm': h}
                    rows += measure(lambda st: weighted_search((0, 0), goal, grid, heuristic=h, stats=st),
                        AStarStats, config, 1 if quick else 3, path_output, expected)
    return rows
