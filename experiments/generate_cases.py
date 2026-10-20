"""Print or save any seeded instance, including a machine-readable course input set."""
import argparse
import json
from pathlib import Path
from .cases import MAZE, WEIGHTED, TREASURE, VALUES, maze_case, weighted_case


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', choices=['course', 'maze', 'weighted'], default='course')
    parser.add_argument('--size', type=int, default=20)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--density', type=float, default=.2)
    parser.add_argument('--high', type=float, default=.4)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = {'maze': MAZE, 'weighted': WEIGHTED, 'treasure': TREASURE, 'values': VALUES} if args.kind == 'course' else (
        maze_case(args.size, args.density, args.seed) if args.kind == 'maze' else
        weighted_case(args.size, args.high, args.seed, obstacle=args.density))
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content)
