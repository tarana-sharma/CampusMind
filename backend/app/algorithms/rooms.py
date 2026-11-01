"""Optimize one-room-per-exam allocation, independently within each timeslot."""
from __future__ import annotations
import time


def allocation_cost(course: dict, room: dict) -> int | None:
    if len(course['students']) > room['capacity']:
        return None
    if not set(course.get('requires', [])).issubset(set(room.get('features', []))):
        return None
    unused = room['capacity'] - len(course['students'])
    # Discourage needlessly occupying specialist computer labs for theory exams.
    specialist_penalty = 12 if 'lab' in room.get('features', []) and 'lab' not in course.get('requires', []) else 0
    return unused + specialist_penalty


def assign_rooms(scenario: dict, colors: dict, method: str = 'branch_bound') -> dict:
    if method not in ('greedy', 'branch_bound'):
        raise ValueError('Room allocation must be greedy or branch_bound.')
    courses = {c['id']: c for c in scenario['courses']}
    rooms = scenario['rooms']
    grouped: dict[int, list[str]] = {}
    for course_id, slot in colors.items():
        grouped.setdefault(slot, []).append(course_id)
    begin = time.perf_counter_ns()
    metrics = {'nodes_expanded': 0, 'branches_pruned': 0}
    trace = []
    allocation = []
    for slot, course_ids in sorted(grouped.items()):
        options = {cid: sorted([(allocation_cost(courses[cid], room), room['id'])
                                 for room in rooms if allocation_cost(courses[cid], room) is not None])
                   for cid in course_ids}
        for cid, candidates in options.items():
            if not candidates:
                raise ValueError(f'No room fits {cid}: check its enrollment and required facilities.')
        # Minimum remaining options first gives stronger pruning and handles hard exams early.
        order = sorted(course_ids, key=lambda cid: (len(options[cid]), -len(courses[cid]['students']), cid))
        best: dict | None = None
        if method == 'greedy':
            used: set[str] = set()
            chosen = {}
            cost = 0
            for cid in order:
                metrics['nodes_expanded'] += 1
                option = next(((price, rid) for price, rid in options[cid] if rid not in used), None)
                if option is None:
                    raise ValueError('Greedy room allocation could not find a feasible matching. Try Branch and Bound.')
                price, rid = option
                used.add(rid)
                chosen[cid] = (rid, price)
                cost += price
                if len(trace) < 200:
                    trace.append({'type':'assign','message':f'Slot {slot+1}: {cid} assigned to {rid} (cost {price}).'})
            best = chosen
        else:
            incumbent = float('inf')
            # Admissible lower bound ignores room collisions for remaining exams.
            tail = [0] * (len(order) + 1)
            for j in range(len(order)-1, -1, -1):
                tail[j] = tail[j + 1] + options[order[j]][0][0]
            def search(i: int, used: set[str], partial: dict, cost: int):
                nonlocal incumbent, best
                metrics['nodes_expanded'] += 1
                if cost + tail[i] >= incumbent:
                    metrics['branches_pruned'] += 1
                    return
                if i == len(order):
                    incumbent = cost
                    best = partial.copy()
                    if len(trace) < 200:
                        trace.append({'type':'incumbent','message':f'Slot {slot+1}: improved allocation cost to {cost}.'})
                    return
                cid = order[i]
                for price, rid in options[cid]:
                    if rid in used:
                        metrics['branches_pruned'] += 1
                        continue
                    partial[cid] = (rid, price)
                    search(i + 1, used | {rid}, partial, cost + price)
                    partial.pop(cid)
            search(0, set(), {}, 0)
            if best is None:
                raise ValueError(f'Cannot assign distinct compatible rooms for slot {slot+1}. Increase capacity or add rooms.')
        for cid in course_ids:
            rid, cost = best[cid]
            allocation.append({'course_id': cid, 'room_id': rid, 'slot_index': slot,
                               'students': len(courses[cid]['students']), 'cost': cost})
    elapsed = (time.perf_counter_ns() - begin)/1e6
    return {'algorithm': 'Room Assignment — Branch and Bound' if method == 'branch_bound' else 'Room Assignment — Greedy',
            'assignments': sorted(allocation, key=lambda x:(x['slot_index'],x['room_id'])),
            'total_cost': sum(x['cost'] for x in allocation), 'optimal': method=='branch_bound',
            'metrics': {**metrics, 'execution_ms': round(elapsed,4)}, 'trace': trace}
