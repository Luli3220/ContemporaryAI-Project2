import random
from search_algorithms import GameStats, minimax, alpha_beta
from .cases import random_tree
from .metrics import measure, game_output


def run(quick=False):
    rows = []
    for branch in (2, 3, 4):
        for depth in ([2, 4] if quick else [2, 4, 6]):
            for seed in range(3 if quick else 20):
                tree = random_tree(branch, depth, seed)
                expected = minimax(tree)
                methods = ['minimax', 'original', 'reverse', 'heuristic']
                random.Random(seed).shuffle(methods)
                for method in methods:
                    config = {'experiment': 'tree', 'case_id': f'tree_{branch}_{depth}_{seed}',
                              'branch': branch, 'depth': depth, 'seed': seed, 'algorithm': method}
                    call = (lambda st: minimax(tree, stats=st)) if method == 'minimax' else (
                        lambda st: alpha_beta(tree, order=method, stats=st))
                    rows += measure(call, GameStats, config, 1 if quick else 3, game_output, expected)
    return rows
