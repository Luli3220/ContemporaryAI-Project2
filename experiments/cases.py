"""Course inputs, never course outputs. Random instances use local RNGs."""
import random
from search_algorithms import TreeNode

MAZE = [list(row) for row in ('S..X.', '.X...', '.X.X.', '...XE', 'XX...')]
WEIGHTED = [['S', 1, 1, 8, 1], [1, 8, 3, 1, 1], [1, 8, 1, 8, 1],
            [1, 1, 1, 8, 1], [8, 8, 1, 1, 'E']]
TREASURE = [['A', 1, 1, 'X', 2, 1, 'T1'], [1, 'X', 6, 'X', 1, 'X', 1],
            [1, 1, 'T2', 1, 1, 1, 1], ['X', 1, 'X', 8, 'X', 1, 'X'],
            [1, 1, 1, 1, 'T3', 1, 1], [1, 'X', 9, 'X', 1, 'X', 1],
            ['T4', 1, 1, 'X', 1, 1, 'B']]
VALUES = {'T1': 9, 'T2': 6, 'T3': 7, 'T4': 7}


def course_tree():
    m1 = TreeNode(children=[TreeNode(3), TreeNode(5)])
    m2 = TreeNode(children=[TreeNode(6), TreeNode(9)])
    m3 = TreeNode(children=[TreeNode(1), TreeNode(2)])
    return TreeNode(children=[TreeNode(children=[m1, m2]), TreeNode(children=[m2, m3])])


def maze_case(n, density, seed):
    rng = random.Random(seed)
    grid = [['X' if rng.random() < density else '.' for _ in range(n)] for _ in range(n)]
    grid[0][0], grid[-1][-1] = 'S', 'E'
    return grid


def weighted_case(n, high, seed, obstacle=0, zero=False):
    rng = random.Random(seed)
    grid = []
    for _ in range(n):
        row = []
        for _ in range(n):
            if rng.random() < obstacle:
                row.append('X')
            else:
                row.append(8 if rng.random() < high else rng.choice((0, 1, 3) if zero else (1, 3)))
        grid.append(row)
    grid[0][0], grid[-1][-1] = 'S', 'E'
    return grid


def random_tree(branch, depth, seed):
    rng = random.Random(seed)

    def build(d):
        return TreeNode(rng.randint(-100, 100)) if d == 0 else TreeNode(children=[build(d - 1) for _ in range(branch)])
    return build(depth)
