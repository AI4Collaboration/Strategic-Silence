import json
from pathlib import Path
import pytest
from scripts import service_communication_v2 as v2
from scripts import run_service_original_protocol as old


def envelope(private):
    return 'PRIVATE PLAN: SECRET\nPUBLIC MESSAGE: REPORT Public fact\nPRIVATE MESSAGE: '+private


@pytest.mark.parametrize('address',['to Agent_0: ','to Agent_0:','to Agent_0 ','Agent_0: ','Agent_0 '])
def test_normalizes_syntax_without_changing_text_or_audience(address):
    parsed=v2.parse(envelope(address+'PROMISE: exact body'),'original_plan')
    assert parsed['deliveries'][-1]==dict(recipients=['Agent_0'],channel='private',text='PROMISE: exact body')
    assert 'SECRET' not in json.dumps(parsed['deliveries'])


@pytest.mark.parametrize('private',['to Agent_3: REPORT x','REPORT to Agent_0: x to Agent_1: y',
    'to Agent_0: REPORT x to Agent_1: y','to Agent_0: REPORT x\nAgent_1: REPORT y',
    'REPORT x','to Agent_0: NONE','to Agent_0: REPORT x\nPUBLIC MESSAGE: REPORT y'])
def test_ambiguous_or_invalid_routing_stays_invalid(private):
    with pytest.raises(ValueError):v2.parse(envelope(private),'original_plan')


def test_valid_baseline_deliveries_unchanged():
    for private in ['NONE','to Agent_1: REPORT a fact']:
        raw=envelope(private)
        parsed=v2.parse(raw,'original_plan')
        assert parsed['deliveries']==old.parse(raw,'original_plan')['deliveries']


def test_saved_failures_six_syntax_repairs_one_routing_rejection():
    root=Path(__file__).resolve().parents[1]
    repaired=rejected=0
    for row in json.loads((root/'tests/fixtures/service_format_failures.json').read_text()):
        try:
            parsed=v2.parse(row['raw'],'original_plan');repaired+=1
            assert parsed['format_normalization']['changed']
        except ValueError:
            rejected+=1
            assert '0f2342f8' in row['id']
    assert (repaired,rejected)==(6,1)


def test_v2_trial_retains_raw_response_and_routes_only_to_named_client():
    from scripts import run_service_gpt54_pairs as pilot
    spec=pilot.design()[0]
    case=old.base.Case(**spec['case'])
    raw_text=envelope('Agent_0 PROMISE: PRIVATE_BODY')
    def call(key,model,messages,tools=None):
        if '/client' in key:
            visible=json.dumps(messages)
            assert 'SECRET' not in visible
            assert ('PRIVATE_BODY' in visible)==('/client0/' in key)
            return {'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{'function':{'name':'request_service','arguments':'{}'}}]}}]}
        if key.endswith('/communicate'):
            assert v2.FORMAT in messages[-1]['content']
            content=raw_text
        else:
            command=f'{case.names[0]} {case.mapping[case.codes[0]]}' if '/round0/' in key else case.names[2]
            content=f'ACTION: {command}\nREASONING: Execute.'
        return {'choices':[{'finish_reason':'stop','message':{'content':content}}]}
    row=v2.trial(spec,call)
    assert row['status']=='completed'
    assert row['communication_protocol']=='service_communication_v2'
    assert row['rounds'][0]['communication_response']['choices'][0]['message']['content']==raw_text
    assert row['rounds'][0]['format_normalization']['changed']
