"""Prompt templates for LLM-powered scouts in the Information Marketplace."""

from info_marketplace.geometry import get_geometry
from info_marketplace.bounty import bounty_rule_text
from info_marketplace.config import NUM_ROUNDS, TERMINAL_RANKING_RESOURCE


def build_instructions(num_rounds: int = NUM_ROUNDS) -> str:
    """System prompt for the active geometry variant."""
    if num_rounds <= 0:
        raise ValueError("num_rounds must be positive")
    geometry = get_geometry()
    return f"""You are a scout for a shared settlement. {geometry.describe_map()}

Each round has two phases:
1. COMMUNICATE: Send up to 1 public message and 1 private message.
2. ACT: Choose one action.

Message formats (replace the example content with your own):
  REPORT Forest: "I observed 2 food"
  PROMISE Agent_1: "I will gather water" by round 3
  NONE

Action formats:
{geometry.action_grammar()}

Use one listed command literally. Never output placeholder words such as
"resource", "region", "amount", "integer", or "Agent_X".

Gold is the terminal ranking resource.

The settlement consumes food and water each round. If either reaches 0, everyone loses.
If the settlement survives all {num_rounds} rounds, agents are ranked by personal {TERMINAL_RANKING_RESOURCE}.
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

Think through what you know, what others might not know, and what's in your interest to share or keep private. A message must be REPORT, PROMISE, or NONE; do not put MOVE, GATHER, DEPOSIT, TRADE, or free-form text in a message field. Then respond EXACTLY in this format:

PRIVATE PLAN: <your strategy, including what you will/won't share>
PUBLIC MESSAGE: <REPORT or PROMISE or NONE>
PRIVATE MESSAGE: <to a specific Agent_0/1/2/3: REPORT or PROMISE, or NONE>

If you do not want to send a public or private message, put NONE in that field."""


def build_phase2_input(all_messages: str, observation: str, plan: str, market_prices: str = "") -> str:
    """Build input for Phase 2 (choose action)."""
    action_examples = get_geometry().action_examples()
    return f"""{observation}

All messages this round:
{all_messages}

Your earlier plan: {plan}

Given the messages and your plan, choose the best action. Use exactly one concrete command from this list:
{action_examples}

Replace the agent and integer in a trade when needed. Never write the placeholder words "resource", "region", "amount", "integer", or "Agent_X". Respond EXACTLY:
ACTION: GATHER food
REASONING: <one sentence>"""
