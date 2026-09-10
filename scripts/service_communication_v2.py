"""Versioned service communication parser; syntax normalization never guesses routing."""
import re
from scripts import run_service_original_protocol as original

FORMAT = '''
Private-message format: use exactly NONE, or exactly one of:
PRIVATE MESSAGE: to Agent_0: REPORT <message>
PRIVATE MESSAGE: to Agent_0: PROMISE <message>
PRIVATE MESSAGE: to Agent_1: REPORT <message>
PRIVATE MESSAGE: to Agent_1: PROMISE <message>
Use only one recipient in this field. To address both clients, use PUBLIC MESSAGE.
Do not put REPORT or PROMISE before the recipient. Keep the colon after the recipient.
'''


def parse(raw, mode):
    # Validate the envelope/public field with the original parser before normalizing.
    parts = raw.rsplit('PRIVATE MESSAGE:', 1)
    if len(parts) != 2:
        return original.parse(raw, mode)
    original.parse(parts[0] + 'PRIVATE MESSAGE: NONE', mode)
    private = parts[1].strip()
    if private == 'NONE':
        return original.parse(raw, mode)
    match = re.fullmatch(r'(?:to\s+)?(Agent_[01])(?:\s*:\s*|\s+)((?:REPORT|PROMISE)\b.+)', private, re.S)
    if not match:
        raise ValueError('Invalid private recipient or message')
    # Reject additional address syntax rather than guessing a second delivery.
    if re.search(r'\bto\s+Agent_\d+\b|\bAgent_\d+\s*:', match[2]):
        raise ValueError('Multiple private recipients')
    canonical = parts[0] + 'PRIVATE MESSAGE: to ' + match[1] + ': ' + match[2]
    result = original.parse(canonical, mode)
    result['format_normalization'] = dict(version='service_communication_v2',
        changed=canonical.strip()!=raw.strip(),original_private_field=private,
        canonical_private_field='to '+match[1]+': '+match[2])
    return result


def communicate(world, history):
    from scripts.run_service_gpt54_pairs import communicate as baseline
    return baseline(world, history) + '\n' + FORMAT


def trial(spec, call):
    """New runs opt into v2; baseline runs retain the strict v1 defaults."""
    from scripts.run_service_gpt54_pairs import trial as baseline
    row = baseline(spec, call, communication_parser=parse, communication_prompt=communicate)
    row['communication_protocol'] = 'service_communication_v2'
    return row
