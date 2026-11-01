"""Kahn's algorithm for curricular prerequisite ordering and cycle identification."""
from __future__ import annotations
from collections import deque
import time


def topological_plan(scenario: dict) -> dict:
    begin = time.perf_counter_ns()
    ids = [c['id'] for c in scenario['courses']]
    adjacent = {cid: [] for cid in ids}
    indegree = {cid:0 for cid in ids}
    for edge in scenario.get('prerequisites', []):
        a,b=edge['before'],edge['after']
        if a not in adjacent or b not in adjacent:
            raise ValueError(f'Prerequisite references missing course: {a} -> {b}.')
        if b not in adjacent[a]:
            adjacent[a].append(b)
            indegree[b]+=1
    queue=deque(sorted(cid for cid in ids if indegree[cid]==0))
    order=[]
    level={cid:0 for cid in ids}
    trace=[]
    while queue:
        cid=queue.popleft()
        order.append(cid)
        trace.append({'type':'complete','message':f'Schedule prerequisite {cid} (level {level[cid]+1}).'})
        for after in sorted(adjacent[cid]):
            level[after]=max(level[after],level[cid]+1)
            indegree[after]-=1
            if indegree[after]==0:
                queue.append(after)
    has_cycle=len(order)<len(ids)
    cycle=[]
    if has_cycle:
        color={cid:0 for cid in ids}
        path=[]
        def dfs(u):
            color[u]=1
            path.append(u)
            for v in adjacent[u]:
                if color[v]==1:
                    return path[path.index(v):]+[v]
                if color[v]==0:
                    match=dfs(v)
                    if match:return match
            path.pop()
            color[u]=2
            return []
        for cid in ids:
            if color[cid]==0:
                cycle=dfs(cid)
                if cycle:break
    elapsed=(time.perf_counter_ns()-begin)/1e6
    return {'algorithm':"Kahn's Topological Sort",'feasible':not has_cycle,'order':order,
            'levels':{cid:level[cid] for cid in order},'cycle':cycle,
            'metrics':{'execution_ms':round(elapsed,4),'nodes_expanded':len(order),'edges_processed':sum(map(len,adjacent.values()))},
            'trace':trace}
