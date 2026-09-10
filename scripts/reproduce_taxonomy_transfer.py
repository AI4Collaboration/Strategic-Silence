"""Verify the frozen transfer archive and replay observations/actions offline.

Uses only the standard library. Semantic examples remain assistant-reviewed
examples, not mechanically validated intent or an exhaustive label census.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'results/taxonomy_transfer'
EXP = 'experiments/taxonomy_six_env_20260910/'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reproduce(release=RELEASE):
    manifest = json.loads((release / 'archive.json').read_text())
    archive = release / manifest['archive']
    require(sha(archive.read_bytes()) == manifest['sha256'], 'Archive hash mismatch')
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist()) == len(set(z.namelist())), 'Duplicate archive members')
        require(set(z.namelist()) == set(manifest['members']), 'Archive inventory mismatch')
        data = {name: z.read(name) for name in z.namelist()}
    for name, value in data.items():
        require(sha(value) == manifest['members'][name]['sha256'], 'Member hash mismatch: ' + name)
        require(len(value) == manifest['members'][name]['bytes'], 'Member length mismatch: ' + name)
    def read(name):
        return json.loads(data[name])
    for published, original in [('examples.json', 'verified_examples.json'),
                                ('FROZEN_CODEBOOK.md', 'FROZEN_CODEBOOK.md'),
                                ('REVIEW_STATUS.md', 'REVIEW_STATUS.md')]:
        require((release / published).read_bytes() == data[EXP + original],
                'Published evidence differs from archive: ' + published)
    cfg = read(EXP + 'protocol.json')
    for name, digest in cfg['source_hashes'].items():
        require(sha(data[name]) == digest, 'Frozen source drift: ' + name)
    groups = {}
    with tempfile.TemporaryDirectory() as tmp:
        classes = {}
        for filename, names in [('envs_a.py', ['NegotiationMarket', 'ProjectAllocation']),
                                ('envs_b.py', ['Investigation', 'RelayIncident'])]:
            path = Path(tmp) / filename
            path.write_bytes(data[EXP + filename])
            spec = importlib.util.spec_from_file_location('frozen_' + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            classes.update({name: getattr(module, name) for name in names})
        envs = dict(zip(['negotiation', 'allocation', 'investigation', 'relay_incident'],
                        [classes[n] for n in ['NegotiationMarket', 'ProjectAllocation', 'Investigation', 'RelayIncident']]))
        require(len(cfg['design']) == 48, 'Unexpected design size')
        require(len({c['id'] for c in cfg['design']}) == 48, 'Duplicate design IDs')
        require(len([n for n in data if n.startswith(EXP + 'live/') and n.endswith('.json')]) == 48,
                'Unexpected trajectory inventory')
        for case in cfg['design']:
            row = read(EXP + 'live/' + case['id'] + '.json')
            require(row['case'] == case and row['complete'], 'Incomplete or mismatched case')
            env = envs[case['environment']](case['seed'], case['condition'])
            require(env.result() == row['initial_result'], 'Initial state mismatch')
            require(len(row['turns']) == len(env.turns), 'Wrong turn count')
            for i, turn in enumerate(row['turns']):
                require(turn['index'] == i and turn['agent'] == env.turns[i], 'Turn identity mismatch')
                require(env.observe(turn['agent']) == turn['observation'], 'Observation mismatch')
                require(json.loads(turn['raw']) == turn['parsed'], 'Raw/parsed reply mismatch')
                env.step(turn['agent'], turn['parsed']['action'])
                require(env.result() == turn['state_after'], 'Transition mismatch')
            require(env.result() == row['result'], 'Final state mismatch')
            g = groups.setdefault(case['environment'], dict(episodes=0, turns=0, conditions=Counter(),
                models=Counter(), failed_game_actions=0, queries=Counter(), correct_decisions=0,
                decision_episodes=0))
            g['episodes'] += 1
            g['turns'] += len(row['turns'])
            g['conditions'][case['condition']] += 1
            g['models'][case['model']] += 1
            g['failed_game_actions'] += sum(e.get('success') is False for e in row['result']['events'])
            for t in row['turns']:
                action = t['parsed']['action']
                if action.get('type') == 'query':
                    g['queries'][action['key']] += 1
            if case['environment'] in ['investigation', 'relay_incident']:
                g['decision_episodes'] += 1
                g['correct_decisions'] += row['result']['state']['decision'] == env.correct_choice
    for g in groups.values():
        require(g['episodes'] == 12 and set(g['conditions'].values()) == {4}
                and set(g['models'].values()) == {6}, 'Unbalanced completed design')
    docrows = [json.loads(line) for line in data['paper/artifact/data/delivery_prospective.jsonl'].splitlines()]
    patterns = Counter()
    invalid = 0
    for row in docrows:
        if row['status'] != 'valid':
            invalid += 1
            continue
        deliveries = [d for e in row['events'] for d in e.get('result', {}).get('deliveries', [])]
        useful = [d for d in deliveries if d['pages'] in ['finding', 'both']]
        operator = [d for d in useful if d['recipient'] == row['outcome']['operator']]
        timely = [d for d in operator if d['tick'] <= 2]
        for key, value in [('any_message', bool(deliveries)), ('report_anywhere', bool(useful)),
                           ('operator_report', bool(operator)), ('operator_timely', bool(timely))]:
            require(row['outcome'][key] == value, 'Document delivery field mismatch: ' + key)
        pattern = ('timely_operator_report' if timely else 'late_operator_report' if operator else
                   'bystander_report' if useful else 'cover_only' if deliveries else 'no_message')
        require(pattern == row['outcome']['pattern'], 'Document outcome mismatch')
        patterns[pattern] += 1
    packets = []
    for batch in 'ABC':
        packets.extend(read(EXP + f'existing_packets/craft_trade/review_batches/craft_{batch}.json'))
    require(len(packets) == 240 and len({p['case_id'] for p in packets}) == 240, 'Craft sample inventory')
    for packet in packets:
        source = packet['source']
        require(sha(data[source['path']]) == source['sha256'], 'Craft source hash mismatch')
    for example in read(EXP + 'verified_examples.json')['examples']:
        require(sha(data[example['source']['path']]) == example['source']['sha256'], 'Example source mismatch')
    journal = [json.loads(line) for line in data[EXP + 'live/requests.jsonl'].splitlines()]
    reserves = {r['call_id']: r for r in journal if r['kind'] == 'reserve'}
    replies = {r['call_id']: r for r in journal if r['kind'] == 'response'}
    require(len(reserves) == 254 and set(reserves) == set(replies), 'Unresolved or unexpected requests')
    require(all(r['usable'] for r in replies.values()), 'Unusable response')
    accounted = sum(r['accounted_nano'] for r in replies.values())
    progress = read(EXP + 'progress.json')
    require(progress['status'] == 'completed' and progress['cost']['accounted_nano'] == accounted,
            'Budget/completion mismatch')
    cumulative = Decimal(str(cfg['prior_accounted_usd'])) + Decimal(accounted) / Decimal(10**9)
    require(cumulative <= Decimal(str(cfg['total_authorized_usd'])), 'Original budget exceeded')
    return dict(fresh_episodes=48, fresh_turns=sum(g['turns'] for g in groups.values()),
                fresh_replay_mismatches=0, environments=groups,
                document_delivery=dict(total=len(docrows), valid=sum(patterns.values()), invalid=invalid,
                                       replay_mismatches=0, outcomes=patterns),
                craft_trade=dict(sample_games=len({p['game_id'] for p in packets}), agent_round_packets=len(packets),
                                 semantic_census_complete=False),
                checked_examples=len(read(EXP + 'verified_examples.json')['examples']),
                dispatched_requests=len(reserves), collection_accounted_usd=str(Decimal(accounted)/Decimal(10**9)),
                cumulative_accounted_usd=str(cumulative), total_budget_usd=str(cfg['total_authorized_usd']),
                semantic_validation='Source integrity verified; semantic correctness and causal intent are not established by replay.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write reproduced_summary.json after successful verification')
    args = parser.parse_args()
    result = reproduce()
    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.write:
        (RELEASE / 'reproduced_summary.json').write_text(rendered)
    else:
        require(result == json.loads((RELEASE / 'reproduced_summary.json').read_text()), 'Saved summary mismatch')
    print(rendered, end='')
