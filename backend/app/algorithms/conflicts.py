"""Build conflict graphs from actual overlapping student enrollments and instructors."""
from __future__ import annotations


def conflict_graph(scenario: dict) -> dict:
    courses = scenario['courses']
    nodes = [c['id'] for c in courses]
    adjacent = {c: set() for c in nodes}
    edges = []
    for i, left in enumerate(courses):
        for right in courses[i + 1:]:
            shared = sorted(set(left['students']) & set(right['students']))
            common_instructor = bool(left['instructor'] and left['instructor'] == right['instructor'])
            if shared or common_instructor:
                adjacent[left['id']].add(right['id'])
                adjacent[right['id']].add(left['id'])
                edges.append({
                    'source': left['id'], 'target': right['id'],
                    'shared_students': len(shared),
                    'same_instructor': common_instructor,
                    'reason': f'{len(shared)} shared student(s)' + (' + same instructor' if common_instructor else ''),
                })
    return {'nodes': nodes, 'edges': edges, 'adjacency': {n: sorted(v) for n, v in adjacent.items()},
            'degrees': {n: len(v) for n, v in adjacent.items()}, 'edge_count': len(edges)}


def check_coloring(graph: dict, colors: dict) -> bool:
    return all(a in colors and b in colors and colors[a] != colors[b]
               for a, nbrs in graph['adjacency'].items() for b in nbrs)
