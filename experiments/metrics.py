"""Measurement and CSV utilities kept outside production algorithms."""
import csv
import hashlib
import random
from dataclasses import asdict
from pathlib import Path
from statistics import median
from time import perf_counter

ORDER_SEED = 20261020
WARMUP_ROUNDS = 2


def shuffled_order(methods, case_id, round_id, *, phase='formal'):
    """A stable per-case/per-round seed, independent of Python's hash randomization."""
    digest = hashlib.sha256(f'{ORDER_SEED}:{case_id}:{phase}:{round_id}'.encode()).digest()
    seed = int.from_bytes(digest[:8], 'big')
    order = list(methods)
    random.Random(seed).shuffle(order)
    return order, seed


def measure_interleaved(calls, stats_type, config, repeats, decode, expected):
    """Warm every method, then time one invocation per method per shuffled round.

    Stats allocation, scheduling, decoding and oracle checks are outside wall_ms;
    the timed call includes input validation and the algorithm's own sorting.
    """
    if repeats <= 0 or not calls:
        raise ValueError('positive repeats and at least one method are required')
    for round_id in range(WARMUP_ROUNDS):
        order, _ = shuffled_order(calls, config['case_id'], round_id, phase='warmup')
        for method in order:
            calls[method](stats_type())
    rows = []
    for round_id in range(repeats):
        order, seed = shuffled_order(calls, config['case_id'], round_id)
        for position, method in enumerate(order):
            stats = stats_type()
            begin = perf_counter()
            result = calls[method](stats)
            wall = (perf_counter() - begin) * 1000
            output = decode(result)
            correct = output['optimal_cost'] == expected
            if not correct:
                raise AssertionError(f'oracle mismatch: {config}, {method}: {output} != {expected}')
            rows.append({**config, 'algorithm': method, 'repeat': round_id, 'round': round_id,
                'order_index': position, 'order_seed': seed, 'execution_order': '|'.join(order),
                **output, **asdict(stats), 'wall_ms': wall, 'correctness_passed': correct})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def measure(call, stats_type, config, repeats, decode, expected):
    call(stats_type())  # Untimed warm-up per input/method.
    rows = []
    for repeat in range(repeats):
        stats = stats_type()
        begin = perf_counter()
        result = call(stats)
        wall = (perf_counter() - begin) * 1000
        output = decode(result)
        correct = output['optimal_cost'] == expected
        if not correct:
            raise AssertionError(f'oracle mismatch: {config}: {output} != {expected}')
        rows.append({**config, 'repeat': repeat, **output, **asdict(stats),
                     'wall_ms': wall, 'correctness_passed': correct})
    return rows


def path_output(result):
    return {'optimal_cost': result.cost, 'path_steps': len(result.path) - 1 if result.found else -1,
            'reachable': result.found}


def game_output(result):
    if isinstance(result, dict):
        return {'optimal_cost': result['best_value'], 'best_target': result['best_target']}
    return {'optimal_cost': result}


def median_by_case(rows, metric):
    groups = {}
    for row in rows:
        groups.setdefault(row['case_id'], []).append(float(row[metric]))
    return [median(v) for v in groups.values()]
