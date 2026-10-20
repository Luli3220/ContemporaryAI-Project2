"""Public data models and counters; all counters reset per invocation."""
from dataclasses import dataclass, fields

Coord = tuple[int, int]


@dataclass
class AStarStats:
    generated: int = 0
    popped: int = 0
    expanded: int = 0
    stale_pops: int = 0
    max_frontier: int = 0
    runtime_ms: float = 0.0


@dataclass
class PathResult:
    found: bool
    path: list[Coord]
    cost: float
    stats: AStarStats


@dataclass
class GameStats:
    visited_nodes: int = 0
    evaluated_leaves: int = 0
    cutoff_events: int = 0
    pruned_siblings: int = 0
    ordering_probes: int = 0
    runtime_ms: float = 0.0


def reset_stats(stats: AStarStats | GameStats) -> None:
    for field in fields(stats):
        setattr(stats, field.name, 0.0 if field.name == 'runtime_ms' else 0)


class TreeNode:
    def __init__(self, value=None, children=None):
        self.value = value
        self.children = children if children is not None else []
