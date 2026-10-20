import copy
import pytest
from search_algorithms import GameStats, TreeNode, minimax, alpha_beta, tree_from_json
from experiments.cases import course_tree, random_tree


def test_official_tree():
    root = course_tree()
    before = copy.deepcopy(root)
    mm, ab = GameStats(), GameStats()
    assert minimax(root, stats=mm) == alpha_beta(root, stats=ab) == 5
    assert (mm.visited_nodes, mm.evaluated_leaves) == (15, 8)
    # Only the first max2 prunes 9 after seeing 6 >= beta=5.
    # The second max2 has beta=inf, and max3 has beta=9: neither prunes.
    assert (ab.visited_nodes, ab.evaluated_leaves, ab.pruned_siblings) == (14, 7, 1)
    assert root.children[0].children[1] is root.children[1].children[0]
    assert minimax(root) == minimax(before)


@pytest.mark.parametrize('values', [[0], [-9, -3, -8], [0, 0, 0], [1.5, -2.3, 0]])
def test_leaf_values(values):
    root = TreeNode(children=[TreeNode(v) for v in values])
    for order in ('original', 'reverse', 'heuristic'):
        assert alpha_beta(root, order=order) == minimax(root) == max(values)
        assert alpha_beta(root, False, order=order) == min(values)
    assert alpha_beta(TreeNode(values[0])) == values[0]


def test_unbalanced_deep_tree():
    root = TreeNode(-4)
    for _ in range(150):
        root = TreeNode(children=[root])
    root = TreeNode(children=[root, TreeNode(2)])
    assert minimax(root) == alpha_beta(root) == 2


@pytest.mark.parametrize('node', [TreeNode(), TreeNode(float('nan')), TreeNode('x'),
    TreeNode(True), TreeNode(1, [TreeNode(2)])])
def test_invalid_nodes(node):
    for fn in (minimax, alpha_beta):
        with pytest.raises(ValueError):
            fn(node)


def test_json_adapter():
    root = tree_from_json({'tree_structure': {'is_maximizing_player': True,
        'children': [{'is_maximizing_player': False, 'children': [{'value': 0}, {'value': -1}]}]}})
    assert alpha_beta(root) == -1
    with pytest.raises(ValueError):
        tree_from_json({'is_maximizing_player': False, 'value': 1})
    with pytest.raises(ValueError):
        tree_from_json({'children': 'bad'})


@pytest.mark.parametrize('seed', range(100))
def test_random_tree(seed):
    root = random_tree(2 + seed % 3, 1 + seed % 5, seed)
    expected = minimax(root)
    for order in ('original', 'reverse', 'heuristic'):
        assert alpha_beta(root, order=order) == expected
