"""Full minimax, deliberately independent from alpha-beta recursion."""
from math import isfinite
from time import perf_counter
from .models import GameStats, TreeNode, reset_stats


def leaf_value(node: TreeNode) -> int | float:
    if type(node.value) not in (int, float) or not isfinite(node.value):
        raise ValueError('leaf needs a finite numeric value')
    return node.value


def minimax(root: TreeNode, maximizing: bool = True, *, stats: GameStats | None = None) -> int | float:
    st = stats if stats is not None else GameStats()
    reset_stats(st)
    begin = perf_counter()

    def visit(node, is_max):
        st.visited_nodes += 1
        if not node.children:
            st.evaluated_leaves += 1
            return leaf_value(node)
        if node.value is not None:
            raise ValueError('internal node cannot have a leaf value')
        values = [visit(child, not is_max) for child in node.children]
        return max(values) if is_max else min(values)

    result = visit(root, maximizing)
    st.runtime_ms = (perf_counter() - begin) * 1000
    return result


def tree_from_json(data: dict, maximizing: bool = True) -> TreeNode:
    if 'tree_structure' in data:
        data = data['tree_structure']
    if ('is_maximizing_player' in data
            and (type(data['is_maximizing_player']) is not bool
                 or data['is_maximizing_player'] != maximizing)):
        raise ValueError('JSON player must alternate with depth')
    children = data.get('children', [])
    if not isinstance(children, list):
        raise ValueError('children must be a list')
    node = TreeNode(data.get('value'), [tree_from_json(c, not maximizing) for c in children])
    if not children:
        leaf_value(node)
    elif node.value is not None:
        raise ValueError('internal node cannot have value')
    return node
