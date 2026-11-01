"""Faculty directory and invigilation API integration tests."""
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app import storage
from app.main import app
from app.algorithms.invigilation import allocate_invigilators,validate_duties,override_duty
from app.service import run_schedule
import json


def test_full_faculty_duty_publication(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(storage,'DB_PATH',Path(folder)/'test.db')
        with TestClient(app) as c:
            s=c.get('/api/scenarios/campus-demo').json()
            assert len(s['instructors'])==8
            s['instructors'].append({'id':'T09','name':'Dr. New Faculty','email':'new@example.test',
                'department':'Computer Science','designation':'Lecturer','skills':['python'],
                'unavailable_slots':['T4'],'max_duties':2,'active':True})
            assert c.put('/api/scenarios/campus-demo',json=s).status_code==200
            schedule=c.post('/api/scenarios/campus-demo/schedule',json={'coloring':'backtracking','rooms':'branch_bound'})
            assert schedule.status_code==200,schedule.text
            rid=schedule.json()['run_id']
            assert c.post('/api/scenarios/campus-demo/duties/plan',json={'method':'quick'}).status_code==409
            assert c.post('/api/scenarios/campus-demo/publish',json={'run_id':rid}).status_code==200
            plan=c.post('/api/scenarios/campus-demo/duties/plan',json={'method':'balanced'})
            assert plan.status_code==200,plan.text
            body=plan.json()
            assert body['summary']['covered_exams']==9
            assert len(body['assignments'])==9
            assert body['status'] in ('optimal','feasible')
            assert c.post('/api/scenarios/campus-demo/duties/publish',json={'run_id':body['run_id']}).status_code==200
            duties=c.get('/api/scenarios/campus-demo/duties/publication').json()
            assert duties['status']=='published' and not duties['stale']
            assert len(duties['assignments'])==9
            exported=c.get('/api/scenarios/campus-demo/duties/published.csv')
            assert exported.status_code==200
            assert 'Faculty name' in exported.text
            s=c.get('/api/scenarios/campus-demo').json()
            s['instructors'][0]['max_duties']=1
            assert c.put('/api/scenarios/campus-demo',json=s).status_code==200
            assert c.get('/api/scenarios/campus-demo/duties/publication').json()['stale']
            assert c.post('/api/scenarios/campus-demo/duties/publish',json={'run_id':body['run_id']}).status_code==409
            assert c.post('/api/scenarios/campus-demo/duties/unpublish').status_code==200


def test_instructor_availability_own_course_and_overrides():
    s=json.loads(storage.SEED_PATH.read_text())
    schedule=run_schedule(s,'greedy','branch_bound')['schedule']
    plan=allocate_invigilators(s,schedule,'quick')
    validate_duties(s,schedule,plan['assignments'])
    for duty in plan['assignments']:
        member=next(t for t in s['instructors'] if t['id']==duty['faculty_id'])
        course=next(c for c in s['courses'] if c['id']==duty['course_id'])
        assert duty['timeslot_id'] not in member['unavailable_slots']
        assert duty['faculty_id'] != course['instructor']
    first=plan['assignments'][0]
    try:
        override_duty(s,schedule,plan['assignments'],first['course_id'],first['faculty_id'],
            next(c for c in s['courses'] if c['id']==first['course_id'])['instructor'])
        assert False,'Own-course assignment should not be accepted'
    except ValueError:
        pass


def test_reject_invalid_faculty_data(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(storage,'DB_PATH',Path(folder)/'test.db')
        with TestClient(app) as c:
            s=c.get('/api/scenarios/campus-demo').json()
            s['instructors'][0]['unavailable_slots']=['BAD-SLOT']
            assert c.put('/api/scenarios/campus-demo',json=s).status_code==422
            s=c.get('/api/scenarios/campus-demo').json()
            s['instructors'][0]['max_duties']=-3
            assert c.put('/api/scenarios/campus-demo',json=s).status_code==422
