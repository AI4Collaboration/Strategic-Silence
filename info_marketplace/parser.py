"""Robust parser for LLM outputs in the Information Marketplace."""

import re
import logging
from info_marketplace.messages import Report, Promise
from info_marketplace.marketplace_actions import ScoutAction
from info_marketplace.config import REGION_NAMES

logger = logging.getLogger(__name__)


def parse_phase1(raw_output: str, agent_name: str, round_num: int) -> tuple[str, list]:
    """Parse Phase 1 LLM output into plan and messages with robust fallbacks.

from __future__ import annotations

    Expected format:
    PRIVATE PLAN: <strategy text>
    PUBLIC MESSAGE: <REPORT region: "claim" | PROMISE agent: "commitment" by round N | NONE>
    PRIVATE MESSAGE: <to Agent_X: REPORT region: "claim" | PROMISE agent: "commitment" by round N | NONE>

    Fallbacks:
    - No headers → entire text is plan, no messages
    - Garbled headers → fuzzy match
    - Invalid region → skip message
    - >1 public → first only

    Returns:
        tuple of (plan_text, list of Report/Promise objects)
    """
    try:
        messages = []
        raw_output = raw_output.strip()

        if not raw_output:
            return "No output received", []

        # Try structured parsing first
        plan, pub_msg, priv_msg = _extract_sections(raw_output)

        # If no clear structure, treat entire output as plan
        if plan is None and pub_msg is None and priv_msg is None:
            logger.warning(f"No clear sections found in Phase 1 output for {agent_name}")
            return raw_output[:200] if len(raw_output) > 200 else raw_output, []

        # Extract plan
        if plan is None:
            plan = "No plan specified"

        # Parse public message
        if pub_msg:
            msg = _parse_message(pub_msg, agent_name, round_num, is_public=True, recipient=None)
            if msg:
                messages.append(msg)

        # Parse private message
        if priv_msg:
            # Extract recipient
            recipient = _extract_recipient(priv_msg)
            msg = _parse_message(priv_msg, agent_name, round_num, is_public=False, recipient=recipient)
            if msg:
                messages.append(msg)

        return plan.strip(), messages

    except Exception as e:
        logger.error(f"Failed to parse Phase 1 output for {agent_name}: {e}")
        return f"PARSE_FAILED: {raw_output[:200]}", []


def parse_phase2(raw_output: str, agent_name: str, round_num: int) -> ScoutAction:
    """Parse Phase 2 LLM output into action with natural language fallback.

    Expected format:
    ACTION: <MOVE region | GATHER resource | DEPOSIT resource amount | STAY>
    REASONING: <one sentence>

    Fallbacks:
    - No ACTION header → scan for keywords in natural language
    - Invalid region → try normalize_region()
    - Missing amount in DEPOSIT → default to 1
    - Unparseable → return STAY

    Returns:
        ScoutAction object (never fails, defaults to STAY)
    """
    try:
        raw_output = raw_output.strip()

        if not raw_output:
            logger.warning(f"Empty Phase 2 output for {agent_name}")
            return ScoutAction(action_type="stay", details={})

        # Try structured parsing first
        action = _parse_structured_action(raw_output)
        if action:
            return action

        # Fallback: natural language parsing
        action = _parse_natural_language_action(raw_output)
        if action:
            logger.info(f"Used natural language fallback for {agent_name}: {action.describe()}")
            return action

        # Ultimate fallback
        logger.warning(f"Could not parse Phase 2 output for {agent_name}, defaulting to STAY")
        return ScoutAction(action_type="stay", details={})

    except Exception as e:
        logger.error(f"Failed to parse Phase 2 output for {agent_name}: {e}")
        return ScoutAction(action_type="stay", details={})


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_sections(text: str) -> tuple[str | None, str | None, str | None]:
    """Extract PRIVATE PLAN, PUBLIC MESSAGE, PRIVATE MESSAGE sections.

    Returns:
        (plan, public_message, private_message) - any can be None
    """
    # Try exact headers first
    plan_match = re.search(
        r'PRIVATE\s+PLAN\s*:\s*(.+?)(?=PUBLIC\s+MESSAGE|PRIVATE\s+MESSAGE|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    pub_match = re.search(
        r'PUBLIC\s+MESSAGE\s*:\s*(.+?)(?=PRIVATE\s+MESSAGE|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    priv_match = re.search(
        r'PRIVATE\s+MESSAGE\s*:\s*(.+?)$',
        text,
        re.DOTALL | re.IGNORECASE
    )

    plan = plan_match.group(1).strip() if plan_match else None
    pub_msg = pub_match.group(1).strip() if pub_match else None
    priv_msg = priv_match.group(1).strip() if priv_match else None

    # Fuzzy match if exact failed
    if plan is None and pub_msg is None and priv_msg is None:
        # Try looser patterns
        plan_match = re.search(r'plan\s*[:\-]\s*(.+?)(?=message|$)', text, re.DOTALL | re.IGNORECASE)
        if plan_match:
            plan = plan_match.group(1).strip()

    return plan, pub_msg, priv_msg


def _extract_recipient(text: str) -> str | None:
    """Extract recipient from private message text."""
    # Pattern: "to Agent_X" or "Agent_X:" at start
    recipient_match = re.search(r'(?:to\s+)?(Agent_\d+)', text, re.IGNORECASE)
    return recipient_match.group(1) if recipient_match else None


def _parse_message(text: str, sender: str, round_num: int, is_public: bool, recipient: str | None):
    """Parse a single message (REPORT or PROMISE or NONE)."""
    text = text.strip()

    # Check for NONE
    if re.match(r'^NONE\s*$', text, re.IGNORECASE) or not text:
        return None

    # Try REPORT first
    report = _parse_report(text, sender, round_num, is_public, recipient)
    if report:
        return report

    # Try PROMISE
    promise = _parse_promise(text, sender, round_num, is_public, recipient)
    if promise:
        return promise

    # No valid message found
    logger.warning(f"Could not parse message: {text[:100]}")
    return None


def _parse_report(text: str, sender: str, round_num: int, is_public: bool, recipient: str | None) -> Report | None:
    """Parse a REPORT message.

    Formats supported:
    - REPORT <region>: "<claim>"
    - REPORT about <region>: "<claim>"
    - Reports <region>: "<claim>"
    """
    # Standard format - capture multi-word regions like "the Forest"
    report_match = re.search(
        r'REPORTS?\s+(?:about\s+)?([^:]+?)\s*:\s*["\'](.+?)["\']',
        text,
        re.IGNORECASE
    )

    if not report_match:
        # Try without quotes
        report_match = re.search(
            r'REPORTS?\s+(?:about\s+)?([^:]+?)\s*:\s*(.+?)(?:\.|$)',
            text,
            re.IGNORECASE
        )

    if report_match:
        region_raw = report_match.group(1)
        claim = report_match.group(2).strip().strip('"\'')

        # Normalize region
        region = normalize_region(region_raw)
        if not region:
            logger.warning(f"Invalid region in REPORT: {region_raw}")
            return None

        return Report(
            sender=sender,
            region_claimed=region,
            claim=claim,
            is_public=is_public,
            recipient=recipient,
            round_sent=round_num,
        )

    return None


def _parse_promise(text: str, sender: str, round_num: int, is_public: bool, recipient: str | None) -> Promise | None:
    """Parse a PROMISE message.

    Formats supported:
    - PROMISE <agent>: "<commitment>" by round <N>
    - PROMISE to <agent>: "<commitment>" by round <N>
    - to <agent>: PROMISE "<commitment>" by round <N>  (LLM variant)
    - PROMISE <agent>: "<commitment>" (defaults to round_num + 3)
    """
    # Format 1: Standard format with deadline
    # PROMISE [to] Agent_X: "text" by round N
    promise_match = re.search(
        r'PROMISES?\s+(?:to\s+)?(Agent_\d+)\s*:\s*["\'](.+?)["\'].*?by\s+round\s+(\d+)',
        text,
        re.IGNORECASE
    )

    if promise_match:
        target = promise_match.group(1)
        commitment = promise_match.group(2).strip()
        by_round = int(promise_match.group(3))

        return Promise(
            sender=sender,
            target=target,
            commitment=commitment,
            by_round=by_round,
            round_sent=round_num,
            is_public=is_public,
        )

    # Format 2: Reversed format with deadline (LLM sometimes produces this)
    # to Agent_X: PROMISE "text" by round N
    promise_match = re.search(
        r'(?:to\s+)?(Agent_\d+)\s*:\s*PROMISES?\s+["\'](.+?)["\'].*?by\s+round\s+(\d+)',
        text,
        re.IGNORECASE
    )

    if promise_match:
        target = promise_match.group(1)
        commitment = promise_match.group(2).strip()
        by_round = int(promise_match.group(3))

        return Promise(
            sender=sender,
            target=target,
            commitment=commitment,
            by_round=by_round,
            round_sent=round_num,
            is_public=is_public,
        )

    # Format 3: Standard without deadline (default to +3 rounds)
    promise_match = re.search(
        r'PROMISES?\s+(?:to\s+)?(Agent_\d+)\s*:\s*["\'](.+?)["\']',
        text,
        re.IGNORECASE
    )

    if promise_match:
        target = promise_match.group(1)
        commitment = promise_match.group(2).strip()

        return Promise(
            sender=sender,
            target=target,
            commitment=commitment,
            by_round=round_num + 3,  # Default deadline
            round_sent=round_num,
            is_public=is_public,
        )

    # Format 4: Reversed without deadline
    # to Agent_X: PROMISE "text"
    promise_match = re.search(
        r'(?:to\s+)?(Agent_\d+)\s*:\s*PROMISES?\s+["\'](.+?)["\']',
        text,
        re.IGNORECASE
    )

    if promise_match:
        target = promise_match.group(1)
        commitment = promise_match.group(2).strip()

        return Promise(
            sender=sender,
            target=target,
            commitment=commitment,
            by_round=round_num + 3,  # Default deadline
            round_sent=round_num,
            is_public=is_public,
        )

    return None


def _parse_structured_action(text: str) -> ScoutAction | None:
    """Parse structured ACTION: format."""
    # Extract ACTION line
    action_match = re.search(r'ACTION\s*:\s*(.+?)(?=REASONING|$)', text, re.DOTALL | re.IGNORECASE)
    if not action_match:
        return None

    action_text = action_match.group(1).strip()

    # Parse MOVE - capture multi-word regions like "the Forest"
    move_match = re.match(r'MOVE\s+(?:to\s+)?(.+?)$', action_text, re.IGNORECASE)
    if move_match:
        region_raw = move_match.group(1).strip()
        region = normalize_region(region_raw)
        if region:
            return ScoutAction(action_type="move", details={"destination": region})

    # Parse GATHER
    gather_match = re.match(r'GATHER\s+(\w+)', action_text, re.IGNORECASE)
    if gather_match:
        resource_raw = gather_match.group(1)
        resource = normalize_resource(resource_raw)
        if resource:
            return ScoutAction(action_type="gather", details={"resource": resource})

    # Parse DEPOSIT
    deposit_match = re.match(r'DEPOSIT\s+(\w+)(?:\s+(\d+))?', action_text, re.IGNORECASE)
    if deposit_match:
        resource_raw = deposit_match.group(1)
        amount = int(deposit_match.group(2)) if deposit_match.group(2) else 1  # Default to 1

        resource = normalize_resource(resource_raw)
        if resource:
            return ScoutAction(action_type="deposit", details={"resource": resource, "amount": amount})

    # Parse STAY
    if re.match(r'STAY', action_text, re.IGNORECASE):
        return ScoutAction(action_type="stay", details={})

    return None


def _parse_natural_language_action(text: str) -> ScoutAction | None:
    """Fallback: parse natural language action descriptions."""
    text_lower = text.lower()

    # Check for movement keywords FIRST (before gather, to avoid "head to Mines to collect" matching collect)
    for region in REGION_NAMES:
        region_lower = region.lower()
        patterns = [
            rf'(?:move|go|head|travel)\s+(?:to\s+)?(?:the\s+)?{region_lower}',  # Allow "the"
            rf'{region_lower}\s+(?:next|now)',
        ]
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return ScoutAction(action_type="move", details={"destination": region})

    # Check for gather keywords
    resources = ["food", "water", "gold"]
    for resource in resources:
        patterns = [
            rf'(?:gather|collect|get|take)\s+(?:some\s+|a\s+)?{resource}',  # Allow "some" or "a"
            rf'{resource}\s+(?:here|now)',
        ]
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return ScoutAction(action_type="gather", details={"resource": resource})

    # Check for deposit keywords
    for resource in resources:
        patterns = [
            rf'(?:deposit|give|bring|contribute)\s+(\d+\s+)?{resource}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Try to extract amount
                amount_match = re.search(rf'(\d+)\s+{resource}', text_lower)
                amount = int(amount_match.group(1)) if amount_match else 1
                return ScoutAction(action_type="deposit", details={"resource": resource, "amount": amount})

    # Check for stay keywords
    if re.search(r'\b(?:stay|wait|nothing|pass)\b', text_lower):
        return ScoutAction(action_type="stay", details={})

    return None


def normalize_region(text: str) -> str | None:
    """Normalize region name to match REGION_NAMES.

    Handles: "the forest", "Forest region", "forests", etc.
    """
    if not text:
        return None

    text_clean = text.strip().lower()

    # Remove common prefixes/suffixes
    text_clean = re.sub(r'^(?:the\s+|a\s+)', '', text_clean)
    text_clean = re.sub(r'(?:\s+region|\s+area)$', '', text_clean)
    text_clean = re.sub(r's$', '', text_clean)  # Remove plural 's'

    # Match against known regions
    for region in REGION_NAMES:
        if text_clean == region.lower():
            return region

    # Fuzzy match: starts with
    for region in REGION_NAMES:
        if text_clean.startswith(region.lower()[:3]):  # Match first 3 chars
            return region

    logger.warning(f"Could not normalize region: {text}")
    return None


def normalize_resource(text: str) -> str | None:
    """Normalize resource name to food/water/gold.

    Handles: "foods", "waters", "golds", etc.
    """
    if not text:
        return None

    text_clean = text.strip().lower()

    # Remove plural 's'
    text_clean = re.sub(r's$', '', text_clean)

    valid_resources = ["food", "water", "gold"]

    if text_clean in valid_resources:
        return text_clean

    # Fuzzy match
    for resource in valid_resources:
        if text_clean.startswith(resource[:3]):
            return resource

    logger.warning(f"Could not normalize resource: {text}")
    return None


if __name__ == "__main__":
    # Quick manual tests
    logging.basicConfig(level=logging.INFO)

    print("=== Testing Phase 1 Parser ===\n")

    # Test 1: Perfect format
    test1 = """PRIVATE PLAN: I will gather food and help the settlement.
PUBLIC MESSAGE: REPORT Forest: "Found 3 food and 2 water"
PRIVATE MESSAGE: NONE"""

    plan1, msgs1 = parse_phase1(test1, "Agent_0", 1)
    print(f"Test 1 (perfect format):")
    print(f"  Plan: {plan1}")
    print(f"  Messages: {len(msgs1)}")
    for msg in msgs1:
        print(f"    - {type(msg).__name__}: {getattr(msg, 'claim', getattr(msg, 'commitment', ''))}")

    # Test 2: Lowercase headers
    test2 = """private plan: keep gold plans secret
public message: report River: "water available"
private message: none"""

    plan2, msgs2 = parse_phase1(test2, "Agent_0", 2)
    print(f"\nTest 2 (lowercase):")
    print(f"  Plan: {plan2}")
    print(f"  Messages: {len(msgs2)}")

    # Test 3: Invalid region
    test3 = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORT InvalidPlace: "nothing here"
PRIVATE MESSAGE: NONE"""

    plan3, msgs3 = parse_phase1(test3, "Agent_0", 3)
    print(f"\nTest 3 (invalid region):")
    print(f"  Plan: {plan3}")
    print(f"  Messages: {len(msgs3)} (should be 0)")

    print("\n=== Testing Phase 2 Parser ===\n")

    # Test 4: Perfect format
    test4 = """ACTION: MOVE River
REASONING: Need water"""

    action4 = parse_phase2(test4, "Agent_0", 1)
    print(f"Test 4 (perfect): {action4.describe()}")

    # Test 5: Natural language
    test5 = """I should head to the Mines to collect some gold"""

    action5 = parse_phase2(test5, "Agent_0", 2)
    print(f"Test 5 (natural language): {action5.describe()}")

    # Test 6: Garbage input
    test6 = """asdfasdfasdf random text blah blah"""

    action6 = parse_phase2(test6, "Agent_0", 3)
    print(f"Test 6 (garbage): {action6.describe()} (should be Stay)")

    print("\n=== Manual Tests Complete ===")
