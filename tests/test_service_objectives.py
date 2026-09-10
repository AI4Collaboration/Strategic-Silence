import json
from scripts import service_objectives as run
from scripts import run_service_gpt54_pairs as base

def test_all_conditions_apply_goals_to_all_roles_and_keep_private_plan_private():
    for condition in run.CONDITIONS:
        spec=dict(base.design()[0],condition=condition,arm='per_call')
        case=base.old.base.Case(**spec['case']);calls=[]
        def call(key,model,messages,tools=None):
            calls.append(key)
            role='client'+key.split('/client')[1][0] if '/client' in key else 'expert'
            assert '/original_plan/'+condition+'/' in key
            assert run.goal(condition,role) in messages[0]['content']
            if '/client' in key:
                assert 'SECRET_PLAN' not in json.dumps(messages)
                return {'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{'function':{'name':'request_service','arguments':'{}'}}]}}]}
            if key.endswith('/communicate'):
                content='PRIVATE PLAN: SECRET_PLAN\nPUBLIC MESSAGE: NONE\nPRIVATE MESSAGE: NONE'
            else:
                command=f'{case.names[0]} {case.mapping[case.codes[0]]}' if '/round0/' in key else case.names[2]
                content=f'ACTION: {command}\nREASONING: Execute.'
            return {'choices':[{'finish_reason':'stop','message':{'content':content}}]}
        row=run.trial(spec,call)
        assert row['status']=='completed' and row['id'].endswith('/'+condition)
        assert len(calls)==8
        assert run.goal('mixed','expert')==run.goal('competitive','expert')
        assert run.goal('mixed','client0')==run.goal('aligned','client0')
