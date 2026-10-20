"""One reopening A* implementation shared by all grid tasks."""
from collections.abc import Callable, Sequence
from heapq import heappop, heappush
from itertools import count
from math import inf, isfinite
from time import perf_counter
from .models import AStarStats, Coord, PathResult, reset_stats

Grid = Sequence[Sequence[int | str]]
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shape_of(grid: Grid) -> tuple[int, int]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('grid must be nonempty and rectangular')
    return len(grid), len(grid[0])


def check_coord(p: Coord, shape: tuple[int, int]) -> None:
    if (not isinstance(p, tuple) or len(p) != 2
            or any(type(x) is not int for x in p)
            or not (0 <= p[0] < shape[0] and 0 <= p[1] < shape[1])):
        raise ValueError(f'invalid or out-of-bounds coordinate: {p!r}')


def validate_endpoints(start: Coord, goal: Coord, grid: Grid) -> tuple[int, int]:
    shape = shape_of(grid)
    for p in (start, goal):
        check_coord(p, shape)
        if grid[p[0]][p[1]] == 'X':
            raise ValueError('endpoint cannot be blocked')
    for label, point in (('S', start), ('E', goal)):
        marked = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == label]
        if marked and marked != [point]:
            raise ValueError(f'{label} marker does not match endpoint or is duplicated')
    return shape


def astar_search(start: Coord, goal: Coord, shape: tuple[int, int],
                 is_blocked: Callable[[Coord], bool],
                 enter_cost: Callable[[Coord], float],
                 heuristic: Callable[[Coord, Coord], float], *,
                 stats: AStarStats | None = None) -> PathResult:
    """Requires finite nonnegative edge costs and an admissible h with h(goal)=0.

    The wrapper validates its complete grid; callbacks are validated as encountered.
    No permanent closed set: admissible inconsistent heuristics can reopen nodes.
    """
    if len(shape) != 2 or any(type(n) is not int or n <= 0 for n in shape):
        raise ValueError('shape must contain two positive integers')
    check_coord(start, shape)
    check_coord(goal, shape)
    if is_blocked(start) or is_blocked(goal):
        raise ValueError('endpoint cannot be blocked')
    st = stats if stats is not None else AStarStats()
    reset_stats(st)
    begin = perf_counter()
    serial = count()
    h = heuristic(start, goal)
    if not isfinite(h) or h < 0 or heuristic(goal, goal) != 0:
        raise ValueError('heuristic must be finite, nonnegative and zero at goal')
    heap = [(h, h, next(serial), 0, start)]
    best = {start: 0}
    parent: dict[Coord, Coord] = {}
    st.generated = st.max_frontier = 1
    while heap:
        _, _, _, g, p = heappop(heap)
        st.popped += 1
        if g != best[p]:
            st.stale_pops += 1
            continue
        if p == goal:
            path = [p]
            while path[-1] != start:
                path.append(parent[path[-1]])
            st.runtime_ms = (perf_counter() - begin) * 1000
            return PathResult(True, path[::-1], g, st)
        st.expanded += 1
        for dr, dc in DIRECTIONS:
            q = (p[0] + dr, p[1] + dc)
            if not (0 <= q[0] < shape[0] and 0 <= q[1] < shape[1]) or is_blocked(q):
                continue
            cost = enter_cost(q)
            if not isfinite(cost) or cost < 0:
                raise ValueError('edge costs must be finite and nonnegative')
            ng = g + cost
            if ng < best.get(q, inf):
                h = heuristic(q, goal)
                if not isfinite(h) or h < 0:
                    raise ValueError('heuristic must be finite and nonnegative')
                best[q], parent[q] = ng, p
                heappush(heap, (ng + h, h, next(serial), ng, q))
                st.generated += 1
                st.max_frontier = max(st.max_frontier, len(heap))
    st.runtime_ms = (perf_counter() - begin) * 1000
    return PathResult(False, [], inf, st)


def maze_search(start: Coord, goal: Coord, grid: Grid, *, heuristic: str = 'manhattan',
                stats: AStarStats | None = None) -> PathResult:
    shape = validate_endpoints(start, goal, grid)
    if any(v not in ('.', 'X', 'S', 'E') for row in grid for v in row):
        raise ValueError('maze allows only . X S E')
    if heuristic not in ('zero', 'manhattan'):
        raise ValueError('unknown heuristic')
    return astar_search(start, goal, shape, lambda p: grid[p[0]][p[1]] == 'X',
                        lambda p: 1, manhattan if heuristic == 'manhattan' else lambda a, b: 0,
                        stats=stats)


def solve_maze(start: Coord, goal: Coord, grid: list[list[str]]) -> list[Coord]:
    return maze_search(start, goal, grid).path


def weighted_search(start: Coord, goal: Coord, grid: Grid, *, heuristic: str = 'adjusted',
                    stats: AStarStats | None = None) -> PathResult:
    shape = validate_endpoints(start, goal, grid)
    numbers = []
    for row in grid:
        for v in row:
            if type(v) is int and v >= 0:
                numbers.append(v)
            elif not (isinstance(v, str) and v in ('S', 'E', 'X')):
                raise ValueError('terrain must be nonnegative integer, S, E or X')
    floor = min(numbers, default=0)
    if heuristic not in ('zero', 'adjusted'):
        raise ValueError('unknown heuristic')

    def cost(p: Coord) -> int:
        v = grid[p[0]][p[1]]
        return 0 if p == goal else (floor if v == 'S' else v)

    return astar_search(start, goal, shape, lambda p: grid[p[0]][p[1]] == 'X', cost,
                        lambda a, b: max(manhattan(a, b) - 1, 0) * floor
                        if heuristic == 'adjusted' else 0, stats=stats)


def solve_weighted_terrain(start: Coord, goal: Coord, grid: Grid) -> int:
    result = weighted_search(start, goal, grid)
    return int(result.cost) if result.found else -1
