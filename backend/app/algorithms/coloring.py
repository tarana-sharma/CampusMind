"""Greedy DSATUR coloring and exact minimum-color backtracking solver."""
from __future__ import annotations
import time
from .conflicts import check_coloring


class SearchLimitExceeded(Exception):
    """Bound exact search to make the web application responsive."""


def greedy_dsatur(graph: dict) -> dict:
    adjacency = {k: set(v) for k, v in graph['adjacency'].items()}
    colors: dict[str, int] = {}
    trace = []
    begin = time.perf_counter_ns()
    while len(colors) < len(adjacency):
        uncolored = [n for n in adjacency if n not in colors]
        node = max(uncolored, key=lambda n: (len({colors[v] for v in adjacency[n] if v in colors}),
                                              len(adjacency[n]), n))
        forbidden = {colors[v] for v in adjacency[node] if v in colors}
        color = next(c for c in range(len(adjacency) + 1) if c not in forbidden)
        colors[node] = color
        trace.append({'type': 'assign', 'node': node, 'slot': color + 1,
                      'message': f'Placed {node} in slot {color + 1}; {len(forbidden)} neighboring colors unavailable.'})
    elapsed = (time.perf_counter_ns() - begin) / 1e6
    return {'algorithm': 'DSATUR Greedy Coloring', 'colors': colors,
            'slots_used': max(colors.values(), default=-1) + 1,
            'optimal': False, 'feasible': check_coloring(graph, colors),
            'metrics': {'execution_ms': round(elapsed, 4), 'nodes_expanded': len(colors), 'branches_pruned': 0},
            'trace': trace}


def backtracking_coloring(graph: dict, max_nodes: int = 400_000) -> dict:
    """Minimize used colors with an exact fixed-k feasibility test for k=1..greedy upper bound.

    Search is capped, never labels an unfinished search exact.  Coloring for >13 exams is
    deliberately disabled for the interactive demo, not claimed to be infeasible.
    """
    adj = {k: set(v) for k, v in graph['adjacency'].items()}
    if len(adj) > 13:
        raise ValueError('Exact graph coloring is limited to 13 courses. Choose DSATUR for larger datasets.')
    begin = time.perf_counter_ns()
    initial = greedy_dsatur(graph)
    ncolors = initial['slots_used']
    if not adj:
        return {**initial, 'algorithm': 'Exact Backtracking Coloring', 'optimal': True}
    metrics = {'nodes_expanded': 0, 'branches_pruned': 0}
    trace = []
    if ncolors == 1:
        return {**initial, 'algorithm': 'Exact Backtracking Coloring', 'optimal': True,
                'metrics': {**initial['metrics'], 'execution_ms': round((time.perf_counter_ns()-begin)/1e6,4)}}
    found = initial['colors']
    lower_bound = 2 if graph['edge_count'] else 1
    for k in range(lower_bound, ncolors):
        colors: dict[str, int] = {}
        def dfs() -> bool:
            metrics['nodes_expanded'] += 1
            if metrics['nodes_expanded'] > max_nodes:
                raise SearchLimitExceeded('Exact coloring reached its search budget. Try DSATUR or reduce courses.')
            if len(colors) == len(adj):
                return True
            unassigned = [v for v in adj if v not in colors]
            v = max(unassigned, key=lambda x: (len({colors[y] for y in adj[x] if y in colors}), len(adj[x]), x))
            forbidden = {colors[y] for y in adj[v] if y in colors}
            for color in range(k):
                if color in forbidden:
                    metrics['branches_pruned'] += 1
                    continue
                colors[v] = color
                if len(trace) < 300:
                    trace.append({'type': 'try', 'node': v, 'slot': color+1,
                                  'message': f'Try {v} in slot {color+1} using at most {k} slots.'})
                if dfs():
                    return True
                del colors[v]
            if len(trace) < 300:
                trace.append({'type': 'backtrack', 'node': v, 'message': f'Backtrack from {v}: no feasible color remains.'})
            return False
        if dfs():
            found = colors.copy()
            break
        if len(trace) < 300:
            trace.append({'type': 'bound', 'message': f'Proved that {k} slots are insufficient.'})
    result = {'algorithm': 'Exact Backtracking Coloring', 'colors': found,
              'slots_used': max(found.values(), default=-1) + 1, 'optimal': True,
              'feasible': check_coloring(graph, found),
              'metrics': {**metrics, 'execution_ms': round((time.perf_counter_ns()-begin)/1e6,4)},
              'trace': trace}
    return result
