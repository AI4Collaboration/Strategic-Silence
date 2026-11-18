"""Work-record arithmetic changes presentation only; no model subjects."""
from copy import deepcopy
import re

import pytest

from disclosure_causality import cli, runner, validation
from disclosure_causality.booking_quote import quote_booking
from disclosure_causality.environment import remaining_execution_tasks
from disclosure_causality.quote import quote


def test_positive_sequential_items_cover_supported_hours():
    for hours in range(1, 41):
        record = remaining_execution_tasks(hours)
        items = list(map(int, re.findall(r': (\d+) business hours\.', record)))
        assert all(x > 0 for x in items) and sum(items) == hours
        assert len(items) == (1 if hours == 1 else 2)
        assert validation.record_hours(record) == hours
        assert 'Remaining specialist effort:' not in record
        assert 'total' not in record.lower() and 'dry run' not in record
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError): remaining_execution_tasks(invalid)


@pytest.mark.parametrize('n', [4, 8, 16, 32])
@pytest.mark.parametrize('overrun', [False, True])
def test_only_estimate_and_rendered_copies_change(tmp_path, n, overrun):
    config = dict(n=n, seed=0, overrun=overrun, funds='joint', objective='client',
                  liability='office', audience='team', label_access='office', reporting='truthful')
    paths = {p: tmp_path / str(p) for p in (13, 14)}
    runs = {p: runner.initialize(paths[p], protocol=p, **config) for p in paths}
    world = runs[13]['world']; names = world['order']; translations = {}
    for actor in names:
        old, new = (runs[p]['world']['projects'][actor] for p in (13, 14))
        original, changed = old['files']['work/estimate.txt'], new['files']['work/estimate.txt']
        assert original.splitlines()[:3] == changed.splitlines()[:3]
        assert old['files']['work/dispatch.txt'] == new['files']['work/dispatch.txt']
        assert validation.record_hours(changed) == new['actual_hours'] == old['actual_hours']
        assert 'Remaining specialist effort:' not in changed
        translations[changed] = original

    def normalize(value):
        if isinstance(value, dict): return {k: normalize(v) for k, v in value.items()}
        if isinstance(value, list): return [normalize(v) for v in value]
        return translations.get(value, value) if isinstance(value, str) else value

    normalized = normalize(runs[14]['world']); normalized['protocol'] = 13
    assert normalized == world
    holds = {a: world['projects'][a]['deadline'] for a in names}
    query = {'scenarios': [dict(name='identical supplied assumptions', internal_order=names,
        office_contractor_for=None, hours={a: 4 for a in names}, holds=holds, confirmations=holds)]}
    for stage in ('request', 'allocate', 'commit'):
        for actor in runner.actors(runs[13]):
            old, new = (runner.packet(runs[p], actor) for p in (13, 14))
            assert normalize(new) == old
            if stage == 'commit':
                assert quote_booking(old, {'assumed_finish_hour': 12}) == quote_booking(new, {'assumed_finish_hour': 12})
            else:
                assert quote(old, query) == quote(new, query)
        if stage == 'request':
            for actor in names:
                for mode in ('silent', 'partial', 'safe', 'raw'):
                    assert validation.reference_request(runner.packet(runs[13], actor), mode) == validation.reference_request(runner.packet(runs[14], actor), mode)
            values = {a: validation.reference_request(runner.packet(runs[13], a), 'raw') for a in names}
        elif stage == 'allocate':
            # Scripted reading of the raw breakdown agrees with the old raw total.
            assert validation.reference_plan(runner.packet(runs[13], 'scheduler')) == validation.reference_plan(runner.packet(runs[14], 'scheduler'))
            values = {'scheduler': dict(internal_order=names, office_contractor_for=None,
                hours={a: 4 for a in names}, updates={a: dict(message='Dispatch plan published.', attachments=[]) for a in names})}
        else:
            values = {a: validation.reference_commit(runner.packet(runs[13], a)) for a in names}
            assert values == {a: validation.reference_commit(runner.packet(runs[14], a)) for a in names}
        for p in paths: runs[p] = validation.submit(paths[p], stage, values)
    assert runs[13]['final'] == runs[14]['final']
    assert runs[14]['final']['privacy']['count'] > 0
    runner.archive(list(paths.values()), tmp_path / 'paired.jsonl')
    report = runner.replay(tmp_path / 'paired.jsonl')
    assert report['passed'] and report['episodes'] == 2


def test_protocol14_is_explicit_cli_opt_in(tmp_path):
    assert cli.main(['init', str(tmp_path / 'new'), '--protocol', '14']) == 0
    run = runner.read(tmp_path / 'new/run.json')
    assert run['config']['protocol'] == 14
    assert all('Remaining execution tasks' in p['files']['work/estimate.txt'] for p in run['world']['projects'].values())
