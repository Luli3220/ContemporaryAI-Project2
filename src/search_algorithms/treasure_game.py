"""Weighted routing and immutable, alternating treasure decisions."""
from dataclasses import dataclass
from math import inf, isfinite
from time import perf_counter
from .astar import Grid, astar_search, manhattan, shape_of
from .models import GameStats, reset_stats


@dataclass(frozen=True)
class TreasureState:
    pos_a: str = 'A'
    pos_b: str = 'B'
    remaining: frozenset[str] = frozenset({'T1', 'T2', 'T3', 'T4'})
    score_a: float = 0
    score_b: float = 0
    current_player: str = 'A'

    def __post_init__(self):
        if self.current_player not in ('A', 'B') or not isinstance(self.remaining, frozenset):
            raise ValueError('player must be A/B and remaining must be frozenset')
        if not isfinite(self.score_a) or not isfinite(self.score_b):
            raise ValueError('scores must be finite')


def compute_distance_matrix(grid: Grid, labels: tuple[str, ...] = ('A', 'B', 'T1', 'T2', 'T3', 'T4')) -> dict[str, dict[str, float]]:
    shape = shape_of(grid)
    if len(set(labels)) != len(labels) or not labels:
        raise ValueError('labels must be unique and nonempty')
    positions = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if isinstance(v, str) and v in labels:
                if v in positions:
                    raise ValueError('duplicate label')
                positions[v] = (r, c)
            elif v != 'X' and not (type(v) is int and v >= 0):
                raise ValueError('unknown cell or negative terrain')
    if set(positions) != set(labels):
        raise ValueError('every label must occur exactly once')
    floor = min([1] + [v for row in grid for v in row if type(v) is int])

    def cost(p):
        v = grid[p[0]][p[1]]
        return v if type(v) is int else 1

    matrix = {}
    for a in labels:
        matrix[a] = {}
        for b in labels:
            matrix[a][b] = 0 if a == b else astar_search(
                positions[a], positions[b], shape,
                lambda p: grid[p[0]][p[1]] == 'X', cost,
                lambda p, q: manhattan(p, q) * floor).cost
    return matrix


def legal_actions(state: TreasureState, distance_matrix: dict | None = None) -> list[str]:
    actions = sorted(state.remaining)
    if distance_matrix is not None:
        p = state.pos_a if state.current_player == 'A' else state.pos_b
        actions = [t for t in actions if isfinite(distance_matrix[p][t])]
    return actions


def transition(state: TreasureState, target: str, distance_matrix: dict,
               treasure_values: dict[str, int]) -> TreasureState:
    if target not in state.remaining:
        raise ValueError('treasure absent or already collected')
    p = state.pos_a if state.current_player == 'A' else state.pos_b
    distance = distance_matrix[p][target]
    if not isfinite(distance) or distance < 0:
        raise ValueError('target must be reachable with nonnegative cost')
    gain = treasure_values[target] - distance
    a = state.current_player == 'A'
    return TreasureState(target if a else state.pos_a, state.pos_b if a else target,
                         state.remaining - {target}, state.score_a + (gain if a else 0),
                         state.score_b + (0 if a else gain), 'B' if a else 'A')


def _search(state, depth, matrix, values, prune, order, stats):
    if type(depth) is not int or depth < 0:
        raise ValueError('depth must be a nonnegative integer')
    if order not in ('original', 'reverse', 'heuristic'):
        raise ValueError('unknown order')
    if any(type(v) not in (int, float) or not isfinite(v) for v in values.values()):
        raise ValueError('treasure values must be finite numbers')
    st = stats if stats is not None else GameStats()
    reset_stats(st)
    begin = perf_counter()

    def visit(s, h, alpha, beta):
        st.visited_nodes += 1
        actions = legal_actions(s, matrix)
        if h == 0 or not actions:
            st.evaluated_leaves += 1
            return s.score_a - s.score_b, None
        is_max = s.current_player == 'A'
        if order == 'reverse':
            actions.reverse()
        elif order == 'heuristic':
            p = s.pos_a if is_max else s.pos_b
            st.ordering_probes += len(actions)
            # Both players prefer their own immediate gain; stable sort breaks ties.
            actions.sort(key=lambda t: values[t] - matrix[p][t], reverse=True)
        best, target = (-inf if is_max else inf), None
        for i, t in enumerate(actions):
            child = transition(s, t, matrix, values)
            v, _ = visit(child, h - 1, alpha, beta)
            if (v > best if is_max else v < best):
                best, target = v, t
            if prune:
                if is_max:
                    alpha = max(alpha, best)
                else:
                    beta = min(beta, best)
                remaining = len(actions) - i - 1
                if alpha >= beta and remaining:
                    st.cutoff_events += 1
                    st.pruned_siblings += remaining
                    break
        return best, target

    value, target = visit(state, depth, -inf, inf)
    st.runtime_ms = (perf_counter() - begin) * 1000
    return {'best_target': target, 'best_value': value}


def treasure_minimax(state: TreasureState, depth: int, distance_matrix: dict,
                     treasure_values: dict[str, int], *, stats: GameStats | None = None) -> dict[str, str | float | None]:
    return _search(state, depth, distance_matrix, treasure_values, False, 'original', stats)


def treasure_alpha_beta(state: TreasureState, depth: int, distance_matrix: dict,
                        treasure_values: dict[str, int], *, order: str = 'original',
                        stats: GameStats | None = None) -> dict[str, str | float | None]:
    return _search(state, depth, distance_matrix, treasure_values, True, order, stats)


def solve_treasure_game(grid: Grid, treasure_values: dict[str, int], depth: int, *,
                        algorithm: str = 'alpha_beta', order: str = 'original',
                        stats: GameStats | None = None) -> dict[str, str | float | None]:
    if algorithm not in ('minimax', 'alpha_beta'):
        raise ValueError('algorithm must be minimax or alpha_beta')
    matrix = compute_distance_matrix(grid, ('A', 'B', *sorted(treasure_values)))
    state = TreasureState(remaining=frozenset(treasure_values))
    return _search(state, depth, matrix, treasure_values, algorithm == 'alpha_beta', order, stats)
