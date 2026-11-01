"""Publishing safeguards and export tests for the administration workflow."""
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app import storage
from app.main import app


def test_draft_publish_and_export(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(storage,'DB_PATH',Path(folder)/'check.db')
        with TestClient(app) as client:
            initial=client.get('/api/scenarios/campus-demo/publication').json()
            assert initial['status']=='draft'
            assert client.get('/api/scenarios/campus-demo/published.csv').status_code==404
            schedule=client.post('/api/scenarios/campus-demo/schedule',json={'coloring':'backtracking','rooms':'branch_bound'}).json()
            assert len(schedule['schedule'])==9
            published=client.post('/api/scenarios/campus-demo/publish',json={'run_id':schedule['run_id']})
            assert published.status_code==200
            assert published.json()['entries']==9
            pub=client.get('/api/scenarios/campus-demo/publication').json()
            assert pub['status']=='published' and not pub['stale']
            assert pub['run_id']==schedule['run_id']
            exported=client.get('/api/scenarios/campus-demo/published.csv')
            assert exported.status_code==200 and exported.headers['content-type'].startswith('text/csv')
            assert 'Course code' in exported.text and 'CS501' in exported.text
            scenario=client.get('/api/scenarios/campus-demo').json()
            scenario['rooms'][0]['capacity']+=1
            assert client.put('/api/scenarios/campus-demo',json=scenario).status_code==200
            stale=client.get('/api/scenarios/campus-demo/publication').json()
            assert stale['status']=='published' and stale['stale']
            assert len(stale['schedule'])==9
            repeat=client.post('/api/scenarios/campus-demo/publish',json={'run_id':schedule['run_id']})
            assert repeat.status_code==409
            assert client.post('/api/scenarios/campus-demo/unpublish').json()['status']=='draft'
            assert client.get('/api/scenarios/campus-demo/published.csv').status_code==404


def test_cannot_publish_unscheduled_run(monkeypatch):
    with tempfile.TemporaryDirectory() as folder:
        monkeypatch.setattr(storage,'DB_PATH',Path(folder)/'check.db')
        with TestClient(app) as client:
            report=client.post('/api/scenarios/campus-demo/budget',json={'method':'dp','budget':15}).json()
            assert client.post('/api/scenarios/campus-demo/publish',json={'run_id':report['run_id']}).status_code==404
