import pytest
from info_marketplace.parser import parse_phase1

@pytest.mark.parametrize('quote,body', [('"',"I'll gather food and deposit it."),("'",'I will report "gold" accurately.'),('"',r'I will say \"ready\" before leaving.')])
@pytest.mark.parametrize('template', ['PROMISE Agent_1: {q}{body}{q} by round 2', 'to Agent_1: PROMISE {q}{body}{q} by round 2', 'PROMISE Agent_1: {q}{body}{q}', 'to Agent_1: PROMISE {q}{body}{q}'])
def test_promise_body_preserved(quote,body,template):
 raw='PRIVATE PLAN: Gather.\nPUBLIC MESSAGE: '+template.format(q=quote,body=body)+'\nPRIVATE MESSAGE: NONE'
 _,messages,_=parse_phase1(raw,'Agent_0',0)
 assert len(messages)==1
 assert messages[0].commitment==body

@pytest.mark.parametrize('quote,body',[('"',"There's gold here; I'll gather one."),("'",'The site contains "gold".')])
def test_report_body_preserved(quote,body):
 raw=f'PRIVATE PLAN: Report.\nPUBLIC MESSAGE: REPORT Mines: {quote}{body}{quote}\nPRIVATE MESSAGE: NONE'
 _,messages,_=parse_phase1(raw,'Agent_0',0)
 assert len(messages)==1
 assert messages[0].claim==body
