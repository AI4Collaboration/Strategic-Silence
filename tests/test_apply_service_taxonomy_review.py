from dataclasses import asdict
import pytest
from scripts.apply_service_taxonomy_review import Case,classify_episode


def fixture():
    case=Case('factory',609110,'split')
    row=dict(id='x',status='completed',case=asdict(case),model='m',arm='per_call',mode='original_plan',
             deliveries=[],outcome={'published':[]},clients=[{'outcome':{}},{'outcome':{}}],rescue_clients=[{'outcome':{}},{'outcome':{}}])
    annotation=dict(episode_id='x',messages=[],plan_review={},reviewer='test')
    return case,row,annotation


def test_silence_and_automatic_ticket_are_distinct_views():
    _,row,a=fixture()
    r=classify_episode(row,a)[0]
    assert r['expert_controlled_delivery']['outcome']=='no_communication'
    assert r['effective_archive']['outcome']=='content_omission'


def test_wrong_audience_is_not_content_omission():
    _,row,a=fixture()
    row['deliveries']=[dict(text='mapping for client zero',recipients=['Agent_1'])]
    a['messages']=[dict(text='mapping for client zero',sufficient_for_client_mapping=[True,False])]
    r=classify_episode(row,a)
    assert r[0]['expert_controlled_delivery']['outcome']=='recipient_failure'
    assert r[1]['expert_controlled_delivery']['outcome']=='content_omission'


def test_published_reference_reaches_both_clients_without_messages():
    case,row,a=fixture();row['outcome']['published']=list(case.docs)
    assert all(r['expert_controlled_delivery']['outcome']=='useful_delivery' for r in classify_episode(row,a))


def test_invalid_case_cannot_be_semantically_relabelled_valid():
    _,row,a=fixture();row['status']='invalid'
    with pytest.raises(AssertionError):classify_episode(row,a)
