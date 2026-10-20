"""Measurement and CSV utilities kept outside production algorithms."""
import csv
from dataclasses import asdict
from pathlib import Path
from statistics import median
from time import perf_counter


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
