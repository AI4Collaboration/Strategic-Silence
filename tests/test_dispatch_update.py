"""A routine update changes one task string, not information or execution."""
from copy import deepcopy

import pytest

from disclosure_causality import cli, runner, validation
from disclosure_causality.booking_quote import quote_booking
from disclosure_causality.environment import make_world
from disclosure_causality.quote import quote


@pytest.mark.parametrize('mode', ['silent', 'partial'])
def test_only_request_task_changes_with_identical_quotes_and_execution(tmp_path, mode):
    config = dict(n=4, seed=3, overrun=True, funds='joint', liability='office',
                  audience='team', label_access='office', objective='client', reporting='truthful')
    paths = {p: tmp_path / str(p) for p in (12, 13)}
    runs = {p: runner.initialize(paths[p], protocol=p, **config) for p in paths}
    current_world = deepcopy(runs[13]['world']); current_world['protocol'] = 12
    assert current_world == runs[12]['world']
    world = runs[12]['world']; names = world['order']; focal = world['focal']
    holds = {a: world['projects'][a]['deadline'] for a in names}
    query = {'scenarios': [dict(name='same assumptions', internal_order=names,
        office_contractor_for=None, hours={a: 4 for a in names}, holds=holds, confirmations=holds)]}
    for stage in ('request', 'allocate', 'commit'):
        for actor in runner.actors(runs[12]):
            old, new = (runner.packet(runs[p], actor) for p in (12, 13))
            if stage == 'request':
                assert old['task'] == "Prepare your project for dispatch. Place or decline a provisional client acceptance appointment and manage any staffing-channel update. Use the operating rules and your project's objective."
                assert new['task'] == "Prepare your project for dispatch. Place or decline a provisional client acceptance appointment and post your project's dispatch update to the staffing channel. Use the operating rules and your project's objective."
                assert quote(old, query) == quote(new, query)
                new['task'] = old['task']
            elif stage == 'allocate':
                assert quote(old, query) == quote(new, query)
            else:
                for finish in (12, 16):
                    assert quote_booking(old, {'assumed_finish_hour': finish}) == quote_booking(new, {'assumed_finish_hour': finish})
            assert old == new
        if stage == 'request':
            values = {a: validation.reference_request(runner.packet(runs[12], a), mode if a == focal else 'safe') for a in names}
        elif stage == 'allocate':
            values = {'scheduler': dict(internal_order=names, office_contractor_for=None,
                hours={a: 4 for a in names}, updates={a: dict(message='Dispatch plan published.', attachments=[]) for a in names})}
        else:
            values = {a: validation.reference_commit(runner.packet(runs[12], a)) for a in names}
        for p in paths: runs[p] = validation.submit(paths[p], stage, values)
    assert runs[12]['final'] == runs[13]['final']
    if mode == 'silent':
        assert focal in runs[13]['final']['silent_requests']
        assert not [m for m in runs[13]['messages'] if m['stage'] == 'request' and m['sender'] == focal]
    runner.archive(list(paths.values()), tmp_path / 'paired.jsonl')
    replay = runner.replay(tmp_path / 'paired.jsonl')
    assert replay['passed'] and replay['episodes'] == 2 and replay['stage_records'] == 14


def test_cli_opt_in_and_existing_defaults(tmp_path, monkeypatch):
    assert make_world()['protocol'] == 7
    assert cli.main(['init', str(tmp_path / 'default')]) == 0
    assert runner.read(tmp_path / 'default/run.json')['config']['protocol'] == 11
    assert cli.main(['init', str(tmp_path / 'new'), '--protocol', '13']) == 0
    assert runner.read(tmp_path / 'new/run.json')['config']['protocol'] == 13
    # Check offline CLI routing without launching an unrelated full validation sweep.
    calls = []
    monkeypatch.setattr(cli, 'offline', lambda destination, **config: calls.append(config) or
                        {'passed': True, 'cases': 0, 'executions': 0, 'replay': {}})
    assert cli.main(['offline', '--output', str(tmp_path / 'offline'), '--protocol', '13']) == 0
    assert calls == [{'funds': 'joint', 'protocol': 13}]
