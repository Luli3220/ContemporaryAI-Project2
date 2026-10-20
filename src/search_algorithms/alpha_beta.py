"""Fail-soft alpha-beta. No bound values are cached as exact results."""
from math import inf
from time import perf_counter
from .models import GameStats, TreeNode, reset_stats
from .minimax import leaf_value


def alpha_beta(root: TreeNode, maximizing: bool = True, *, order: str = 'original',
               stats: GameStats | None = None) -> int | float:
    if order not in ('original', 'reverse', 'heuristic'):
        raise ValueError('unknown order')
    st = stats if stats is not None else GameStats()
    reset_stats(st)
    begin = perf_counter()

    def estimate(node):
        # A cheap, imperfect estimate, not an oracle minimax sort.
        while node.children:
            st.ordering_probes += 1
            node = node.children[0]
        st.ordering_probes += 1
        return leaf_value(node)

    def visit(node, is_max, alpha, beta):
        st.visited_nodes += 1
        if not node.children:
            st.evaluated_leaves += 1
            return leaf_value(node)
        if node.value is not None:
            raise ValueError('internal node cannot have a leaf value')
        children = node.children
        if order == 'reverse':
            children = children[::-1]
        elif order == 'heuristic':
            children = sorted(children, key=estimate, reverse=is_max)
        best = -inf if is_max else inf
        for i, child in enumerate(children):
            value = visit(child, not is_max, alpha, beta)
            best = max(best, value) if is_max else min(best, value)
            if is_max:
                alpha = max(alpha, best)
            else:
                beta = min(beta, best)
            remaining = len(children) - i - 1
            if alpha >= beta and remaining:
                st.cutoff_events += 1
                st.pruned_siblings += remaining
                break
        return best

    result = visit(root, maximizing, -inf, inf)
    st.runtime_ms = (perf_counter() - begin) * 1000
    return result
