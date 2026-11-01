"""Orchestrate syllabus algorithms without hiding any behind third-party solvers."""
from __future__ import annotations
from .algorithms.conflicts import conflict_graph
from .algorithms.coloring import greedy_dsatur, backtracking_coloring
from .algorithms.rooms import assign_rooms
from .algorithms.prerequisites import topological_plan
from .algorithms.budget import budget_optimize


def validate_scenario(s:dict) -> None:
    needed=('courses','rooms','timeslots','prerequisites','budget_items','instructors')
    for key in needed:
        if key not in s or not isinstance(s[key],list):
            raise ValueError(f'{key} must be a list.')
    if len(s['courses']) > 35 or len(s['rooms'])>20 or len(s['timeslots'])>25:
        raise ValueError('Demo editor supports at most 35 courses, 20 rooms and 25 timeslots.')
    for key in ('courses','rooms','timeslots'):
        ids=[x.get('id') for x in s[key]]
        if any(not isinstance(i,str) or not i.strip() for i in ids) or len(set(ids))!=len(ids):
            raise ValueError(f'{key} must have unique nonempty IDs.')
    slots={x['id'] for x in s['timeslots']}
    faculty_ids=[x.get('id') for x in s['instructors']]
    if len(set(faculty_ids))!=len(faculty_ids) or any(not isinstance(i,str) or not i.strip() for i in faculty_ids):
        raise ValueError('Faculty IDs must be nonempty and unique.')
    if len(s['instructors'])>100:
        raise ValueError('The local workspace supports at most 100 faculty records.')
    for t in s['instructors']:
        if not t.get('name') or not str(t['name']).strip():raise ValueError('Every faculty member needs a name.')
        if not isinstance(t.get('max_duties',3),int) or not 0<=t.get('max_duties',3)<=25:
            raise ValueError(f"{t['id']}: maximum duties must be between 0 and 25.")
        if not isinstance(t.get('unavailable_slots',[]),list) or any(x not in slots for x in t.get('unavailable_slots',[])):
            raise ValueError(f"{t['id']}: unavailable slots must be valid time-block IDs.")
        if not isinstance(t.get('skills',[]),list):raise ValueError('Faculty skills must be a list.')
        if not isinstance(t.get('active',True),bool):raise ValueError('Faculty active status must be a boolean.')
    pol=s.get('exam_policy',{})
    if not isinstance(pol,dict) or pol.get('invigilators_per_exam',1) not in (1,2):
        raise ValueError('Each exam must require one or two invigilators.')
    instructor_ids={x.get('id') for x in s['instructors']}
    for c in s['courses']:
        if not isinstance(c.get('students'),list) or len(c['students'])!=len(set(c['students'])):
            raise ValueError(f"{c['id']}: students must be a list of unique IDs.")
        if not all(isinstance(x,str) for x in c['students']):
            raise ValueError('Student IDs must be strings.')
        if c.get('instructor') not in instructor_ids:
            raise ValueError(f"{c['id']} has an unknown instructor.")
        if not isinstance(c.get('requires'),list):
            raise ValueError('Course requirements must be a list.')
    for slot in s['timeslots']:
        if not isinstance(slot.get('date'),str) or len(slot['date'])!=10 or not isinstance(slot.get('start'),str) or not isinstance(slot.get('end'),str) or slot['start']>=slot['end']:
            raise ValueError('Time blocks require a valid date and increasing start/end times.')
    from datetime import date
    from datetime import time as clock_time
    for slot in s['timeslots']:
        try:
            date.fromisoformat(slot['date'])
            clock_time.fromisoformat(slot['start'])
            clock_time.fromisoformat(slot['end'])
        except (ValueError,TypeError):
            raise ValueError('Invalid examination date or time format.')
    for i,x in enumerate(s['timeslots']):
        if any(x['date']==y['date'] and x['start']<y['end'] and y['start']<x['end'] for y in s['timeslots'][i+1:]):
            raise ValueError('Overlapping exam sessions on the same date are not allowed.')
    for room in s['rooms']:
        if not isinstance(room.get('capacity'),int) or room['capacity']<1:
            raise ValueError(f"Room {room['id']} must have a positive integer capacity.")
        if not isinstance(room.get('features'),list):
            raise ValueError('Room features must be a list.')
    ids={c['id'] for c in s['courses']}
    for pair in s['prerequisites']:
        if pair.get('before') not in ids or pair.get('after') not in ids:
            raise ValueError('All prerequisites must reference existing courses.')
    for item in s['budget_items']:
        if not isinstance(item.get('cost'),int) or item['cost']<=0 or not isinstance(item.get('value'),int) or item['value']<0:
            raise ValueError('Budget items must have positive integer costs and nonnegative integer values.')


def run_schedule(s:dict, coloring_method:str='greedy',room_method:str='branch_bound') -> dict:
    validate_scenario(s)
    graph=conflict_graph(s)
    if coloring_method not in ('greedy','backtracking'):
        raise ValueError('Choose greedy or backtracking coloring.')
    coloring=greedy_dsatur(graph) if coloring_method=='greedy' else backtracking_coloring(graph)
    if coloring['slots_used']>len(s['timeslots']):
        raise ValueError(f"Schedule needs {coloring['slots_used']} timeslots, but only {len(s['timeslots'])} exist.")
    rooms=assign_rooms(s,coloring['colors'],room_method)
    map_courses={c['id']:c for c in s['courses']}
    map_rooms={r['id']:r for r in s['rooms']}
    schedule=[]
    for a in rooms['assignments']:
        cid=a['course_id']
        slot=s['timeslots'][a['slot_index']]
        schedule.append({**a,'course_name':map_courses[cid]['name'],
                         'instructor':map_courses[cid]['instructor'],
                         'room_name':map_rooms[a['room_id']]['name'],
                         'timeslot_id':slot['id'],'date':slot['date'],
                         'time':f"{slot['start']} – {slot['end']}",'slot_label':slot['label']})
    if len(schedule)!=len(s['courses']):
        raise ValueError('Incomplete timetable: some exams were not assigned a room.')
    return {'kind':'schedule','coloring':coloring,'rooms':rooms,'schedule':schedule,
            'conflicts':{'edges':graph['edge_count'],'degrees':graph['degrees']},
            'summary':{'exams_scheduled':len(schedule),'slots_used':coloring['slots_used'],
                       'room_waste_cost':rooms['total_cost'],'student_clashes':0,
                       'coloring_method':coloring_method,'room_method':room_method,
                       'exact_coloring':coloring['optimal'],'exact_rooms':rooms['optimal']}}


def compare_algorithms(s:dict,budget:int=45) ->dict:
    validate_scenario(s)
    graph=conflict_graph(s)
    color_g=greedy_dsatur(graph)
    color_b=backtracking_coloring(graph) if len(s['courses'])<=13 else None
    room_g=assign_rooms(s,color_g['colors'],'greedy')
    room_b=assign_rooms(s,color_g['colors'],'branch_bound')
    kit_g=budget_optimize(s['budget_items'],budget,'greedy')
    kit_b=budget_optimize(s['budget_items'],budget,'dp')
    # Small reproducible counterexample where the local greedy choice is not globally optimal.
    challenge_courses = [(25,['projector']),(11,['projector']),(37,[]),(20,['lab']),(21,['lab'])]
    challenge_rooms = [(40,['lab']),(25,['lab','projector']),(60,['projector']),(40,['lab','projector']),(50,['projector']),(25,['lab','projector'])]
    sample={'courses':[{'id':f'C{i}','students':[f'S{j}' for j in range(count)],'requires':features}
                        for i,(count,features) in enumerate(challenge_courses)],
            'rooms':[{'id':f'R{i}','capacity':count,'features':features} for i,(count,features) in enumerate(challenge_rooms)]}
    challenge_colors={c['id']:0 for c in sample['courses']}
    hard_g=assign_rooms(sample,challenge_colors,'greedy')
    hard_b=assign_rooms(sample,challenge_colors,'branch_bound')
    counter_items=[{'id':'A','name':'Upgrade A','cost':10,'value':60},
                   {'id':'B','name':'Upgrade B','cost':20,'value':100},
                   {'id':'C','name':'Upgrade C','cost':30,'value':120}]
    return {'kind':'benchmark',
            'counterexamples':{'rooms':{'greedy_cost':hard_g['total_cost'],'exact_cost':hard_b['total_cost'],
                                         'description':'Five exams competing for six rooms in one time block.'},
                               'knapsack':{'greedy_value':budget_optimize(counter_items,50,'greedy')['total_value'],
                                           'exact_value':budget_optimize(counter_items,50,'dp')['total_value'],
                                           'description':'Three indivisible upgrades and a 50-unit budget.'}},
            'coloring':[color_g]+([color_b] if color_b else []),
            'room_allocation':[room_g,room_b],
            'budget':[kit_g,kit_b],
            'summary':{'conflict_edges':graph['edge_count'],'greedy_slots':color_g['slots_used'],
                       'exact_slots':color_b['slots_used'] if color_b else None,
                       'greedy_room_cost':room_g['total_cost'],'exact_room_cost':room_b['total_cost'],
                       'greedy_budget_value':kit_g['total_value'],'dp_budget_value':kit_b['total_value']}}
