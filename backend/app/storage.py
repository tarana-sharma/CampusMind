"""Small local SQLite store. Scenarios are versioned JSON snapshots for reproducibility."""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv('CAMPUSMIND_DB_PATH', str(ROOT / 'data' / 'campusmind.db')))
SEED_PATH = ROOT / 'data' / 'campus_demo.json'


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def initialize():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 1,
            data TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, scenario_id TEXT NOT NULL,
            revision INTEGER NOT NULL, kind TEXT NOT NULL, algorithm TEXT NOT NULL,
            summary TEXT NOT NULL, payload TEXT NOT NULL, scenario_snapshot TEXT NOT NULL,
            created_at TEXT NOT NULL)''')
        db.execute("""CREATE TABLE IF NOT EXISTS publications (scenario_id TEXT PRIMARY KEY, run_id INTEGER NOT NULL, revision INTEGER NOT NULL, snapshot TEXT NOT NULL, published_at TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS duty_publications (
            scenario_id TEXT PRIMARY KEY, run_id INTEGER NOT NULL, revision INTEGER NOT NULL,
            schedule_run_id INTEGER NOT NULL, snapshot TEXT NOT NULL, published_at TEXT NOT NULL)""")
        seed = json.loads(SEED_PATH.read_text(encoding='utf-8'))
        db.execute('INSERT OR IGNORE INTO scenarios(id,revision,data,updated_at) VALUES(?,?,?,?)',
                   (seed['id'], 1, json.dumps(seed), now()))


def get_scenario(scenario_id: str):
    with connect() as db:
        row = db.execute('SELECT * FROM scenarios WHERE id=?', (scenario_id,)).fetchone()
    if row is None:
        return None
    return {'revision': row['revision'], 'updated_at': row['updated_at'], **json.loads(row['data'])}


def get_scenarios():
    with connect() as db:
        rows=db.execute('SELECT * FROM scenarios ORDER BY updated_at DESC').fetchall()
    return [{'id':r['id'],'revision':r['revision'],'updated_at':r['updated_at'],
             'name':json.loads(r['data']).get('name')} for r in rows]


def save_scenario(scenario_id: str, data:dict):
    data={k:v for k,v in data.items() if k not in ('revision','updated_at')}
    data['id']=scenario_id
    with connect() as db:
        db.execute('UPDATE scenarios SET data=?,revision=revision+1,updated_at=? WHERE id=?',
                   (json.dumps(data),now(),scenario_id))
    return get_scenario(scenario_id)


def reset_scenario(scenario_id: str):
    data=json.loads(SEED_PATH.read_text(encoding='utf-8'))
    return save_scenario(scenario_id, data)


def record_run(scenario:dict, kind:str, algorithm:str, summary:dict, payload:dict):
    snapshot={k:v for k,v in scenario.items() if k not in ('revision','updated_at')}
    with connect() as db:
        cursor=db.execute('''INSERT INTO runs(scenario_id,revision,kind,algorithm,summary,payload,scenario_snapshot,created_at)
                             VALUES(?,?,?,?,?,?,?,?)''',
            (scenario['id'],scenario['revision'],kind,algorithm,json.dumps(summary),json.dumps(payload),json.dumps(snapshot),now()))
        run_id=cursor.lastrowid
    return run_id


def list_runs(scenario_id: str, limit: int = 50):
    with connect() as db:
        rows=db.execute('''SELECT id,scenario_id,revision,kind,algorithm,summary,created_at
                           FROM runs WHERE scenario_id=? ORDER BY id DESC LIMIT ?''',(scenario_id,limit)).fetchall()
    return [{**dict(row),'summary':json.loads(row['summary'])} for row in rows]


def read_run(run_id: int):
    with connect() as db:
        row=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
    if row is None:return None
    return {**dict(row),'summary':json.loads(row['summary']),
            'payload':json.loads(row['payload']),'scenario_snapshot':json.loads(row['scenario_snapshot'])}


def publish_run(scenario_id: str, run_id: int):
    """Save an immutable timetable snapshot only for the current scenario revision."""
    with connect() as db:
        row = db.execute('SELECT * FROM runs WHERE id=? AND scenario_id=? AND kind=?',
                         (run_id, scenario_id, 'schedule')).fetchone()
        if row is None:
            return None
        current = db.execute('SELECT revision FROM scenarios WHERE id=?', (scenario_id,)).fetchone()
        if current is None or row['revision'] != current['revision']:
            raise ValueError('This schedule is outdated. Generate a new timetable before publishing.')
        snapshot=json.loads(row['payload'])
        timestamp=now()
        db.execute("""INSERT INTO publications(scenario_id,run_id,revision,snapshot,published_at)
                      VALUES(?,?,?,?,?) ON CONFLICT(scenario_id) DO UPDATE SET
                      run_id=excluded.run_id,revision=excluded.revision,
                      snapshot=excluded.snapshot,published_at=excluded.published_at""",
                   (scenario_id,run_id,row['revision'],json.dumps(snapshot),timestamp))
        return {'status':'published','run_id':run_id,'revision':row['revision'],
                'published_at':timestamp,'entries':len(snapshot.get('schedule',[]))}


def get_publication(scenario_id: str):
    with connect() as db:
        row=db.execute('SELECT * FROM publications WHERE scenario_id=?',(scenario_id,)).fetchone()
        current=db.execute('SELECT revision FROM scenarios WHERE id=?',(scenario_id,)).fetchone()
    if row is None:
        return {'status':'draft','run_id':None,'revision':None,'entries':0,'stale':False}
    data=dict(row)
    result=json.loads(data.pop('snapshot'))
    return {'status':'published','run_id':data['run_id'],'revision':data['revision'],
            'published_at':data['published_at'],'entries':len(result.get('schedule',[])),
            'stale':not current or current['revision'] != data['revision'],
            'schedule':result.get('schedule',[])}


def unpublish(scenario_id: str):
    with connect() as db:
        db.execute('DELETE FROM publications WHERE scenario_id=?',(scenario_id,))
        db.execute('DELETE FROM duty_publications WHERE scenario_id=?',(scenario_id,))
    return {'status':'draft','run_id':None,'revision':None,'entries':0,'stale':False}


def get_duty_publication(scenario_id:str):
    with connect() as db:
        duty=db.execute('SELECT * FROM duty_publications WHERE scenario_id=?',(scenario_id,)).fetchone()
        current=db.execute('SELECT revision FROM scenarios WHERE id=?',(scenario_id,)).fetchone()
        timetable=db.execute('SELECT run_id FROM publications WHERE scenario_id=?',(scenario_id,)).fetchone()
    if duty is None:
        return {'status':'draft','run_id':None,'schedule_run_id':None,'entries':0,'stale':False,'assignments':[]}
    assignments=json.loads(duty['snapshot'])
    stale=(current is None or duty['revision']!=current['revision'] or
           timetable is None or duty['schedule_run_id']!=timetable['run_id'])
    return {'status':'published','run_id':duty['run_id'],'schedule_run_id':duty['schedule_run_id'],
            'revision':duty['revision'],'published_at':duty['published_at'],
            'entries':len(assignments),'stale':stale,'assignments':assignments}


def publish_duties(scenario_id:str,run_id:int):
    with connect() as db:
        run=db.execute('SELECT * FROM runs WHERE id=? AND scenario_id=? AND kind=?',
                       (run_id,scenario_id,'invigilation')).fetchone()
        if run is None:return None
        current=db.execute('SELECT revision FROM scenarios WHERE id=?',(scenario_id,)).fetchone()
        official=db.execute('SELECT run_id,revision FROM publications WHERE scenario_id=?',(scenario_id,)).fetchone()
        if not current or not official or current['revision']!=run['revision'] or official['revision']!=current['revision']:
            raise ValueError('The timetable or source data changed. Refresh the plan before publishing duties.')
        result=json.loads(run['payload'])
        if result['schedule_run_id']!=official['run_id']:
            raise ValueError('These duties belong to a different timetable. Generate a new plan.')
        stamp=now()
        db.execute('''INSERT INTO duty_publications(scenario_id,run_id,revision,schedule_run_id,snapshot,published_at)
                      VALUES(?,?,?,?,?,?) ON CONFLICT(scenario_id) DO UPDATE SET
                      run_id=excluded.run_id,revision=excluded.revision,
                      schedule_run_id=excluded.schedule_run_id,snapshot=excluded.snapshot,published_at=excluded.published_at''',
                   (scenario_id,run_id,run['revision'],result['schedule_run_id'],json.dumps(result['assignments']),stamp))
    return {'status':'published','entries':len(result['assignments']),'run_id':run_id,'published_at':stamp}


def unpublish_duties(scenario_id:str):
    with connect() as db:
        db.execute('DELETE FROM duty_publications WHERE scenario_id=?',(scenario_id,))
    return {'status':'draft','entries':0,'assignments':[],'stale':False}
