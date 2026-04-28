"""Comprehensive pytest tests for parser.py."""

import pytest
from info_marketplace.parser import (
    parse_phase1,
    parse_phase2,
    normalize_region,
    normalize_resource,
)
from info_marketplace.messages import Report, Promise
from info_marketplace.marketplace_actions import ScoutAction


# ============================================================================
# Phase 1 Tests
# ============================================================================

def test_phase1_perfect_format():
    """Test perfect format with all sections."""
    text = """PRIVATE PLAN: Gather food and deposit
from __future__ import annotations

PUBLIC MESSAGE: REPORT Forest: "Found 3 food"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 1)

    assert plan == "Gather food and deposit"
    assert len(messages) == 1
    assert isinstance(messages[0], Report)
    assert messages[0].region_claimed == "Forest"
    assert messages[0].claim == "Found 3 food"


def test_phase1_lowercase_headers():
    """Test lowercase headers are handled."""
    text = """private plan: keep it secret
public message: report River: "water here"
private message: none"""

    plan, messages = parse_phase1(text, "Agent_0", 2)

    assert "secret" in plan.lower()
    assert len(messages) == 1
    assert messages[0].region_claimed == "River"


def test_phase1_both_none():
    """Test when both messages are NONE."""
    text = """PRIVATE PLAN: Just exploring
PUBLIC MESSAGE: NONE
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 3)

    assert "exploring" in plan.lower()
    assert len(messages) == 0


def test_phase1_free_form_text():
    """Test when output is free-form without headers."""
    text = """I'm going to explore the forest and gather some resources."""

    plan, messages = parse_phase1(text, "Agent_0", 4)

    assert "explore" in plan.lower() or "forest" in plan.lower()
    assert len(messages) == 0


def test_phase1_invalid_region():
    """Test invalid region name is skipped."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORT InvalidPlace: "nothing"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 5)

    assert plan == "test"
    assert len(messages) == 0  # Invalid region should be skipped


def test_phase1_private_to_agent():
    """Test private message with recipient."""
    text = """PRIVATE PLAN: coordinate
PUBLIC MESSAGE: NONE
PRIVATE MESSAGE: to Agent_2: REPORT Mines: "gold here" """

    plan, messages = parse_phase1(text, "Agent_0", 6)

    assert len(messages) == 1
    assert not messages[0].is_public
    assert messages[0].recipient == "Agent_2"


def test_phase1_two_publics():
    """Test >1 public message (should take first only)."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORT Forest: "first"
PUBLIC MESSAGE: REPORT River: "second"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 7)

    # Should only parse first public (before PRIVATE MESSAGE)
    public_msgs = [m for m in messages if m.is_public]
    assert len(public_msgs) == 1
    assert public_msgs[0].claim == "first"


def test_phase1_about_phrasing():
    """Test 'REPORT about region' phrasing."""
    text = """PRIVATE PLAN: share info
PUBLIC MESSAGE: REPORT about Plains: "found food"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 8)

    assert len(messages) == 1
    assert messages[0].region_claimed == "Plains"
    assert "food" in messages[0].claim


def test_phase1_promise_with_deadline():
    """Test PROMISE with explicit deadline."""
    text = """PRIVATE PLAN: make promise
PUBLIC MESSAGE: PROMISE Agent_3: "will scout Mines" by round 10
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 5)

    assert len(messages) == 1
    assert isinstance(messages[0], Promise)
    assert messages[0].target == "Agent_3"
    assert messages[0].by_round == 10
    assert "scout Mines" in messages[0].commitment


def test_phase1_promise_no_deadline():
    """Test PROMISE without deadline (should default to round + 3)."""
    text = """PRIVATE PLAN: promise help
PUBLIC MESSAGE: PROMISE Agent_1: "bring water"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 5)

    assert len(messages) == 1
    assert isinstance(messages[0], Promise)
    assert messages[0].by_round == 8  # 5 + 3


def test_phase1_empty_input():
    """Test empty input."""
    plan, messages = parse_phase1("", "Agent_0", 1)

    assert plan == "No output received"
    assert len(messages) == 0


def test_phase1_no_quotes_in_report():
    """Test REPORT without quotes around claim."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORT Forest: found resources here.
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 1)

    assert len(messages) == 1
    assert "resources" in messages[0].claim.lower()


def test_phase1_fuzzy_region_normalization():
    """Test fuzzy region matching (the forest, forests, etc)."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORT the Forest: "testing"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 1)

    assert len(messages) == 1
    assert messages[0].region_claimed == "Forest"


# ============================================================================
# Phase 2 Tests
# ============================================================================

def test_phase2_perfect_format():
    """Test perfect ACTION format."""
    text = """ACTION: MOVE River
REASONING: Need water urgently"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "move"
    assert action.details["destination"] == "River"


def test_phase2_gather_action():
    """Test GATHER action."""
    text = """ACTION: GATHER food
REASONING: Settlement needs food"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "gather"
    assert action.details["resource"] == "food"


def test_phase2_deposit_with_amount():
    """Test DEPOSIT with explicit amount."""
    text = """ACTION: DEPOSIT water 3
REASONING: Contribute to settlement"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "deposit"
    assert action.details["resource"] == "water"
    assert action.details["amount"] == 3


def test_phase2_deposit_without_amount():
    """Test DEPOSIT without amount (should default to 1)."""
    text = """ACTION: DEPOSIT gold
REASONING: Help settlement"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "deposit"
    assert action.details["resource"] == "gold"
    assert action.details["amount"] == 1


def test_phase2_stay_action():
    """Test STAY action."""
    text = """ACTION: STAY
REASONING: Wait for others"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "stay"
    assert action.details == {}


def test_phase2_natural_language_move():
    """Test natural language movement."""
    text = """I should head to the Mines to collect gold"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "move"
    assert action.details["destination"] == "Mines"


def test_phase2_natural_language_gather():
    """Test natural language gather."""
    text = """Let me collect some water from here"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "gather"
    assert action.details["resource"] == "water"


def test_phase2_natural_language_deposit():
    """Test natural language deposit with amount."""
    text = """I will bring 2 food to the settlement"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "deposit"
    assert action.details["resource"] == "food"
    assert action.details["amount"] == 2


def test_phase2_no_header():
    """Test output without ACTION header."""
    text = """GATHER food REASONING: needed"""

    action = parse_phase2(text, "Agent_0", 1)

    # Should fall back to natural language parsing
    assert action.action_type == "gather"
    assert action.details["resource"] == "food"


def test_phase2_invalid_region():
    """Test invalid region falls back to normalization."""
    text = """ACTION: MOVE the Forest
REASONING: explore"""

    action = parse_phase2(text, "Agent_0", 1)

    # "the Forest" should normalize to "Forest"
    assert action.action_type == "move"
    assert action.details["destination"] == "Forest"


def test_phase2_garbage_input():
    """Test completely unparseable input defaults to STAY."""
    text = """asdfasdf random garbage text blah"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "stay"


def test_phase2_multiple_actions():
    """Test multiple ACTION statements (should take first)."""
    text = """ACTION: GATHER food
ACTION: MOVE River
REASONING: test"""

    action = parse_phase2(text, "Agent_0", 1)

    # Should parse first action
    assert action.action_type == "gather"
    assert action.details["resource"] == "food"


def test_phase2_empty_input():
    """Test empty input defaults to STAY."""
    action = parse_phase2("", "Agent_0", 1)

    assert action.action_type == "stay"


# ============================================================================
# Normalization Tests
# ============================================================================

def test_normalize_region_exact_match():
    """Test exact region name matches."""
    assert normalize_region("Forest") == "Forest"
    assert normalize_region("River") == "River"
    assert normalize_region("Plains") == "Plains"
    assert normalize_region("Mines") == "Mines"


def test_normalize_region_case_insensitive():
    """Test case-insensitive matching."""
    assert normalize_region("forest") == "Forest"
    assert normalize_region("RIVER") == "River"
    assert normalize_region("pLaInS") == "Plains"


def test_normalize_region_with_article():
    """Test region with article 'the'."""
    assert normalize_region("the Forest") == "Forest"
    assert normalize_region("the forest") == "Forest"
    assert normalize_region("a river") == "River"


def test_normalize_region_with_suffix():
    """Test region with suffix."""
    assert normalize_region("Forest region") == "Forest"
    assert normalize_region("River area") == "River"


def test_normalize_region_plural():
    """Test region plural forms."""
    assert normalize_region("forests") == "Forest"
    assert normalize_region("mines") == "Mines"


def test_normalize_region_fuzzy_match():
    """Test fuzzy matching (first 3 chars)."""
    assert normalize_region("For") == "Forest"
    assert normalize_region("Riv") == "River"
    assert normalize_region("Min") == "Mines"


def test_normalize_region_invalid():
    """Test invalid region returns None."""
    assert normalize_region("InvalidPlace") is None
    assert normalize_region("xyz") is None
    assert normalize_region("") is None


def test_normalize_resource_exact():
    """Test exact resource names."""
    assert normalize_resource("food") == "food"
    assert normalize_resource("water") == "water"
    assert normalize_resource("gold") == "gold"


def test_normalize_resource_case():
    """Test case-insensitive resources."""
    assert normalize_resource("Food") == "food"
    assert normalize_resource("WATER") == "water"
    assert normalize_resource("GoLd") == "gold"


def test_normalize_resource_plural():
    """Test plural resources."""
    assert normalize_resource("foods") == "food"
    assert normalize_resource("waters") == "water"


def test_normalize_resource_fuzzy():
    """Test fuzzy resource matching."""
    assert normalize_resource("foo") == "food"
    assert normalize_resource("wat") == "water"
    assert normalize_resource("gol") == "gold"


def test_normalize_resource_invalid():
    """Test invalid resource returns None."""
    assert normalize_resource("invalid") is None
    assert normalize_resource("xyz") is None
    assert normalize_resource("") is None


# ============================================================================
# Edge Cases
# ============================================================================

def test_phase1_private_to_self():
    """Test private message to self (should parse but be flagged)."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: NONE
PRIVATE MESSAGE: to Agent_0: REPORT Forest: "secret" """

    plan, messages = parse_phase1(text, "Agent_0", 1)

    # Should still parse (logic to reject is in game layer, not parser)
    assert len(messages) == 1
    assert messages[0].recipient == "Agent_0"


def test_phase1_reports_plural():
    """Test 'REPORTS' (plural) is accepted."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: REPORTS Forest: "found stuff"
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 1)

    assert len(messages) == 1
    assert messages[0].claim == "found stuff"


def test_phase1_promises_plural():
    """Test 'PROMISES' (plural) is accepted."""
    text = """PRIVATE PLAN: test
PUBLIC MESSAGE: PROMISES Agent_2: "will help" by round 5
PRIVATE MESSAGE: NONE"""

    plan, messages = parse_phase1(text, "Agent_0", 2)

    assert len(messages) == 1
    assert isinstance(messages[0], Promise)


def test_phase2_move_with_to():
    """Test 'MOVE to region' phrasing."""
    text = """ACTION: MOVE to River
REASONING: need water"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "move"
    assert action.details["destination"] == "River"


def test_phase2_lowercase_action():
    """Test lowercase action keyword."""
    text = """action: gather food
reasoning: needed"""

    action = parse_phase2(text, "Agent_0", 1)

    assert action.action_type == "gather"
    assert action.details["resource"] == "food"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
