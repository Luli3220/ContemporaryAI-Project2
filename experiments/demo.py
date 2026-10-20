import argparse
import json
from search_algorithms import (solve_maze, solve_weighted_terrain, weighted_search, minimax, alpha_beta,
    compute_distance_matrix, TreasureState, treasure_minimax, treasure_alpha_beta)
from .cases import MAZE, WEIGHTED, TREASURE, VALUES, course_tree


def official_results():
    matrix = compute_distance_matrix(TREASURE)
    return {'maze_path': solve_maze((0, 0), (3, 4), MAZE),
            'weighted_cost': solve_weighted_terrain((0, 0), (4, 4), WEIGHTED),
            'weighted_path': weighted_search((0, 0), (4, 4), WEIGHTED).path,
            'tree': {'minimax': minimax(course_tree()), 'alpha_beta': alpha_beta(course_tree())},
            'distance_matrix': matrix,
            'treasure': {str(h): {name: fn(TreasureState(), h, matrix, VALUES)
                for name, fn in [('minimax', treasure_minimax), ('alpha_beta', treasure_alpha_beta)]}
                for h in (2, 4)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['1', '2', '3', '4', 'all'], default='all')
    args = parser.parse_args()
    result = official_results()
    keys = {'1': ['maze_path'], '2': ['weighted_cost', 'weighted_path'], '3': ['tree'], '4': ['distance_matrix', 'treasure']}
    if args.task != 'all':
        result = {k: result[k] for k in keys[args.task]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
