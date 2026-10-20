import copy
from math import inf
import random
import pytest
from search_algorithms import (AStarStats, astar_search, maze_search, weighted_search,
                               solve_maze, solve_weighted_terrain)
from experiments.cases import MAZE, WEIGHTED, maze_case, weighted_case
from experiments.references import bfs_distance, dijkstra_cost


def check_path(result, grid, start, goal, weighted=False):
    if not result.found:
        assert result.path == [] and result.cost == inf
        return
    assert result.path[0] == start and result.path[-1] == goal
    assert len(result.path) == len(set(result.path))
    total = 0
    for a, b in zip(result.path, result.path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        assert 0 <= b[0] < len(grid) and 0 <= b[1] < len(grid[0])
        assert grid[b[0]][b[1]] != 'X'
        total += (0 if b == goal else grid[b[0]][b[1]]) if weighted else 1
    assert total == result.cost


def test_course_paths():
    original = copy.deepcopy((MAZE, WEIGHTED))
    assert len(solve_maze((0, 0), (3, 4), MAZE)) - 1 == 7
    assert solve_weighted_terrain((0, 0), (4, 4), WEIGHTED) == 7
    check_path(weighted_search((0, 0), (4, 4), WEIGHTED), WEIGHTED, (0, 0), (4, 4), True)
    assert (MAZE, WEIGHTED) == original


@pytest.mark.parametrize('grid,start,goal,distance', [
    ([['.']], (0, 0), (0, 0), 0),
    ([list('SE')], (0, 0), (0, 1), 1),
    ([list('S..E')], (0, 0), (0, 3), 3),
    ([['S'], ['.'], ['E']], (0, 0), (2, 0), 2),
    ([list('SXE')], (0, 0), (0, 2), inf),
    ([list('S..'), list('...'), list('..E')], (0, 0), (2, 2), 4),
    ([list('S.XE'), list('.XX.'), list('....')], (0, 0), (0, 3), 7),
])
def test_maze_boundaries(grid, start, goal, distance):
    result = maze_search(start, goal, grid)
    assert result.cost == distance
    check_path(result, grid, start, goal)


@pytest.mark.parametrize('grid,start,goal', [([], (0, 0), (0, 0)),
    ([[]], (0, 0), (0, 0)), ([['.'], ['.', '.']], (0, 0), (1, 0)),
    ([['?']], (0, 0), (0, 0)), ([['.']], (-1, 0), (0, 0)),
    ([['.']], (0, 0), (1, 0)), ([['X']], (0, 0), (0, 0)),
    ([list('SE')], (0, 1), (0, 0)), ([list('SSE')], (0, 0), (0, 2))])
def test_maze_invalid(grid, start, goal):
    with pytest.raises(ValueError):
        solve_maze(start, goal, grid)


@pytest.mark.parametrize('seed', range(100))
def test_random_maze(seed):
    rng = random.Random(seed)
    n = rng.randrange(2, 18)
    grid = maze_case(n, rng.uniform(0, .5), seed)
    expected = bfs_distance(grid, (0, 0), (n - 1, n - 1))
    for h in ('zero', 'manhattan'):
        result = maze_search((0, 0), (n - 1, n - 1), grid, heuristic=h)
        assert result.cost == expected
        check_path(result, grid, (0, 0), (n - 1, n - 1))


@pytest.mark.parametrize('grid,start,goal,cost', [
    ([[5]], (0, 0), (0, 0), 0), ([['S', 'E']], (0, 0), (0, 1), 0),
    ([['S', 0, 0, 'E']], (0, 0), (0, 3), 0),
    ([['S', 'X', 'E']], (0, 0), (0, 2), -1),
    ([['S', 8, 'E'], [1, 1, 1]], (0, 0), (0, 2), 3),
    ([['S', 2, 2], [1, 1, 'E']], (0, 0), (1, 2), 2),
    ([['S', 3, 3, 'E']], (0, 0), (0, 3), 6),
    ([['S'], [2], ['E']], (0, 0), (2, 0), 2)])
def test_weighted_boundaries(grid, start, goal, cost):
    assert solve_weighted_terrain(start, goal, grid) == cost
    check_path(weighted_search(start, goal, grid), grid, start, goal, True)


@pytest.mark.parametrize('grid', [[['S', -1, 'E']], [['S', True, 'E']],
    [['S', 1.5, 'E']], [['S', '?', 'E']], [['S'], [1, 'E']], [], [['E', 'S']]])
def test_weighted_invalid(grid):
    with pytest.raises(ValueError):
        solve_weighted_terrain((0, 0), (0, 2), grid)


@pytest.mark.parametrize('seed', range(100))
def test_random_weighted(seed):
    n = 2 + seed % 14
    grid = weighted_case(n, .4, seed, obstacle=.2, zero=seed % 2 == 0)
    expected = dijkstra_cost(grid, (0, 0), (n - 1, n - 1))
    for h in ('zero', 'adjusted'):
        result = weighted_search((0, 0), (n - 1, n - 1), grid, heuristic=h)
        assert result.cost == expected
        check_path(result, grid, (0, 0), (n - 1, n - 1), True)


def test_stats_reset_and_goal_not_expanded():
    st = AStarStats(generated=999)
    maze_search((0, 0), (0, 0), [['.']], stats=st)
    assert (st.generated, st.popped, st.expanded, st.max_frontier) == (1, 1, 0, 1)


def test_inconsistent_admissible_heuristic_reopens_and_stales():
    # Enumerate deterministic grid instances to exercise stale entries; oracle costs stay equal.
    stale = 0
    for seed in range(30):
        grid = weighted_case(10, .4, seed, obstacle=.1)
        goal = (9, 9)
        # h=0 on alternating cells, safe adjusted Manhattan elsewhere: admissible, inconsistent.
        result = astar_search((0, 0), goal, (10, 10),
            lambda p: grid[p[0]][p[1]] == 'X',
            lambda p: 0 if p == goal else (1 if grid[p[0]][p[1]] == 'S' else grid[p[0]][p[1]]),
            lambda p, g: max(abs(p[0]-g[0])+abs(p[1]-g[1])-1, 0) if sum(p) % 2 else 0)
        assert result.cost == dijkstra_cost(grid, (0, 0), goal)
        stale += result.stats.stale_pops
    assert stale > 0
