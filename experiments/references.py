"""Independent oracles: no calls to production search/transition functions."""
from collections import deque
from heapq import heappop, heappush
from itertools import permutations
from math import inf


def bfs_distance(grid, start, goal):
    queue, seen = deque([(start, 0)]), {start}
    while queue:
        (r, c), d = queue.popleft()
        if (r, c) == goal:
            return d
        for q in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if (0 <= q[0] < len(grid) and 0 <= q[1] < len(grid[0])
                    and grid[q[0]][q[1]] != 'X' and q not in seen):
                seen.add(q)
                queue.append((q, d + 1))
    return inf


def dijkstra_cost(grid, start, goal, *, free_goal=True):
    nums = [v for row in grid for v in row if type(v) is int]
    s_cost = min(nums, default=0)
    queue, distances, closed = [(0, start)], {start: 0}, set()
    while queue:
        d, p = heappop(queue)
        if p in closed:
            continue
        closed.add(p)
        if p == goal:
            return d
        for r, c in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c] == 'X':
                continue
            v = grid[r][c]
            cost = (v if type(v) is int else (s_cost if v == 'S' else 1))
            if free_goal and (r, c) == goal:
                cost = 0
            candidate = d + cost
            if candidate < distances.get((r, c), inf):
                distances[(r, c)] = candidate
                heappush(queue, (candidate, (r, c)))
    return inf


def enumerated_game(matrix, values, depth, state=None):
    """Enumerate all prefixes, score each directly, then back up prefix trie."""
    if state is None:
        pa, pb, sa, sb, player, remaining = 'A', 'B', 0, 0, 'A', sorted(values)
    else:
        pa, pb, sa, sb, player, remaining = (state.pos_a, state.pos_b, state.score_a,
            state.score_b, state.current_player, sorted(state.remaining))
    horizon = min(depth, len(remaining))
    if horizon == 0:
        return sa - sb, {}
    leaves = {}
    for seq in permutations(remaining, horizon):
        a, b, x, y, turn = pa, pb, sa, sb, player
        for t in seq:
            if turn == 'A':
                x += values[t] - matrix[a][t]
                a = t
            else:
                y += values[t] - matrix[b][t]
                b = t
            turn = 'B' if turn == 'A' else 'A'
        leaves[seq] = x - y
    current, root_values = leaves, {}
    for level in range(horizon - 1, -1, -1):
        grouped = {}
        for seq, value in current.items():
            grouped.setdefault(seq[:-1], []).append(value)
        max_turn = (player == 'A') == (level % 2 == 0)
        if level == 0:
            root_values = {seq[0]: value for seq, value in current.items()}
        current = {prefix: (max(v) if max_turn else min(v)) for prefix, v in grouped.items()}
    return current[()], root_values
