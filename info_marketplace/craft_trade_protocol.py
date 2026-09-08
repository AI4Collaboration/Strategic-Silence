"""Strict communication parsing for the paper-style craft/trade runner."""
import re
from info_marketplace.messages import CommunicationChoice, CommunicationType
from info_marketplace.parser import parse_phase1

def parse_communication(raw, agent, round_num, elicitation):
    """Strict envelope around the legacy content parser; failures are not silence."""
    plan_pattern = r"PRIVATE\s+PLAN\s*:\s*(?P<plan>.+?)\s*" if elicitation != "no_plan" else ""
    pattern = (plan_pattern + r"PUBLIC\s+MESSAGE\s*:\s*(?P<public>.+?)\s*"
               r"PRIVATE\s+MESSAGE\s*:\s*(?P<private>.+?)\s*")
    match = re.fullmatch(pattern, raw.strip(), re.I | re.S)
    invalid = CommunicationChoice(agent, round_num, CommunicationType.NONE, CommunicationType.NONE)
    if not match:
        return "", [], invalid, False
    fields = match.groupdict()
    # Multiple envelopes or empty fields must not be hidden in a parsed message.
    if any(re.search(r"(?:PRIVATE PLAN|PUBLIC MESSAGE|PRIVATE MESSAGE)\s*:", value, re.I)
           for value in fields.values()):
        return "", [], invalid, False
    source = raw if elicitation != "no_plan" else "PRIVATE PLAN: unused\n" + raw
    plan, messages, choice = parse_phase1(source, agent, round_num)
    for channel, public in (("public", True), ("private", False)):
        field = fields[channel].strip()
        delivered = [m for m in messages if m.is_public == public]
        if field.upper() == "NONE":
            if delivered:
                return "", [], invalid, False
        elif len(delivered) != 1 or not re.match(
            r"(?:REPORT|PROMISE)\b" if public else r"to\s+Agent_[0-3]\s*:\s*(?:REPORT|PROMISE)\b",
            field, re.I
        ):
            return "", [], invalid, False
        elif not public:
            recipient = re.match(r"to\s+(Agent_[0-3])", field, re.I)[1]
            actual = getattr(delivered[0], "recipient", getattr(delivered[0], "target", None))
            if recipient.lower() == agent.lower() or actual is None or actual.lower() != recipient.lower():
                return "", [], invalid, False
    return ("" if elicitation == "no_plan" else plan), messages, choice, True
