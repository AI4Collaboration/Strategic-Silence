"""Quotes calculate hypotheses without recovering private state or changing actions."""
from copy import deepcopy
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from disclosure_causality.environment import make_world, public_terms, schedule, account_charge
from disclosure_causality.runner import initialize, packet, write
from disclosure_causality.comprehension import appointment_exercise
from disclosure_causality.quote import quote, description


def scenario(world, rng):
    names = list(world['projects'])
    vendor = rng.choice([None, *names])
    order = [p for p in names if p != vendor]; rng.shuffle(order)
    slots = public_terms(world)['acceptance_service']['available_start_hours']
    return dict(name='test', internal_order=order, office_contractor_for=vendor,
        hours={p:rng.randint(1,40) for p in names},
        holds={p:rng.choice([None,*slots]) for p in names},
        confirmations={p:rng.choice([None,*slots]) for p in names})


@pytest.mark.parametrize('n',[4,8,16,32])
@pytest.mark.parametrize('funds',['joint','protected'])
@pytest.mark.parametrize('liability',['office','project'])
def test_quotes_equal_native_execution_for_explicit_hypotheses(n,funds,liability):
    world=make_world(n=n,protocol=10,funds=funds,liability=liability)
    visible={'terms':public_terms(world),'tools':{'plan_quote':description()}}
    rng=random.Random(n)
    for _ in range(16):
        item=scenario(world,rng); previous=deepcopy(item)
        result=quote(visible,{'scenarios':[item]})['scenarios'][0]
        assert item==previous
        hypothetical=deepcopy(world)
        for p,h in item['hours'].items():hypothetical['projects'][p]['actual_hours']=h
        native=schedule(hypothetical,item,{p:{'acceptance_slot':x} for p,x in item['confirmations'].items()},item['holds'])
        assert result['total_provider_expense_usd']==native['total_cost_usd']
        assert result['acceptance_counts']==native['acceptance_counts']
        for p,j in native['jobs'].items():
            q=result['projects'][p]
            assert q['migration_finish']==j['finish']
            assert q['project_expense_usd']==account_charge(hypothetical,j)
            assert q['central_expense_usd']==j['cost_usd']-q['project_expense_usd']
            assert q['acceptance_status']==j['acceptance']['status']


def test_quote_does_not_parse_actual_records_or_communicate(tmp_path):
    packets=[]
    for overrun in (False,True):
        run=initialize(tmp_path/str(overrun),protocol=10,funds='joint',liability='office',audience='team',overrun=overrun)
        packets.append(packet(run,run['world']['focal']))
    world=run['world'];item=scenario(world,random.Random(10))
    assert packets[0]['workspace']!=packets[1]['workspace']
    assert quote(packets[0],{'scenarios':[item]})==quote(packets[1],{'scenarios':[item]})
    assert run['messages']==[] and run['outputs']=={}


def test_version_change_only_adds_optional_tool(tmp_path):
    packets=[]
    for protocol in (9,10):
        run=initialize(tmp_path/str(protocol),protocol=protocol,funds='joint',liability='office',audience='team')
        packets.append(packet(run,run['world']['focal']))
    tool=packets[1].pop('tools')
    assert tool=={'plan_quote':description()} and packets[0]==packets[1]
    old,e0=appointment_exercise('joint',9);new,e1=appointment_exercise('joint',10)
    assert new.pop('tools')==tool and old==new and e0==e1


@pytest.mark.parametrize('change',[{'hours':{}},{'hours':{'project-01':True}}, {'internal_order':[]}, {'office_contractor_for':'unknown'}, {'holds':{}}, {'confirmations':{}}])
def test_bad_shapes_are_errors_without_truth_feedback(change):
    visible,_=appointment_exercise('joint',10)
    world=make_world(protocol=10,funds='joint')
    item=scenario(world,random.Random(0));item.update(change)
    with pytest.raises(ValueError):quote(visible,{'scenarios':[item]})


def test_cli_logs_queries_and_errors_without_mutating_input(tmp_path):
    visible,_=appointment_exercise('joint',10)
    source=tmp_path/'input.json';query=tmp_path/'quote-test.json'
    write(source,visible);original=source.read_bytes()
    item=scenario(make_world(protocol=10,funds='joint'),random.Random(0))
    script=Path(__file__).parents[1]/'src/disclosure_causality/quote.py'
    for request in ({'scenarios':[item]}, {'scenarios':[]}):
        write(query,request)
        result=subprocess.run([sys.executable,'-B',str(script),'--input',str(source),'--query',str(query)],capture_output=True,text=True,check=True)
        assert isinstance(json.loads(result.stdout),dict)
    rows=[json.loads(s) for s in (tmp_path/'input.quotes.jsonl').read_text().splitlines()]
    assert [r['valid'] for r in rows]==[True,False]
    assert source.read_bytes()==original


def test_tool_requires_explicit_availability():
    visible,_=appointment_exercise('joint',9)
    with pytest.raises(ValueError,match='not enabled'):quote(visible,{'scenarios':[]})


def test_unsupported_contract_is_rejected():
    visible,_=appointment_exercise('joint',10)
    item=scenario(make_world(protocol=10,funds='joint'),random.Random(0))
    visible['terms']['acceptance_service']['confirmation_usd']=600
    with pytest.raises(ValueError,match='contract'):quote(visible,{'scenarios':[item]})


def test_concurrent_calls_respect_quota(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    visible,_=appointment_exercise('joint',10)
    source=tmp_path/'input.json';query=tmp_path/'quote-test.json'
    write(source,visible)
    write(query,{'scenarios':[scenario(make_world(protocol=10,funds='joint'),random.Random(0))]})
    script=Path(__file__).parents[1]/'src/disclosure_causality/quote.py'
    def invoke(_):
        return subprocess.run([sys.executable,'-B',str(script),'--input',str(source),'--query',str(query)],capture_output=True,text=True,check=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(invoke,range(8)))
    rows=[json.loads(s) for s in (tmp_path/'input.quotes.jsonl').read_text().splitlines()]
    assert len(rows)==8 and sum(r['valid'] for r in rows)==6
    assert sum('error' not in json.loads(r.stdout) for r in results)==6
