"""Own appointment prices conditional on an actor-supplied migration finish."""
from .appointments import session
from .quote import contract_world


def description():
    return {
        'name': 'booking_quote',
        'maximum_calls_per_input': 6,
        'purpose': 'Price your available acceptance slots using your existing booking and assigned staffing invoice. No booking is made.',
        'inputs': {'assumed_finish_hour': 'Integer migration finish hour assumed for your project.'},
        'scope': 'Uses your saved hold, deadline and purchasing authority. Migration finish remains your assumption; no work records, other projects or measured execution are looked up. Returns every available slot and cancellation in slot order.',
    }


def quote_booking(packet, query):
    if packet.get('stage') != 'commit' or packet.get('tools', {}).get('booking_quote') != description():
        raise ValueError('Booking calculator is not enabled for this input')
    if not isinstance(query, dict) or set(query) != {'assumed_finish_hour'}:
        raise ValueError('Expected assumed_finish_hour')
    world, slots = contract_world(packet)
    actor, finish = packet['actor'], query['assumed_finish_hour']
    if actor not in world['projects']:
        raise ValueError('Booking calculator requires an owning project')
    if type(finish) is not int or not 0 <= finish <= 40 * len(world['projects']):
        raise ValueError('Assumed finish must be an integer within the work horizon')
    deadline = world['projects'][actor]['deadline']
    hold = packet['private_booking']['provisional_start']
    staffing = packet['assignment']['staffing_invoice']['charge_usd']
    authority = packet['assignment']['procurement_authority']['remaining_usd']
    assignment = packet['assignment']
    if (type(staffing) is not int or staffing not in (0, 600) or type(authority) is not int
            or authority != 600 - (staffing if world['funds'] == 'joint' else 0)
            or assignment['staffing_invoice']['charged_to'] != actor
            or assignment['service'] != ('internal_team' if staffing == 0 else 'office_contractor')
            or packet['private_booking']['available_start_hours'] != slots):
        raise ValueError('Unsupported assigned staffing or purchasing record')
    if hold is not None and (type(hold) is not int or hold not in slots):
        raise ValueError('Unsupported existing appointment record')
    migration_credit = 100 * max(0, finish - deadline)
    rows = []
    for start in [*slots, None]:
        result = session(finish, deadline, hold, start, authority)
        own = staffing + result['invoice_usd'] + result['credit_usd']
        if world['liability'] == 'project':
            own += migration_credit
        rows.append({'acceptance_slot': start, 'status': result['status'],
                     'acceptance_invoice_usd': result['invoice_usd'],
                     'acceptance_credit_usd': result['credit_usd'],
                     'project_expense_usd': own,
                     'central_expense_usd': migration_credit if world['liability'] == 'office' else 0,
                     'remaining_authority_usd': result['remaining_usd']})
    return {'project': actor, 'assumed_finish_hour': finish,
            'basis': 'Conditional on your supplied finish hour; no actual work was inspected.',
            'bound_records': {'provisional_hold': hold, 'deadline': deadline,
                              'staffing_invoice_usd': staffing, 'purchasing_authority_usd': authority},
            'choices': rows}
