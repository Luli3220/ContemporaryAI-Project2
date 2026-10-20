from statistics import median
from time import perf_counter
from search_algorithms import (GameStats, TreasureState, compute_distance_matrix,
    treasure_minimax, treasure_alpha_beta, solve_treasure_game, transition)
from .cases import TREASURE, VALUES
from .references import enumerated_game
from .metrics import measure_interleaved, game_output


def timed_game(matrix, values, depth, config, repeats):
    expected, _ = enumerated_game(matrix, values, depth)
    calls = {'minimax': lambda st: treasure_minimax(TreasureState(), depth, matrix, values, stats=st)}
    for method in ('original', 'reverse', 'heuristic'):
        calls[method] = lambda st, method=method: treasure_alpha_beta(
            TreasureState(), depth, matrix, values, order=method, stats=st)
    return measure_interleaved(calls, GameStats, config, repeats, game_output, expected)


def root_responses(matrix):
    rows=[]
    for depth in (2,4):
        for target in sorted(VALUES):
            state=transition(TreasureState(),target,matrix,VALUES)
            for reply in sorted(state.remaining):
                child=transition(state,reply,matrix,VALUES)
                value=treasure_minimax(child,depth-2,matrix,VALUES)['best_value']
                expected,_=enumerated_game(matrix,VALUES,depth-2,child)
                assert value==expected
                rows.append({'depth':depth,'a_first':target,'b_reply':reply,'utility':value})
    return rows


def run(quick=False):
    matrix = compute_distance_matrix(TREASURE)
    rows, roots, sensitivity = [], [], []
    for depth in range(7):
        expected, root_values = enumerated_game(matrix, VALUES, depth)
        roots.extend({'depth': depth, 'target': target, 'value': value} for target, value in root_values.items())
        rows += timed_game(matrix, VALUES, depth,
            {'experiment': 'treasure', 'case_id': f'treasure_{depth}', 'depth': depth},
            2 if quick else 30)
    for value in range(0, 19, 2):
        values = {**VALUES, 'T1': value}
        for depth in (2, 4):
            expected, _ = enumerated_game(matrix, values, depth)
            sensitivity += timed_game(matrix, values, depth,
                {'experiment': 'sensitivity', 'case_id': f'sensitivity_{value}_{depth}',
                 't1_value': value, 'depth': depth}, 2 if quick else 30)
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
