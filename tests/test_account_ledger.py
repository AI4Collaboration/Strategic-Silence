"""Clearer accounting must preserve mechanics and private workload boundaries."""
from copy import deepcopy
import json

import pytest

from disclosure_causality.environment import make_world, public_terms, schedule
from disclosure_causality.runner import initialize, packet
from disclosure_causality.validation import reference_request, submit
from disclosure_causality.comprehension import appointment_exercise


@pytest.mark.parametrize('n', [4, 8, 16, 32])
@pytest.mark.parametrize('funds', ['joint', 'protected'])
@pytest.mark.parametrize('liability', ['office', 'project'])
@pytest.mark.parametrize('overrun', [False, True])
@pytest.mark.parametrize('objective', ['client', 'shared'])
def test_ledger_does_not_change_actions_costs_or_service_outcomes(n, funds, liability, overrun, objective):
    config=dict(n=n, funds=funds, liability=liability, overrun=overrun, objective=objective, audience='team')
    previous=make_world(protocol=8, **config); current=make_world(protocol=9, **config)
    stripped=deepcopy(current);stripped['protocol']=8
    for p in stripped['projects'].values():p['files'].pop('finance/cost-center.txt')
    assert stripped==previous
    for actor,p in current['projects'].items():
        ledger=p['files']['finance/cost-center.txt']
        assert p['label'] not in ledger and p['contact'] not in ledger
        assert ('central service-guarantee account' in ledger)==(liability=='office')
        assert ('separate staffing reserve' in ledger)==(funds=='protected')
    holds={p:v['deadline'] for p,v in previous['projects'].items()}
    choices={p:{'acceptance_slot':v['deadline']} for p,v in previous['projects'].items()}
    for contractor in (None,previous['focal']):
        plan={'internal_order':[p for p in previous['order'] if p!=contractor], 'office_contractor_for':contractor}
        assert schedule(previous,plan,choices,holds)==schedule(current,plan,choices,holds)
    old_terms=public_terms(previous);new_terms=public_terms(current)
    old_terms['procurement']['payment_rules']=old_terms['procurement']['payment_rules'].replace('Reconciliation','Acceptance')
    assert old_terms==new_terms
    assert 'reconciliation' not in json.dumps(new_terms).lower()


def test_office_finance_records_do_not_reveal_unreported_work_or_private_holds(tmp_path):
    offices=[]
    for overrun in (False,True):
        path=tmp_path/str(overrun)
        run=initialize(path,protocol=9,funds='joint',liability='office',audience='team',overrun=overrun)
        requests={a:reference_request(packet(run,a),'silent') for a in run['world']['projects']}
        run=submit(path,'request',requests)
        visible=packet(run,'scheduler');offices.append(visible)
        assert len([p for p in visible['workspace'] if p.startswith('finance/')])==3
        assert not any(p.startswith('reports/') for p in visible['workspace'])
    assert offices[0]==offices[1]


@pytest.mark.parametrize('funds',['joint','protected'])
def test_postcheck_adds_records_without_changing_questions_or_expected_values(funds):
    before,expected=appointment_exercise(funds,8)
    after,observed=appointment_exercise(funds,9)
    assert expected==observed and before['exercise']==after['exercise']
    assert before['response_schema']==after['response_schema']
    assert len(after['workspace'])==3
    assert 'workspace' not in before


def test_task_and_choice_schema_stay_unchanged(tmp_path):
    packets=[]
    for protocol in (8,9):
        run=initialize(tmp_path/str(protocol),protocol=protocol,funds='joint',liability='office',audience='team')
        packets.append(packet(run,run['world']['focal']))
    for key in ('task','response_schema','delivery','messages'):
        assert packets[0][key]==packets[1][key]
    assert packets[0]['terms']['reporting_agreement']==packets[1]['terms']['reporting_agreement']
