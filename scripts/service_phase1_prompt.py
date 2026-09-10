"""Frozen phase-one template used by the service study; independent of world rules."""
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
