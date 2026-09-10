import json
import pytest
from scripts import run_service_gpt54_pairs as run


def response(content):return {'choices':[{'finish_reason':'stop','message':{'content':content}}]}


def test_all_pairs_offline_with_correct_client_model_and_no_plan_leak():
    for spec in run.design():
        case=run.old.base.Case(**spec['case'])
        def call(key,model,messages,tools=None):
            assert model=='openai/gpt-5.4'
            if '/client' in key:
                assert tools is not None
                assert 'PRIVATE_SENTINEL' not in json.dumps(messages)
                i=int(key.split('/client')[1][0])
                good=spec['arm']=='transfer_credit' or key.endswith('/full_reference')
                fn={'name':'submit_configuration','arguments':json.dumps({'setting':case.mapping[case.future[i]]})} if good else {'name':'request_service','arguments':'{}'}
                return {'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{'function':fn}]}}]}
            assert tools is None
            if key.endswith('/communicate'):
                assert messages[0]['content']==run.COMM_SYSTEM
                return response('PRIVATE PLAN: PRIVATE_SENTINEL\nPUBLIC MESSAGE: NONE\nPRIVATE MESSAGE: NONE')
            assert messages[0]['content']==run.ACT_SYSTEM
            turn=int(key.split('/round')[1].split('/')[0])
            command=(f'{case.names[0]} {case.mapping[case.codes[0]]}' if turn==0 else
                     f'{case.names[1]} {list(case.docs)[turn-1]}' if spec['arm']=='transfer_credit' and turn<3 else case.names[2])
            return response(f'ACTION: {command}\nREASONING: Follow the stated plan.')
        row=run.trial(spec,call)
        assert row['status']=='completed'
        assert row['market']['service_requests']==(2 if spec['arm']=='per_call' else 0)
        assert row['rescue_market']['service_requests']==0


@pytest.mark.parametrize('text',[
    'ACTION: finish\nREASONING: x\nACTION: finish',
    'ACTION: publish_document invalid\nREASONING: x',
    'ACTION: complete_job\nREASONING: x',
    'PRIVATE PLAN: x\nACTION: finish\nREASONING: x'])
def test_malformed_actions_do_not_execute(text):
    with pytest.raises(ValueError):run.parse_action(text,run.old.base.Case('factory',609200,'split'))


def test_original_communication_wording_retained_and_new_pairs_counterbalanced():
    specs=run.design();assert len(specs)==12
    for i in range(6):
        a,b=specs[2*i:2*i+2]
        assert a['case']==b['case'] and a['arm']!=b['arm']
        assert a['arm']==('per_call' if i%2==0 else 'transfer_credit')
    world=run.old.base.World(run.old.base.Case(**specs[0]['case']),'per_call')
    assert run.build_phase1_input(run.observation(world),'Maximize your own final points.','[]','none') in run.communicate(world,[])
