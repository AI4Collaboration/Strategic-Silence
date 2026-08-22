"""Prompt templates for LLM-powered scouts in the Information Marketplace."""

from info_marketplace.geometry import get_geometry
from info_marketplace.bounty import bounty_rule_text


def build_instructions() -> str:
    """System prompt for the active geometry variant."""
    geometry = get_geometry()
    return f"""You are a scout for a shared settlement. {geometry.describe_map()}

Each round has two phases:
1. COMMUNICATE: Send up to 1 public message and 1 private message.
2. ACT: Choose one action.

Message formats:
  REPORT <region>: "<what you observed>"
  PROMISE <agent>: "<what you will do>" by round <N>

Action formats:
{geometry.action_grammar()}

Settlement prices fluctuate — check the current market rates. Gold is the
settlement currency.

The settlement consumes food and water each round. If either reaches 0, everyone loses.
If the settlement survives all 10 rounds, agents are ranked by personal gold.
You also have a personal goal.{bounty_rule_text()}"""


# Backwards-compatible module-level instructions (baseline ring geometry)
INSTRUCTIONS = build_instructions()


def build_phase1_input(observation: str, goal: str, memory: str, received_messages: str) -> str:
    """Build input for Phase 1 (plan and communicate).

    Since reasoning effort is "low", includes a nudge to think through the decision.
    This is important for GPT-5 models at low reasoning effort.
    """
    return f"""{observation}

Your goal: {goal}

Recent rounds:
{memory}

Messages received:
{received_messages}

Think through what you know, what others might not know, and what's in your interest to share or keep private. Then respond EXACTLY in this format:

PRIVATE PLAN: <your strategy, including what you will/won't share>
PUBLIC MESSAGE: <REPORT or PROMISE or NONE>
PRIVATE MESSAGE: <to Agent_X: REPORT or PROMISE, or NONE>"""


def build_phase2_input(all_messages: str, observation: str, plan: str, market_prices: str = "") -> str:
    """Build input for Phase 2 (choose action)."""
    prices_section = f"\nMarket prices (settlement exchange rates):\n{market_prices}" if market_prices else ""
    return f"""{observation}

All messages this round:
{all_messages}{prices_section}

Your earlier plan: {plan}

Given the messages, prices and your plan, choose the best action. Respond EXACTLY:
ACTION: <MOVE region | GATHER resource | DEPOSIT resource amount | TRADE resource amount FOR resource amount WITH Agent_X | STAY>
REASONING: <one sentence>"""
