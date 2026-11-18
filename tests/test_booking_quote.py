"""Binding owned records must preserve execution and hidden-work boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from disclosure_causality.environment import make_world, schedule, account_charge
from disclosure_causality.runner import packet, write
from disclosure_causality.booking_quote import quote_booking


def fixture(n=4,funds='joint',liability='office',vendor=False,protocol=11):
    world=make_world(n=n,protocol=protocol,funds=funds,liability=liability,audience='team',objective='client')
    names=list(world['projects']);contractor=world['focal'] if vendor else None
    holds={p:j['deadline'] for p,j in world['projects'].items()}
    plan=dict(internal_order=[p for p in world['order'] if p!=contractor],office_contractor_for=contractor,
        hours={p:j['actual_hours'] for p,j in world['projects'].items()},updates={p:{'message':'Dispatch plan published.','attachments':[]} for p in names})
    requests={p:dict(appointment_hold=h,message='',attachments=[]) for p,h in holds.items()}
    run=dict(world=world,stage='commit',outputs={'request':requests,'allocate':{'scheduler':plan}},messages=[],config={})
    return run,holds,plan


@pytest.mark.parametrize('n',[4,8,16,32])
@pytest.mark.parametrize('funds',['joint','protected'])
@pytest.mark.parametrize('liability',['office','project'])
@pytest.mark.parametrize('vendor',[False,True])
def test_bound_quotes_match_real_execution(n,funds,liability,vendor):
    run,holds,plan=fixture(n,funds,liability,vendor)
    world=run['world'];base={p:{'acceptance_slot':h} for p,h in holds.items()}
    native=schedule(world,plan,base,holds)
    for actor in (world['focal'],world['order'][1]):
        visible=packet(run,actor);original=deepcopy(visible)
        q=quote_booking(visible,{'assumed_finish_hour':native['jobs'][actor]['finish']})
        assert visible==original
        assert q['bound_records']['provisional_hold']==holds[actor]
        for row in q['choices']:
            choices=deepcopy(base);choices[actor]={'acceptance_slot':row['acceptance_slot']}
            actual=schedule(world,plan,choices,holds)['jobs'][actor]
            assert row['project_expense_usd']==account_charge(world,actual)
            assert row['status']==actual['acceptance']['status']
            assert row['remaining_authority_usd']==actual['procurement']['remaining_usd']
            assert row['central_expense_usd']==actual['cost_usd']-account_charge(world,actual)


def test_quote_binds_own_hold_but_never_looks_up_actual_finish():
    run,holds,plan=fixture();actor=run['world']['order'][1];visible=packet(run,actor)
    before=quote_booking(visible,{'assumed_finish_hour':12})
    assert before['bound_records']['provisional_hold']==8
    for entry in before['choices']:
        if entry['acceptance_slot']==12:assert entry['project_expense_usd']==365
    hidden=deepcopy(visible);hidden['workspace']={'random':'Other records changed'};hidden['messages']=[]
    hidden['dispatch_plan']['hours']={p:1 for p in hidden['dispatch_plan']['hours']}
    assert quote_booking(hidden,{'assumed_finish_hour':12})==before
    altered=deepcopy(visible);altered['private_booking']['provisional_start']=12
    after=quote_booking(altered,{'assumed_finish_hour':12})
    assert next(r for r in after['choices'] if r['acceptance_slot']==12)['project_expense_usd']==340
    assumed=quote_booking(visible,{'assumed_finish_hour':8})
    assert next(r for r in assumed['choices'] if r['acceptance_slot']==8)['status']=='completed'
    assert next(r for r in before['choices'] if r['acceptance_slot']==8)['status']=='missed'


def test_changes_only_confirmation_tool_interface():
    old,_,_=fixture(protocol=10);new,_,_=fixture(protocol=11)
    actor=old['world']['focal']
    for stage,who in [('request',actor),('allocate','scheduler'),('commit',actor)]:
        old['stage']=new['stage']=stage
        x,y=packet(old,who),packet(new,who)
        if stage=='commit':
            assert set(x.pop('tools'))=={'plan_quote'} and set(y.pop('tools'))=={'booking_quote'}
        assert x==y


@pytest.mark.parametrize('query',[{}, {'assumed_finish_hour':True}, {'assumed_finish_hour':-1}, {'assumed_finish_hour':121}, {'assumed_finish_hour':12,'hold':12}])
def test_invalid_or_record_overriding_queries_are_rejected(query):
    run,_,_=fixture();visible=packet(run,run['world']['focal'])
    with pytest.raises(ValueError):quote_booking(visible,query)


def test_cli_records_booking_assumption_and_bound_source(tmp_path):
    run,_,_=fixture();visible=packet(run,run['world']['order'][1])
    source=tmp_path/'input.json';query=tmp_path/'quote-booking.json'
    write(source,visible);write(query,{'assumed_finish_hour':12})
    script=Path(__file__).parents[1]/'src/disclosure_causality/quote.py'
    result=subprocess.run([sys.executable,'-B',str(script),'--input',str(source),'--query',str(query)],capture_output=True,text=True,check=True)
    returned=json.loads(result.stdout);records=[json.loads(line) for line in (tmp_path/'input.quotes.jsonl').read_text().splitlines()]
    assert len(records)==1 and records[0]['valid'] and records[0]['result']==returned
    assert returned['assumed_finish_hour']==12 and returned['bound_records']['provisional_hold']==8


@pytest.mark.parametrize('mismatch',['owner','service','slots','boolean_invoice'])
def test_mismatched_assignment_is_rejected(mismatch):
    run,_,_=fixture();visible=packet(run,run['world']['focal'])
    if mismatch=='owner':visible['assignment']['staffing_invoice']['charged_to']='project-02'
    elif mismatch=='service':visible['assignment']['service']='office_contractor'
    elif mismatch=='slots':visible['private_booking']['available_start_hours']=[4]
    else:visible['assignment']['staffing_invoice']['charge_usd']=False
    with pytest.raises(ValueError,match='Unsupported'):quote_booking(visible,{'assumed_finish_hour':8})
