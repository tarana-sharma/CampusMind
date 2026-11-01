"""Smoke and integration tests using a temporary SQLite database."""
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app import storage
from app.main import app


def test_api_end_to_end(monkeypatch):
    with tempfile.TemporaryDirectory() as temp:
        monkeypatch.setattr(storage, 'DB_PATH', Path(temp)/'test.db')
        with TestClient(app) as client:
            assert client.get('/api/health').json()['ok']
            scenario=client.get('/api/scenarios/campus-demo')
            assert scenario.status_code==200
            assert len(scenario.json()['courses'])==9
            graph=client.get('/api/scenarios/campus-demo/conflicts').json()
            assert graph['edge_count']>0
            sched=client.post('/api/scenarios/campus-demo/schedule',json={'coloring':'backtracking','rooms':'branch_bound'})
            assert sched.status_code==200,sched.text
            assert len(sched.json()['schedule'])==9
            run_id=sched.json()['run_id']
            assert client.get(f'/api/runs/{run_id}').json()['revision']==1
            assert client.get(f'/api/runs/{run_id}/export').status_code==200
            comp=client.post('/api/scenarios/campus-demo/compare',json={'budget':15})
            assert comp.status_code==200,comp.text
            assert comp.json()['counterexamples']['rooms']['greedy_cost']>comp.json()['counterexamples']['rooms']['exact_cost']
            assert comp.json()['counterexamples']['knapsack']['exact_value']>comp.json()['counterexamples']['knapsack']['greedy_value']
            topo=client.post('/api/scenarios/campus-demo/prerequisites')
            assert topo.status_code==200 and topo.json()['feasible']
            budget=client.post('/api/scenarios/campus-demo/budget',json={'method':'dp','budget':15})
            assert budget.status_code==200 and budget.json()['total_value']>0
            revision=scenario.json()['revision']
            updated=scenario.json()
            updated['rooms'][0]['capacity']+=1
            response=client.put('/api/scenarios/campus-demo',json=updated)
            assert response.status_code==200 and response.json()['revision']==revision+1
            assert client.post('/api/scenarios/campus-demo/reset').status_code==200
            assert len(client.get('/api/scenarios/campus-demo/runs').json())>=4


def test_api_rejects_invalid_scenario(monkeypatch):
    with tempfile.TemporaryDirectory() as temp:
        monkeypatch.setattr(storage, 'DB_PATH', Path(temp)/'test.db')
        with TestClient(app) as client:
            data=client.get('/api/scenarios/campus-demo').json()
            data['rooms'][0]['capacity']=-10
            resp=client.put('/api/scenarios/campus-demo',json=data)
            assert resp.status_code==422
