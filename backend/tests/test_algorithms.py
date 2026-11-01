import json
from pathlib import Path
import copy
import pytest
from app.algorithms.conflicts import conflict_graph,check_coloring
from app.algorithms.coloring import greedy_dsatur,backtracking_coloring
from app.algorithms.rooms import assign_rooms
from app.algorithms.prerequisites import topological_plan
from app.algorithms.budget import budget_optimize
from app.service import run_schedule,validate_scenario,compare_algorithms

SEED=json.loads((Path(__file__).resolve().parents[2]/'data'/'campus_demo.json').read_text())


def test_valid_scenario():validate_scenario(SEED)

def test_conflict_graph_symmetric():
    graph=conflict_graph(SEED)
    assert graph['edge_count']>0
    for a,nbrs in graph['adjacency'].items():
        for b in nbrs:assert a in graph['adjacency'][b]

def test_greedy_feasible():
    g=conflict_graph(SEED)
    result=greedy_dsatur(g)
    assert result['feasible'] and check_coloring(g,result['colors'])
    assert result['slots_used']<=len(SEED['timeslots'])

def test_exact_coloring_not_worse_than_greedy():
    g=conflict_graph(SEED)
    exact=backtracking_coloring(g)
    greedy=greedy_dsatur(g)
    assert exact['optimal'] and check_coloring(g,exact['colors'])
    assert exact['slots_used']<=greedy['slots_used']

def test_exact_triangle_needs_three():
    g={'adjacency':{'A':['B','C'],'B':['A','C'],'C':['A','B']},'edge_count':3}
    assert backtracking_coloring(g)['slots_used']==3

def test_exact_path_needs_two():
    g={'adjacency':{'A':['B'],'B':['A','C'],'C':['B']},'edge_count':2}
    assert backtracking_coloring(g)['slots_used']==2

def test_rooms_exact_never_worse_on_same_color_assignment():
    colors=greedy_dsatur(conflict_graph(SEED))['colors']
    greedy=assign_rooms(SEED,colors,'greedy')
    optimal=assign_rooms(SEED,colors,'branch_bound')
    assert optimal['total_cost']<=greedy['total_cost']
    assert len(optimal['assignments'])==len(SEED['courses'])

def test_rooms_hard_constraint_capacity():
    s=copy.deepcopy(SEED)
    for room in s['rooms']:room['capacity']=2
    with pytest.raises(ValueError,match='No room fits'):
        assign_rooms(s,greedy_dsatur(conflict_graph(s))['colors'],'branch_bound')

def test_topological_order_respects_edges():
    result=topological_plan(SEED)
    assert result['feasible']
    positions={cid:i for i,cid in enumerate(result['order'])}
    for pair in SEED['prerequisites']:
        assert positions[pair['before']]<positions[pair['after']]

def test_topological_cycle_found():
    s=copy.deepcopy(SEED)
    s['prerequisites'].append({'before':'CS503','after':'CS501'})
    result=topological_plan(s)
    assert not result['feasible'] and result['cycle'][0]==result['cycle'][-1]

def test_budget_dp_beats_ratio_greedy_counterexample():
    items=[{'id':'x','name':'X','cost':10,'value':60},{'id':'y','name':'Y','cost':20,'value':100},
           {'id':'z','name':'Z','cost':30,'value':120}]
    assert budget_optimize(items,50,'dp')['total_value']==220
    assert budget_optimize(items,50,'greedy')['total_value']==160

def test_budget_respects_capacity():
    for algorithm in ('dp','greedy'):
        r=budget_optimize(SEED['budget_items'],45,algorithm)
        assert r['budget_used']<=45

def test_schedule_integrated():
    r=run_schedule(SEED)
    assert r['summary']['student_clashes']==0
    assert len(r['schedule'])==len(SEED['courses'])
    occupied={(a['slot_index'],a['room_id']) for a in r['schedule']}
    assert len(occupied)==len(r['schedule'])

def test_compare_experiment():
    r=compare_algorithms(SEED)
    assert r['summary']['exact_room_cost']<=r['summary']['greedy_room_cost']
    assert r['summary']['dp_budget_value']>=r['summary']['greedy_budget_value']
