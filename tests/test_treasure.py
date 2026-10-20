from dataclasses import FrozenInstanceError
from math import inf
import random
import pytest
from search_algorithms import (TreasureState, GameStats, compute_distance_matrix, legal_actions,
    transition, treasure_minimax, treasure_alpha_beta, solve_treasure_game)
from experiments.cases import TREASURE, VALUES
from experiments.references import dijkstra_cost, enumerated_game


@pytest.fixture(scope='module')
def matrix():
    return compute_distance_matrix(TREASURE)


def test_distance_matrix(matrix):
    expected = [[0,12,10,4,8,8], [12,0,8,8,4,10], [10,8,0,6,6,12],
                [4,8,6,0,6,6], [8,4,6,6,0,6], [8,10,12,6,6,0]]
    labels = list(matrix)
    positions = {v: (r, c) for r, row in enumerate(TREASURE)
                 for c, v in enumerate(row) if isinstance(v, str) and v != 'X'}
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            assert matrix[a][b] == expected[i][j]
            assert matrix[a][b] == dijkstra_cost(TREASURE, positions[a], positions[b], free_goal=False)


@pytest.mark.parametrize('depth,target,value,nodes,actions', [
    (2, 'T2', -1, 17, [-4,-1,-2,-4]), (4, 'T3', 3, 65, [-5,1,3,-7])])
def test_official_game(matrix, depth, target, value, nodes, actions):
    st = GameStats()
    expected = {'best_target': target, 'best_value': value}
    assert treasure_minimax(TreasureState(), depth, matrix, VALUES, stats=st) == expected
    assert st.visited_nodes == nodes
    for order in ('original', 'reverse', 'heuristic'):
        assert treasure_alpha_beta(TreasureState(), depth, matrix, VALUES, order=order) == expected
    v, roots = enumerated_game(matrix, VALUES, depth)
    assert v == value and list(roots.values()) == actions


def test_transitions(matrix):
    s = TreasureState()
    t = transition(s, 'T1', matrix, VALUES)
    assert t.score_a == -1 and t.score_b == 0 and t.pos_a == 'T1' and t.pos_b == 'B'
    assert s.remaining == frozenset(VALUES) and len(t.remaining) == 3 and t.current_player == 'B'
    u = transition(t, 'T3', matrix, VALUES)
    assert u.pos_a == 'T1' and u.pos_b == 'T3' and u.score_b == 3 and u.current_player == 'A'
    with pytest.raises(ValueError):
        transition(t, 'T1', matrix, VALUES)
    with pytest.raises(FrozenInstanceError):
        s.score_a = 3


@pytest.mark.parametrize('depth', range(7))
def test_horizons_and_exhaustion(matrix, depth):
    s = TreasureState()
    expected, _ = enumerated_game(matrix, VALUES, depth)
    assert treasure_minimax(s, depth, matrix, VALUES)['best_value'] == expected
    for order in ('original', 'reverse', 'heuristic'):
        assert treasure_alpha_beta(s, depth, matrix, VALUES, order=order)['best_value'] == expected
    if depth == 0:
        assert treasure_alpha_beta(s, depth, matrix, VALUES)['best_target'] is None


def test_unreachable_and_ties():
    m = {'A': {'T1': inf}, 'B': {'T1': 1}, 'T1': {'T1': 0}}
    s = TreasureState(remaining=frozenset({'T1'}))
    assert legal_actions(s, m) == []
    assert treasure_alpha_beta(s, 4, m, {'T1': 2}) == {'best_target': None, 'best_value': 0}
    with pytest.raises(ValueError):
        transition(s, 'T1', m, {'T1': 2})
    m = {a: {b: 0 for b in ('A','B','T1','T2')} for a in ('A','B','T1','T2')}
    s = TreasureState(remaining=frozenset({'T1', 'T2'}))
    assert treasure_alpha_beta(s, 2, m, {'T1':1,'T2':1})['best_target'] == 'T1'


@pytest.mark.parametrize('seed', range(60))
def test_random_directed_games(seed):
    rng = random.Random(seed)
    labels = ['A', 'B', *VALUES]
    matrix = {a: {b: 0 if a == b else rng.randint(0, 20) for b in labels} for a in labels}
    values = {t: rng.randint(-3, 12) for t in VALUES}
    s = TreasureState()
    for depth in (1,2,3,4):
        expected, _ = enumerated_game(matrix, values, depth)
        assert treasure_minimax(s, depth, matrix, values)['best_value'] == expected
        for order in ('original', 'reverse', 'heuristic'):
            assert treasure_alpha_beta(s, depth, matrix, values, order=order)['best_value'] == expected


def test_public_wrapper_and_invalid(matrix):
    assert solve_treasure_game(TREASURE, VALUES, 4)['best_value'] == 3
    for depth in (-1, 1.5, True):
        with pytest.raises(ValueError):
            treasure_minimax(TreasureState(), depth, matrix, VALUES)
    with pytest.raises(ValueError):
        compute_distance_matrix([['A', 'A', 'B']], ('A', 'B'))
    with pytest.raises(ValueError):
        compute_distance_matrix([['A']], ('A', 'B'))
