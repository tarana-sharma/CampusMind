"""Constraint-aware invigilation duty assignment, using Greedy + bounded Branch and Bound.

Constraints: distinct invigilators per exam/slot, staff availability, max duties,
optional own-course exclusions. Objective: workload fairness plus modest same-department
preference. Every result is verified before being returned.
"""
from __future__ import annotations
import time
from collections import defaultdict


def validate_duties(scenario: dict, exams: list[dict], duties: list[dict]) -> None:
    teachers={f['id']:f for f in scenario['instructors']}
    courses={c['id']:c for c in scenario['courses']}
    exams_by_id={e['course_id']:e for e in exams}
    policy=scenario.get('exam_policy', {})
    coverage=int(policy.get('invigilators_per_exam',1))
    if len(duties)!=len(exams)*coverage:
        raise ValueError('Every examination must have the required number of invigilators.')
    per_exam=defaultdict(set)
    per_slot=defaultdict(set)
    loads=defaultdict(int)
    for duty in duties:
        cid=duty['course_id']; fid=duty['faculty_id']
        if cid not in exams_by_id or fid not in teachers:
            raise ValueError('Duty references an unknown exam or faculty member.')
        exam=exams_by_id[cid]; member=teachers[fid]
        slot=exam['timeslot_id']
        if not member.get('active',True): raise ValueError(f'{fid} is not active.')
        if slot in member.get('unavailable_slots',[]): raise ValueError(f'{fid} unavailable for {slot}.')
        if policy.get('prevent_own_course',True) and courses[cid]['instructor']==fid:
            raise ValueError(f'{fid} cannot supervise their own course {cid}.')
        if fid in per_slot[slot]: raise ValueError(f'{fid} has overlapping duties in {slot}.')
        if fid in per_exam[cid]: raise ValueError('Duplicate invigilator on one exam.')
        per_exam[cid].add(fid); per_slot[slot].add(fid); loads[fid]+=1
        if loads[fid]>member.get('max_duties',3): raise ValueError(f'{fid} exceeds maximum duties.')
    if any(len(per_exam[exam['course_id']])!=coverage for exam in exams):
        raise ValueError('Some exams do not have sufficient coverage.')


def allocate_invigilators(scenario: dict, exams: list[dict], method: str='balanced') -> dict:
    if method not in ('balanced','quick'): raise ValueError('Choose balanced or quick planning.')
    if not exams: raise ValueError('Publish a nonempty timetable before assigning duties.')
    start=time.perf_counter_ns()
    courses={c['id']:c for c in scenario['courses']}
    teachers={t['id']:t for t in scenario['instructors'] if t.get('active',True)}
    policy=scenario.get('exam_policy',{})
    required=int(policy.get('invigilators_per_exam',1))
    if required<1 or required>2: raise ValueError('One or two invigilators per examination are supported.')
    # Each coverage requirement is a task; repeated exams in the same slot must use distinct people.
    tasks=[(e,idx) for e in exams for idx in range(required)]
    candidates={e['course_id']:[fid for fid,t in teachers.items()
                if e['timeslot_id'] not in t.get('unavailable_slots',[])
                and (not policy.get('prevent_own_course',True) or fid!=courses[e['course_id']]['instructor'])
                and t.get('max_duties',3)>0] for e in exams}
    for e in exams:
        if len(candidates[e['course_id']])<required:
            raise ValueError(f"Not enough eligible faculty for {e['course_id']}. Check availability and rules.")
    # Fewest candidates first; large simultaneous blocks receive priority.
    slot_load=defaultdict(int)
    for e,_ in tasks: slot_load[e['timeslot_id']]+=1
    tasks.sort(key=lambda task:(len(candidates[task[0]['course_id']]),-slot_load[task[0]['timeslot_id']],task[0]['slot_index'],task[0]['course_id'],task[1]))

    def incremental(exam,fid,load):
        member=teachers[fid]; same=member.get('department')==courses[exam['course_id']].get('department')
        return 3*load+1+(0 if same else 2)

    def eligible(exam,fid,load,slot_used,exam_used):
        return (load[fid]<teachers[fid].get('max_duties',3)
                and fid not in slot_used[exam['timeslot_id']]
                and fid not in exam_used[exam['course_id']])

    def greedy():
        loads=defaultdict(int); slot_used=defaultdict(set); exam_used=defaultdict(set); selected=[]; total=0
        for exam,_ in tasks:
            poss=sorted((incremental(exam,fid,loads[fid]),fid) for fid in candidates[exam['course_id']]
                        if eligible(exam,fid,loads,slot_used,exam_used))
            if not poss:return None
            cost,fid=poss[0];total+=cost;selected.append((exam['course_id'],fid))
            loads[fid]+=1;slot_used[exam['timeslot_id']].add(fid);exam_used[exam['course_id']].add(fid)
        return (total,selected)

    incumbent=greedy(); best=incumbent
    expanded=0; pruned=0; limit=120000; exhausted=False
    if method=='balanced':
        loads=defaultdict(int);slot_used=defaultdict(set);exam_used=defaultdict(set);partial=[]
        mismatch_bounds=[min(0 if teachers[fid].get('department')==courses[exam['course_id']].get('department') else 2
                             for fid in candidates[exam['course_id']]) for exam,_ in tasks]
        mismatch_tail=[0]*(len(tasks)+1)
        for i in range(len(tasks)-1,-1,-1): mismatch_tail[i]=mismatch_tail[i+1]+mismatch_bounds[i]

        def load_lower_bound(remaining:int):
            # Relax slot, exam and availability restrictions: this can only underestimate cost.
            possible=sorted((loads[fid] for fid in teachers))
            penalty=0
            for _ in range(remaining):
                idx=min(range(len(possible)),key=lambda i:possible[i])
                penalty+=3*possible[idx]
                possible[idx]+=1
            return penalty

        def search(pos:int,cost:int):
            nonlocal expanded,pruned,best,exhausted
            if expanded>=limit:
                exhausted=True;return
            expanded+=1
            if pos==len(tasks):
                if best is None or cost<best[0]:best=(cost,partial.copy())
                return
            # Admissible relaxation of unavoidable workload, coverage and department costs.
            remaining=len(tasks)-pos
            lower=cost+remaining+mismatch_tail[pos]+load_lower_bound(remaining)
            if best is not None and lower>=best[0]:
                pruned+=1;return
            exam,_=tasks[pos]
            opts=sorted((incremental(exam,fid,loads[fid]),fid) for fid in candidates[exam['course_id']]
                        if eligible(exam,fid,loads,slot_used,exam_used))
            if not opts:
                pruned+=1;return
            for increment,fid in opts:
                if best is not None and cost+increment>=best[0]:
                    pruned+=1;continue
                loads[fid]+=1;slot_used[exam['timeslot_id']].add(fid);exam_used[exam['course_id']].add(fid)
                partial.append((exam['course_id'],fid))
                search(pos+1,cost+increment)
                partial.pop();loads[fid]-=1;slot_used[exam['timeslot_id']].remove(fid);exam_used[exam['course_id']].remove(fid)
                if exhausted:return
        search(0,0)
    else:
        expanded=len(tasks)
    if best is None:
        raise ValueError('No feasible invigilation plan. Add faculty, increase duty limits, or relax availability restrictions.')
    assignments=[]
    exam_by_id={e['course_id']:e for e in exams}
    for cid,fid in best[1]:
        e=exam_by_id[cid]
        assignments.append({'course_id':cid,'course_name':e['course_name'],'faculty_id':fid,
                            'faculty_name':teachers[fid]['name'],'room_id':e['room_id'],
                            'room_name':e['room_name'],'timeslot_id':e['timeslot_id'],
                            'date':e['date'],'time':e['time'],'slot_index':e['slot_index']})
    assignments.sort(key=lambda a:(a['slot_index'],a['room_id'],a['faculty_id']))
    validate_duties(scenario,exams,assignments)
    load_counts={f['id']:sum(a['faculty_id']==f['id'] for a in assignments) for f in scenario['instructors']}
    return {'kind':'invigilation','algorithm':method,'assignments':assignments,'total_cost':best[0],
            'status':'optimal' if method=='balanced' and not exhausted else 'feasible',
            'summary':{'covered_exams':len(exams),'total_duties':len(assignments),
                       'faculty_utilized':sum(v>0 for v in load_counts.values()),
                       'workload_min':min(load_counts.values(),default=0),'workload_max':max(load_counts.values(),default=0)},
            'loads':load_counts,'metrics':{'nodes_expanded':expanded,'branches_pruned':pruned,
                   'search_limit_reached':exhausted,'execution_ms':round((time.perf_counter_ns()-start)/1e6,4)}}


def override_duty(scenario:dict,exams:list[dict],assignments:list[dict],course_id:str,previous_faculty:str,replacement:str) -> list[dict]:
    revised=[dict(a) for a in assignments]
    target=next((a for a in revised if a['course_id']==course_id and a['faculty_id']==previous_faculty),None)
    if target is None: raise ValueError('The selected duty no longer exists in the draft.')
    person=next((f for f in scenario['instructors'] if f['id']==replacement),None)
    if person is None:raise ValueError('The replacement faculty member does not exist.')
    target['faculty_id']=replacement
    target['faculty_name']=person['name']
    validate_duties(scenario,exams,revised)
    return revised
