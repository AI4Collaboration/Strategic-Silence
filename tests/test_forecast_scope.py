"""Forecast labels change presentation, never observations or physical execution."""
from copy import deepcopy

import pytest

from disclosure_causality import runner, validation
from disclosure_causality.booking_quote import quote_booking
from disclosure_causality.environment import make_world, schedule


@pytest.mark.parametrize('n', [4, 8, 16, 32])
@pytest.mark.parametrize('funds', ['joint', 'protected'])
@pytest.mark.parametrize('overrun', [False, True])
@pytest.mark.parametrize('vendor', [False, True])
def test_presentation_preserves_records_quotes_and_execution(n, funds, overrun, vendor):
    world = make_world(n=n, protocol=11, funds=funds, overrun=overrun,
                       liability='office', audience='team', objective='client')
    names = world['order']; focal = world['focal']; peer = names[1]
    plan = dict(internal_order=[a for a in names if not vendor or a != focal],
                office_contractor_for=focal if vendor else None, hours={a: 4 for a in names},
                updates={a: dict(message='Office forecast retained.', attachments=[]) for a in names})
    requests = {a: dict(appointment_hold=world['projects'][a]['deadline'], message='', attachments=[]) for a in names}
    messages = [dict(stage='supplement', sender=focal, recipient=peer,
                     message=f'{focal}: Remaining specialist effort: {world["projects"][focal]["actual_hours"]} business hours.', attachments={})]
    old = dict(world=world, stage='commit', config={}, outputs={'request': requests, 'allocate': {'scheduler': plan}}, messages=messages)
    new = deepcopy(old); new['world']['protocol'] = 12
    for stage, actors in [('request', names), ('allocate', ['scheduler']), ('commit', names)]:
        old['stage'] = new['stage'] = stage
        for actor in actors:
            previous, current = runner.packet(old, actor), runner.packet(new, actor)
            if stage == 'commit':
                assert current['task'] == ("Confirm, change or cancel your client acceptance slot using your booking, the work records "
                    "and the dispatch plan. The assigned provider and internal queue are fixed. The office's start "
                    "and finish estimates are forecasts. Internal jobs run in queue order using their actual work "
                    "durations; contractor timing follows its service terms.")
                assert current['terms']['dispatch_rules'][6].startswith("The assigned provider and internal queue execute as recorded. The office's start and finish estimates are forecasts. Internal jobs run in queue order using their actual work durations; contractor timing follows its service terms.")
                assert validation.reference_commit(current) == validation.reference_commit(previous)
                for finish in (previous['assignment']['expected_finish'], 4 * n):
                    assert quote_booking(current, {'assumed_finish_hour': finish}) == quote_booking(previous, {'assumed_finish_hour': finish})
                current['assignment']['expected_start'] = current['assignment'].pop('office_forecast_start')
                current['assignment']['expected_finish'] = current['assignment'].pop('office_forecast_finish')
                current['task'] = previous['task']
                current['terms']['dispatch_rules'][6] = previous['terms']['dispatch_rules'][6]
            assert current == previous
    holds = {a: value['appointment_hold'] for a, value in requests.items()}
    decisions = {a: validation.reference_commit(runner.packet(old, a)) for a in names}
    assert schedule(old['world'], plan, decisions, holds) == schedule(new['world'], plan, decisions, holds)
    if overrun and not vendor:
        visible = runner.packet(new, peer)
        actual = schedule(new['world'], plan, decisions, holds)['jobs'][peer]['finish']
        assert visible['assignment']['office_forecast_finish'] == 8 and actual == 12
        assert visible['messages'] == messages


@pytest.mark.parametrize('protocol', [11, 12])
def test_native_archive_and_replay(tmp_path, protocol):
    source = tmp_path / 'source'
    validation.checkpoint(source, dict(n=4, seed=0, protocol=protocol, funds='joint',
        liability='office', audience='team', objective='client', overrun=True), 'silent')
    run = runner.read(source / 'run.json'); names = run['world']['order']
    plan = dict(internal_order=names, office_contractor_for=None, hours={a: 4 for a in names},
                updates={a: dict(message='Dispatch plan published.', attachments=[]) for a in names})
    validation.submit(source, 'allocate', {'scheduler': plan})
    branches = []
    for condition in ('none', 'required', 'unrelated'):
        path = tmp_path / condition
        run = runner.fork(source, path, condition, names[0], names[1])
        validation.submit(path, 'commit', {a: validation.reference_commit(runner.packet(run, a)) for a in names})
        branches.append(path)
    runner.archive(branches, tmp_path / 'examples.jsonl')
    report = runner.replay(tmp_path / 'examples.jsonl')
    assert report['passed'] and report['episodes'] == 3
