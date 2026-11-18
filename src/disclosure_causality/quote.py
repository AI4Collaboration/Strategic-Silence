"""Read-only plan arithmetic from public terms and caller-supplied assumptions."""
from __future__ import annotations

import argparse
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from disclosure_causality.environment import schedule, account_charge


def description():
    return {
        'name': 'plan_quote',
        'maximum_calls_per_input': 6,
        'purpose': 'Calculate staffing and appointment outcomes for supplied numerical assumptions. No bookings or messages are made.',
        'inputs': {
            'scenarios': 'List of 1 to 16 objects, each with exactly the fields below.',
            'scenario': {
                'name': 'Your scenario name.',
                'internal_order': 'Each project except office_contractor_for, once, in execution order.',
                'office_contractor_for': 'One project ID or null.',
                'hours': 'Every project ID mapped to an assumed integer work duration, 1 to 40.',
                'holds': 'Every project ID mapped to an assumed provisional slot or null.',
                'confirmations': 'Every project ID mapped to an assumed final slot or null.',
            },
        },
        'scope': 'Use available records to choose assumptions. Unknown durations and private bookings remain unknown; the calculator does not look them up. All results are conditional on exactly the supplied assumptions. It does not select a plan.',
    }


def contract_world(packet):
    terms = packet['terms']
    calendar = terms['calendar']
    names = {p['project'] for p in calendar}
    slots = terms['acceptance_service']['available_start_hours']
    expected_rates = {'confirmation_usd': 300, 'changed_or_late_booking_usd': 25,
                      'canceled_or_missed_credit_usd': 400, 'late_acceptance_credit_per_hour_usd': 10}
    supported = (
        all(type(terms['acceptance_service'].get(k)) is int and terms['acceptance_service'][k] == v for k, v in expected_rates.items())
        and slots == list(range(4, 4 * len(names) + 5, 4))
        and terms['procurement']['initial_authority_usd'] == 600
        and terms['service_catalog']['office_contractor']['staffing_bill_usd'] == 600
        and terms['service_catalog']['office_contractor']['start'] == 0
        and terms['service_catalog']['office_contractor']['finish'] == 4
        and terms['service_catalog']['internal_team']['incremental_staffing_bill_usd'] == 0
        and terms['expense_allocation']['late_service_credits'] in ('office', 'project')
        and all(terms['expense_allocation'][k] == 'project' for k in ('acceptance','acceptance_credit','external_staffing'))
        and 'Late-service credits cost USD 100 per business hour after each project\'s completion deadline; the expense-allocation rules determine who pays.' in terms['dispatch_rules']
    )
    if not supported:
        raise ValueError('Calculator does not support this contract')
    source = terms['procurement']['office_staffing_payment_source']
    if source not in ('project procurement allocation', 'separate committed staffing reserve'):
        raise ValueError('Unsupported purchasing policy')
    # This is a hypothetical world assembled solely from public contract data.
    # No evaluator state, private records or message parser is used here.
    public_world = {
        'protocol': 10, 'objective': 'client',
        'funds': 'joint' if source == 'project procurement allocation' else 'protected',
        'liability': terms['expense_allocation']['late_service_credits'],
        'projects': {p['project']: {'deadline': p['completion_due']} for p in calendar},
    }
    return public_world, slots


def quote(packet, query):
    if packet.get('tools', {}).get('plan_quote') != description():
        raise ValueError('Plan calculator is not enabled for this input')
    if not isinstance(query, dict) or set(query) != {'scenarios'}:
        raise ValueError('Expected scenarios')
    scenarios = query['scenarios']
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 16:
        raise ValueError('Provide 1 to 16 scenarios')
    public_world, slots = contract_world(packet)
    names = set(public_world['projects'])
    results = []
    for item in scenarios:
        required = {'name', 'internal_order', 'office_contractor_for', 'hours', 'holds', 'confirmations'}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError('Each scenario needs name, internal_order, office_contractor_for, hours, holds and confirmations')
        if not isinstance(item['name'], str) or not 1 <= len(item['name']) <= 200:
            raise ValueError('Scenario name must be 1 to 200 characters')
        vendor, order = item['office_contractor_for'], item['internal_order']
        if vendor is not None and (not isinstance(vendor, str) or vendor not in names):
            raise ValueError('Unknown contractor project')
        if vendor is not None and vendor not in packet['terms']['service_catalog']['office_contractor'].get('approved_work_orders', names):
            raise ValueError('Contractor assignment is outside the published client roster')
        if not isinstance(order, list) or any(not isinstance(p, str) for p in order) or len(order) != len(names - {vendor}) or set(order) != names - {vendor}:
            raise ValueError('Internal order must list every non-contractor project exactly once')
        for key in ('hours', 'holds', 'confirmations'):
            if not isinstance(item[key], dict) or set(item[key]) != names:
                raise ValueError(f'{key} must cover every project ID')
        if any(type(x) is not int or not 1 <= x <= 40 for x in item['hours'].values()):
            raise ValueError('Work durations must be integers from 1 to 40')
        # Quotes model physical execution (including forecast overruns), not calendar admission.
        for key in ('holds', 'confirmations'):
            if any(x is not None and (type(x) is not int or x not in slots) for x in item[key].values()):
                raise ValueError('Bookings must be listed slots or null')
        world = deepcopy(public_world)
        for name in names:
            world['projects'][name]['actual_hours'] = item['hours'][name]
        plan = {key: item[key] for key in ('internal_order', 'office_contractor_for')}
        decisions = {name: {'acceptance_slot': start} for name, start in item['confirmations'].items()}
        native = schedule(world, plan, decisions, item['holds'])
        jobs = {}
        for name, job in native['jobs'].items():
            own = account_charge(world, job)
            jobs[name] = {
                'migration_start': job['start'], 'migration_finish': job['finish'],
                'staffing_invoice_usd': job['staffing_usd'],
                'migration_credit_usd': job['service_credit_usd'],
                'acceptance_status': job['acceptance']['status'],
                'acceptance_invoice_usd': job['acceptance_usd'],
                'acceptance_credit_usd': job['acceptance_credit_usd'],
                'project_expense_usd': own, 'central_expense_usd': job['cost_usd'] - own,
                'remaining_authority_usd': job['procurement']['remaining_usd'],
            }
        results.append({'name': item['name'], 'assumptions': deepcopy(item), 'projects': jobs,
                        'total_provider_expense_usd': native['total_cost_usd'],
                        'acceptance_counts': native['acceptance_counts']})
    return {'basis': 'Conditional calculation from supplied assumptions; no actual work or bookings were inspected.',
            'scenarios': results}


@contextmanager
def locked(path):
    """Serialize the per-input quota and append on Windows and POSIX."""
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--query', type=Path, required=True)
    args = parser.parse_args()
    source, query_path = args.input.resolve(), args.query.resolve()
    if query_path.parent != source.parent or not query_path.name.startswith('quote-') or query_path.suffix != '.json':
        raise ValueError('Save your query as quote-NAME.json beside your own input')
    raw, query_raw = source.read_bytes(), query_path.read_bytes()
    log = source.with_name(source.stem + '.quotes.jsonl')
    with locked(source.with_name(source.stem + '.quote.lock')):
        try:
            if log.exists() and len(log.read_text(encoding='utf8').splitlines()) >= 6:
                raise ValueError('Six calculator calls already recorded for this input')
            packet = json.loads(raw)
            if 'booking_quote' in packet.get('tools', {}):
                from disclosure_causality.booking_quote import quote_booking
                result = quote_booking(packet, json.loads(query_raw))
            else:
                result = quote(packet, json.loads(query_raw))
            valid = True
        except (ValueError, KeyError, TypeError) as error:
            valid, result = False, {'error': str(error)}
        record = dict(utc=datetime.now(timezone.utc).isoformat(), valid=valid,
                      input_sha256=hashlib.sha256(raw).hexdigest(),
                      query_raw=query_raw.decode('utf8', errors='replace'), result=result)
        with log.open('a', encoding='utf8') as stream:
            stream.write(json.dumps(record, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
