"""CampusMind academic operations REST API. Authentication is required before public deployment."""
from __future__ import annotations
import json
import csv
import io
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from . import storage
from .algorithms.conflicts import conflict_graph
from .algorithms.coloring import SearchLimitExceeded
from .algorithms.prerequisites import topological_plan
from .algorithms.budget import budget_optimize
from .service import validate_scenario, run_schedule, compare_algorithms


@asynccontextmanager
async def lifespan(_app:FastAPI):
    storage.initialize()
    yield

app=FastAPI(title='CampusMind',version='3.0.0',description='Academic scheduling and resource planning platform API',lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173',
             'http://localhost:5174','http://127.0.0.1:5174'],allow_credentials=False,allow_methods=['*'],allow_headers=['*'])

class ScheduleRequest(BaseModel):
    coloring:str='greedy'
    rooms:str='branch_bound'

class RoomRequest(BaseModel):
    assignment:str='branch_bound'

class BudgetRequest(BaseModel):
    method:str='dp'
    budget:int=Field(default=45,ge=0,le=2000)

class CompareRequest(BaseModel):
    budget:int=Field(default=45,ge=0,le=2000)


def scenario_or_404(scenario_id:str):
    s=storage.get_scenario(scenario_id)
    if s is None: raise HTTPException(404,'Scenario not found')
    return s


def record_and_return(s:dict,kind:str,algorithm:str,result:dict,summary:dict|None=None):
    summary=summary if summary is not None else result.get('summary',{})
    run_id=storage.record_run(s,kind,algorithm,summary,result)
    return {'run_id':run_id,'revision':s['revision'],**result}


@app.get('/api/health')
def health(): return {'ok':True,'name':'CampusMind','version':'3.0.0'}

@app.get('/api/scenarios')
def scenarios(): return storage.get_scenarios()

@app.get('/api/scenarios/{scenario_id}')
def scenario(scenario_id:str): return scenario_or_404(scenario_id)

@app.put('/api/scenarios/{scenario_id}')
def update_scenario(scenario_id:str,data:dict):
    scenario_or_404(scenario_id)
    try:validate_scenario(data)
    except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
    return storage.save_scenario(scenario_id,data)

@app.post('/api/scenarios/{scenario_id}/reset')
def reset_scenario(scenario_id:str):
    scenario_or_404(scenario_id)
    if scenario_id!='campus-demo':raise HTTPException(400,'Reset is only available for the bundled demo.')
    return storage.reset_scenario(scenario_id)

@app.get('/api/scenarios/{scenario_id}/conflicts')
def conflicts(scenario_id:str):
    s=scenario_or_404(scenario_id)
    return conflict_graph(s)

@app.post('/api/scenarios/{scenario_id}/schedule')
def schedule(scenario_id:str,request:ScheduleRequest):
    s=scenario_or_404(scenario_id)
    try:result=run_schedule(s,request.coloring,request.rooms)
    except (ValueError,SearchLimitExceeded) as e:raise HTTPException(422,str(e))
    return record_and_return(s,'schedule',f'{request.coloring} + {request.rooms}',result)

@app.post('/api/scenarios/{scenario_id}/rooms')
def rooms(scenario_id:str,request:RoomRequest):
    s=scenario_or_404(scenario_id)
    try:result=run_schedule(s,'greedy',request.assignment)
    except ValueError as e:raise HTTPException(422,str(e))
    result['kind']='rooms'
    return record_and_return(s,'rooms',request.assignment,result)

@app.post('/api/scenarios/{scenario_id}/prerequisites')
def prerequisites(scenario_id:str):
    s=scenario_or_404(scenario_id)
    try:result=topological_plan(s)
    except ValueError as e:raise HTTPException(422,str(e))
    return record_and_return(s,'prerequisites','Kahn Topological Sort',result,
                             {'feasible':result['feasible'],'levels':max(result['levels'].values(),default=-1)+1})

@app.post('/api/scenarios/{scenario_id}/budget')
def budget(scenario_id:str,request:BudgetRequest):
    s=scenario_or_404(scenario_id)
    try:result=budget_optimize(s['budget_items'],request.budget,request.method)
    except ValueError as e:raise HTTPException(422,str(e))
    return record_and_return(s,'budget',request.method,result,
                             {'value':result['total_value'],'budget_used':result['budget_used'],'optimal':result['optimal']})

@app.post('/api/scenarios/{scenario_id}/compare')
def compare(scenario_id:str,request:CompareRequest):
    s=scenario_or_404(scenario_id)
    try:result=compare_algorithms(s,request.budget)
    except (ValueError,SearchLimitExceeded) as e:raise HTTPException(422,str(e))
    return record_and_return(s,'benchmark','Comparative DAA Experiment',result)

@app.get('/api/scenarios/{scenario_id}/runs')
def runs(scenario_id:str):
    scenario_or_404(scenario_id)
    return storage.list_runs(scenario_id)

@app.get('/api/runs/{run_id}')
def run(run_id:int):
    result=storage.read_run(run_id)
    if result is None:raise HTTPException(404,'Run not found')
    return result

@app.get('/api/runs/{run_id}/export')
def export_run(run_id:int):
    result=storage.read_run(run_id)
    if result is None:raise HTTPException(404,'Run not found')
    return JSONResponse(result,headers={'Content-Disposition':f'attachment; filename="campusmind-run-{run_id}.json"'})


class PublishRequest(BaseModel):
    run_id: int = Field(gt=0)


@app.get('/api/scenarios/{scenario_id}/publication')
def publication(scenario_id: str):
    scenario_or_404(scenario_id)
    return storage.get_publication(scenario_id)


@app.post('/api/scenarios/{scenario_id}/publish')
def publish(scenario_id: str, request: PublishRequest):
    scenario_or_404(scenario_id)
    try:
        result=storage.publish_run(scenario_id,request.run_id)
    except ValueError as e:
        raise HTTPException(409,str(e))
    if result is None:
        raise HTTPException(404,'No completed timetable found for this run.')
    return result


@app.post('/api/scenarios/{scenario_id}/unpublish')
def unpublish(scenario_id: str):
    scenario_or_404(scenario_id)
    return storage.unpublish(scenario_id)


def _safe_csv_cell(value):
    text=str(value)
    return "'" + text if text and text.lstrip().startswith(('=','+','-','@','\t','\r')) else text


@app.get('/api/scenarios/{scenario_id}/published.csv')
def export_published(scenario_id: str):
    scenario_or_404(scenario_id)
    publication=storage.get_publication(scenario_id)
    if publication['status']!='published':
        raise HTTPException(404,'Publish a timetable before exporting the official version.')
    output=io.StringIO()
    writer=csv.writer(output)
    fields=('date','time','course_id','course_name','room_id','room_name','students','instructor')
    writer.writerow(('Date','Time','Course code','Course name','Room code','Room','Students','Instructor ID'))
    for entry in sorted(publication['schedule'], key=lambda x:(x['date'],x['time'],x['course_id'])):
        writer.writerow([_safe_csv_cell(entry.get(field,'')) for field in fields])
    return Response(content='\ufeff'+output.getvalue(),media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition':'attachment; filename="campusmind-official-timetable.csv"'})


# Faculty duty scheduling is only valid against a published, current timetable.
from .algorithms.invigilation import allocate_invigilators, override_duty, validate_duties


class DutyRequest(BaseModel):
    method: str = 'balanced'


class DutyOverride(BaseModel):
    run_id: int = Field(gt=0)
    course_id: str
    previous_faculty_id: str
    new_faculty_id: str


@app.get('/api/scenarios/{scenario_id}/duties/publication')
def duty_publication(scenario_id:str):
    scenario_or_404(scenario_id)
    return storage.get_duty_publication(scenario_id)


def current_official(scenario_id:str):
    official=storage.get_publication(scenario_id)
    if official['status']!='published' or official['stale']:
        raise HTTPException(409,'Publish a current examination timetable before scheduling invigilation duties.')
    return official


@app.post('/api/scenarios/{scenario_id}/duties/plan')
def plan_duties(scenario_id:str,request:DutyRequest):
    s=scenario_or_404(scenario_id)
    official=current_official(scenario_id)
    try:
        result=allocate_invigilators(s,official['schedule'],request.method)
    except ValueError as error:
        raise HTTPException(422,str(error))
    result['schedule_run_id']=official['run_id']
    return record_and_return(s,'invigilation',request.method,result)


@app.post('/api/scenarios/{scenario_id}/duties/override')
def change_duty(scenario_id:str,request:DutyOverride):
    s=scenario_or_404(scenario_id)
    official=current_official(scenario_id)
    old=storage.read_run(request.run_id)
    if old is None or old['scenario_id']!=scenario_id or old['kind']!='invigilation':
        raise HTTPException(404,'Duty plan not found.')
    if old['revision']!=s['revision'] or old['payload']['schedule_run_id']!=official['run_id']:
        raise HTTPException(409,'The duty plan is outdated. Generate a new plan.')
    try:
        assignments=override_duty(s,official['schedule'],old['payload']['assignments'],
                     request.course_id,request.previous_faculty_id,request.new_faculty_id)
    except ValueError as error:
        raise HTTPException(422,str(error))
    result={**old['payload'],'assignments':assignments,'algorithm':'manual adjustment',
            'status':'manually reviewed','summary':{**old['payload']['summary'],
                 'faculty_utilized':len(set(a['faculty_id'] for a in assignments))}}
    return record_and_return(s,'invigilation','manual adjustment',result)


@app.post('/api/scenarios/{scenario_id}/duties/publish')
def publish_duty_plan(scenario_id:str,request:PublishRequest):
    scenario_or_404(scenario_id)
    try:
        result=storage.publish_duties(scenario_id,request.run_id)
    except ValueError as error:
        raise HTTPException(409,str(error))
    if result is None:raise HTTPException(404,'Duty plan not found.')
    return result


@app.post('/api/scenarios/{scenario_id}/duties/unpublish')
def unpublish_duty_plan(scenario_id:str):
    scenario_or_404(scenario_id)
    return storage.unpublish_duties(scenario_id)


@app.get('/api/scenarios/{scenario_id}/duties/published.csv')
def export_duties(scenario_id:str):
    scenario_or_404(scenario_id)
    publication=storage.get_duty_publication(scenario_id)
    if publication['status']!='published':
        raise HTTPException(404,'Publish a duty roster first.')
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['Date','Time','Course code','Course','Room','Faculty ID','Faculty name'])
    for a in publication['assignments']:
        writer.writerow([_safe_csv_cell(a.get(key,'')) for key in
            ('date','time','course_id','course_name','room_name','faculty_id','faculty_name')])
    return Response(content='\ufeff'+output.getvalue(),media_type='text/csv; charset=utf-8',
        headers={'Content-Disposition':'attachment; filename="campusmind-invigilation-roster.csv"'})
