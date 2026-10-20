from statistics import median
from time import perf_counter
from search_algorithms import (GameStats, TreasureState, compute_distance_matrix,
    treasure_minimax, treasure_alpha_beta, solve_treasure_game, transition)
from .cases import TREASURE, VALUES
from .references import enumerated_game
from .metrics import measure, game_output


def run(quick=False):
    matrix = compute_distance_matrix(TREASURE)
    rows, roots, sensitivity = [], [], []
    for depth in range(7):
        expected, root_values = enumerated_game(matrix, VALUES, depth)
        roots.extend({'depth': depth, 'target': target, 'value': value} for target, value in root_values.items())
        for method in ('minimax', 'original', 'reverse', 'heuristic'):
            call = (lambda st: treasure_minimax(TreasureState(), depth, matrix, VALUES, stats=st)) if method == 'minimax' else (
                lambda st: treasure_alpha_beta(TreasureState(), depth, matrix, VALUES, order=method, stats=st))
            config = {'experiment': 'treasure', 'case_id': f'treasure_{depth}', 'depth': depth, 'algorithm': method}
            rows += measure(call, GameStats, config, 2 if quick else 30, game_output, expected)
    for value in range(0, 19, 2):
        values = {**VALUES, 'T1': value}
        for depth in (2, 4):
            expected, _ = enumerated_game(matrix, values, depth)
            for order in ('original', 'heuristic'):
                config = {'experiment': 'sensitivity', 'case_id': f'sensitivity_{value}_{depth}',
                          't1_value': value, 'depth': depth, 'algorithm': order}
                sensitivity += measure(lambda st: treasure_alpha_beta(TreasureState(), depth, matrix, values,
                    order=order, stats=st), GameStats, config, 2 if quick else 30, game_output, expected)
    # Routing time is intentionally kept separate from game recursion time.
    times = []
    compute_distance_matrix(TREASURE)
    for repeat in range(2 if quick else 30):
        begin = perf_counter()
        compute_distance_matrix(TREASURE)
        precompute_ms = (perf_counter() - begin) * 1000
        begin = perf_counter()
        solve_treasure_game(TREASURE, VALUES, 4)
        end_to_end_ms = (perf_counter() - begin) * 1000
        times.append({'repeat': repeat, 'precompute_ms': precompute_ms, 'end_to_end_ms': end_to_end_ms})
    # Principal variations: exact re-search each child instead of mislabeling AB bounds as exact.
    variations = {}
    for depth in (2, 4):
        s, sequence = TreasureState(), []
        for h in range(depth, 0, -1):
            result = treasure_minimax(s, h, matrix, VALUES)
            t = result['best_target']
            child = transition(s, t, matrix, VALUES)
            sequence.append({'player': s.current_player, 'target': t,
                'gain': (child.score_a - s.score_a) if s.current_player == 'A' else (child.score_b - s.score_b),
                'score_a': child.score_a, 'score_b': child.score_b})
            s = child
        variations[str(depth)] = sequence
    return rows, roots, sensitivity, times, variations
