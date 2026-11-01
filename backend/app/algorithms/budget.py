"""Select indivisible examination readiness upgrades: 0/1 knapsack DP vs ratio greedy."""
from __future__ import annotations
import time


def budget_optimize(items: list[dict], capacity: int, method: str = 'dp') -> dict:
    if not isinstance(capacity, int) or not 0<=capacity<=2000:
        raise ValueError('Budget must be an integer between 0 and 2000 units.')
    if method not in ('dp', 'greedy'):
        raise ValueError('Choose dp or greedy.')
    if any(item['cost']<=0 or item['value']<0 for item in items):
        raise ValueError('All item costs must be positive and values nonnegative.')
    start=time.perf_counter_ns()
    trace=[]
    if method=='greedy':
        selected=[]
        used=0
        for item in sorted(items,key=lambda x:(-x['value']/x['cost'],-x['value'],x['id'])):
            if used+item['cost']<=capacity:
                selected.append(item)
                used+=item['cost']
                trace.append({'type':'select','message':f"Selected {item['name']} by value-to-cost ratio."})
        states=len(items)
    else:
        n=len(items)
        dp=[[0]*(capacity+1) for _ in range(n+1)]
        for i in range(1,n+1):
            item=items[i-1]
            for c in range(capacity+1):
                dp[i][c]=dp[i-1][c]
                if item['cost']<=c:
                    dp[i][c]=max(dp[i][c],dp[i-1][c-item['cost']]+item['value'])
        selected=[]
        c=capacity
        for i in range(n,0,-1):
            if dp[i][c]!=dp[i-1][c]:
                item=items[i-1]
                selected.append(item)
                c-=item['cost']
                trace.append({'type':'select','message':f"Backtracked DP table: include {item['name']}."})
        selected.reverse()
        used=sum(x['cost'] for x in selected)
        states=(n+1)*(capacity+1)
    return {'algorithm':'0/1 Knapsack — Dynamic Programming' if method=='dp' else 'Value/Cost Greedy Heuristic',
            'selected':selected,'budget':capacity,'budget_used':used,
            'total_value':sum(x['value'] for x in selected),'optimal':method=='dp',
            'metrics':{'execution_ms':round((time.perf_counter_ns()-start)/1e6,4),'states_evaluated':states},'trace':trace}
