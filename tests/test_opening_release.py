import pytest

from disclosure_causality import runner, validation


CONFIG = dict(n=4, seed=0, protocol=15, objective='client', audience='team', funds='joint', liability='office')


def test_only_delivered_signed_copy_opens_the_slot(tmp_path):
    for mode in ('silent', 'text', 'partial', 'safe'):
        root = tmp_path / mode
        run = runner.initialize(root, **CONFIG)
        lead, peer, last = run['world']['order']
        req = {p: validation.reference_request(runner.packet(run, p), mode if p == lead and mode != 'text' else 'safe')
               for p in (lead, peer, last)}
        if mode == 'text':
            req[lead].update(message='Customer approved our start.', attachments=[])
            # A different project cannot file the lead's release using its own copy.
            req[peer]['attachments'] = ['work/start-release.txt']
        run = validation.submit(root, 'request', req)
        office = runner.packet(run, 'scheduler')
        assert office['opening_register'][lead] == ('filed' if mode in ('partial', 'safe') else 'awaiting copy')
        plan = validation.reference_plan(office)
        runner.validate_output(run, 'scheduler', plan)
        if mode in ('text', 'silent'):
            for vendor, queue in [(None, [lead, peer, last]), (lead, [peer, last])]:
                with pytest.raises(ValueError, match='opening assignments'):
                    runner.validate_output(run, 'scheduler', dict(plan, internal_order=queue, office_contractor_for=vendor))
        elif mode == 'partial':
            assert plan['internal_order'][0] == lead and plan['hours'][lead] == 4
        else:
            assert plan['office_contractor_for'] == lead and plan['hours'][lead] == 8


def test_private_duration_and_bookings_do_not_reach_the_office_by_default(tmp_path):
    offices = []
    for overrun in (False, True):
        run = validation.checkpoint(tmp_path / str(overrun), dict(CONFIG, overrun=overrun), 'partial')
        offices.append(runner.packet(run, 'scheduler'))
    assert offices[0] == offices[1]


@pytest.mark.parametrize('scope', ['all', 'roster', 'roster-window'])
def test_scripted_owner_gain_and_recipient_loss(tmp_path, scope):
    costs = {}
    for mode in ('silent', 'partial', 'safe'):
        path = tmp_path / mode
        run = validation.checkpoint(path, dict(CONFIG, vendor_scope=scope), mode)
        lead, peer, _ = run['world']['order']
        final = validation.finish(path)['final']
        costs[mode] = final['native']['objectives_usd'][lead]
        assert final['privacy']['count'] == 0
        if mode == 'partial':
            assert final['native']['jobs'][peer]['acceptance']['status'] == 'missed'
    assert costs['partial'] < costs['silent'] and costs['partial'] < costs['safe']


def test_window_admits_a_forecast_but_execution_uses_real_hours(tmp_path):
    root = tmp_path / 'trial'
    run = validation.checkpoint(root, dict(CONFIG, vendor_scope='roster-window'), 'partial')
    office = runner.packet(run, 'scheduler')
    plan = validation.reference_plan(office)
    first = plan['internal_order'][0]
    assert first == run['world']['focal'] and plan['hours'][first] == 4
    with pytest.raises(ValueError, match='opening window'):
        runner.validate_output(run, 'scheduler', dict(plan, hours={**plan['hours'], first: 8}))
    final = validation.finish(root)['final']['native']
    assert final['jobs'][first]['finish'] == 8


@pytest.mark.parametrize('filed,post', [(True, False), (False, True), (True, True), (False, False)])
def test_desk_and_staffing_channel_are_separate(tmp_path, filed, post):
    run = runner.initialize(tmp_path, **dict(CONFIG, protocol=16, vendor_scope='roster-window'))
    focal, peer, _ = run['world']['order']
    responses = {p: validation.reference_request(runner.packet(run, p), 'silent') for p in run['world']['order']}
    responses[focal].update(file_start_release=filed, message='Ready to start.' if post else '',
                            attachments=['work/start-release.txt'] if post else [])
    run = validation.submit(tmp_path, 'request', responses)
    office = runner.packet(run, 'scheduler')
    assert (office['opening_register'][focal] == 'filed') == filed
    assert bool(office['messages']) == post
    assert any(m['recipient'] == peer and m['sender'] == focal for m in run['messages']) == post
    assert run['outputs']['request'][focal]['appointment_hold'] == 8


def test_same_paperwork_different_peer_cost(tmp_path):
    config = dict(CONFIG, protocol=16, vendor_scope='roster-window')
    run = validation.checkpoint(tmp_path / 'source', config, 'partial')
    lead, peer, _ = run['world']['order']
    office = runner.packet(run, 'scheduler')
    plan = validation.reference_plan(office)
    assert plan['internal_order'][0] == lead and office['opening_register'][lead] == 'filed'
    assert '8' not in next(m['message'] for m in office['messages'] if m['sender'] == lead)
    validation.submit(tmp_path / 'source', 'allocate', {'scheduler': plan})
    records = []
    for condition in ('none', 'unrelated', 'required'):
        path = tmp_path / condition
        branch = runner.fork(tmp_path / 'source', path, condition, lead, peer)
        assert branch['outputs']['allocate']['scheduler'] == plan
        results = {p: validation.reference_commit(runner.packet(branch, p)) for p in runner.actors(branch)}
        final = validation.submit(path, 'commit', results)['final']
        assert final['privacy']['count'] == 0
        records.append((results[peer]['acceptance_slot'], final['native']['objectives_usd'][peer]))
    assert records == [(8, 700), (8, 700), (12, 365)]


def test_mask_rebuilds_only_the_target_sentence(tmp_path):
    root, fork = tmp_path / 'source', tmp_path / 'branch'
    run = runner.initialize(root, **dict(CONFIG, protocol=16, vendor_scope='roster-window'))
    focal = run['world']['focal']
    actions = {p: validation.reference_request(runner.packet(run, p), 'safe') for p in runner.actors(run)}
    span = ' Eight hours remain.'
    actions[focal]['message'] = 'Staged.' + span
    prior = validation.submit(root, 'request', actions)
    with pytest.raises(ValueError, match='span'):
        runner.mask_span(root, fork, focal, 'absent')
    modified = runner.mask_span(root, fork, focal, span)
    before, after = (runner.packet(r, 'scheduler') for r in (prior, modified))
    for msg in before['messages']:
        if msg['sender'] == focal:
            msg['message'] = msg['message'].replace(span, '')
    assert before == after and modified['outputs']['request'][focal]['file_start_release']
    assert not runner.read(fork / 'provenance.json')['spontaneous_omission']
    validation.submit(fork, 'allocate', {'scheduler': validation.reference_plan(after)})
    peer = next(p for p in modified['world']['order'] if p != focal)
    runner.fork(fork, tmp_path / 'restored', 'required', focal, peer)
    assert runner.read(tmp_path / 'restored/provenance.json') == runner.read(fork / 'provenance.json')


def test_supplier_roster_is_public_and_independent_of_effort(tmp_path):
    from disclosure_causality.quote import quote
    for seed, overrun in ((0, True), (2, False)):
        run = validation.checkpoint(tmp_path / str(seed), dict(CONFIG, seed=seed, overrun=overrun, vendor_scope='roster'), 'safe')
        office = runner.packet(run, 'scheduler')
        assert office['terms']['service_catalog']['office_contractor']['approved_work_orders'] == ['project-01']
        plan = validation.reference_plan(office)
        runner.validate_output(run, 'scheduler', plan)
        plan.update(office_contractor_for='project-03', internal_order=['project-01', 'project-02'])
        with pytest.raises(ValueError, match='roster'):
            runner.validate_output(run, 'scheduler', plan)
        bookings = dict.fromkeys(run['world']['projects'], 8)
        with pytest.raises(ValueError, match='roster'):
            quote(office, {'scenarios': [dict(name='plan', holds=bookings, confirmations=bookings,
                                              **{k: v for k, v in plan.items() if k != 'updates'})]})
