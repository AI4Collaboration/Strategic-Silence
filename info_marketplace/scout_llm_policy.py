"""LLM-powered scout policy using OpenAI Responses API with reasoning models."""

import os
import time
from openai import OpenAI

from word_play.core.components import Agent_Policy

from info_marketplace.prompts import INSTRUCTIONS, build_phase1_input, build_phase2_input
from info_marketplace.parser import parse_phase1, parse_phase2
from info_marketplace.agent_components import PrivateGoal, MemorySummary, PlanLog
from info_marketplace.marketplace_actions import ScoutAction
from info_marketplace.load_env import load_env

# Load environment variables from .env file
load_env()


class ScoutLLMPolicy(Agent_Policy):
    """LLM-powered scout using OpenAI Responses API with reasoning models.

from __future__ import annotations

    Uses the Responses API (responses.create) which differs from Chat Completions:
    - Uses `input` (not `messages`) and `instructions` (not `system`)
    - Reasoning is controlled via `reasoning={"effort": "none"|"low"|"medium"|"high"}`
    - Response text is in `response.output_text`
    """

    def __init__(
        self,
        model_name: str = "gpt-5.4-mini",
        reasoning_effort: str = "low",
        api_key: str | None = None,
    ):
        super().__init__()
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.call_log: list[dict] = []  # log all inputs/outputs for analysis

    def select_action(self, observation):
        """Not used - we use plan_and_communicate() and act() instead."""
        raise NotImplementedError("Use plan_and_communicate() and act()")

    def plan_and_communicate(
        self, observation: str, received_messages: str, round_num: int
    ) -> tuple[str, list]:
        """Phase 1: call LLM for private plan + messages."""
        agent = self.entity
        goal = agent.get_component(PrivateGoal).description
        memory = agent.get_component(MemorySummary).to_string()

        input_text = build_phase1_input(observation, goal, memory, received_messages)
        raw = self._call_llm(input_text)

        self.call_log.append(
            {
                "round": round_num,
                "phase": 1,
                "input": input_text,
                "response": raw,
                "model": self.model_name,
            }
        )

        plan, messages = parse_phase1(raw, agent.name, round_num)
        return plan, messages

    def act(self, all_messages: str, observation: str, round_num: int) -> ScoutAction:
        """Phase 2: call LLM for action choice."""
        agent = self.entity
        plan = agent.get_component(PlanLog).get_plan(round_num) or ""

        input_text = build_phase2_input(all_messages, observation, plan)
        raw = self._call_llm(input_text)

        self.call_log.append(
            {
                "round": round_num,
                "phase": 2,
                "input": input_text,
                "response": raw,
                "model": self.model_name,
            }
        )

        action = parse_phase2(raw, agent.name, round_num)
        return action

    def _call_llm(self, input_text: str) -> str:
        """Call OpenAI Responses API with retry logic.

        Uses exponential backoff: 1s, 2s, 4s on retries.

        Note: reasoning tokens count against max_output_tokens!
        - "none": ~0 reasoning tokens
        - "low": ~100-200 reasoning tokens
        - "medium": ~400-600 reasoning tokens
        - "high": ~1000+ reasoning tokens
        We use 3000 to ensure plenty of room for reasoning + visible output.
        """
        for attempt in range(3):
            try:
                response = self.client.responses.create(
                    model=self.model_name,
                    instructions=INSTRUCTIONS,
                    input=input_text,
                    reasoning={"effort": self.reasoning_effort},
                    max_output_tokens=3000,  # Large budget to avoid truncation with reasoning
                )
                return response.output_text
            except Exception as e:
                if attempt == 2:
                    return f"API_ERROR: {str(e)}"
                time.sleep(2**attempt)  # exponential backoff
        return "API_ERROR: max retries exceeded"


if __name__ == "__main__":
    from info_marketplace.agent_components import create_scout_entity, PrivateGoal

    print("=== Testing ScoutLLMPolicy ===")
    print("This will make live API calls to OpenAI.\n")

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        exit(1)

    # Create a test scout with LLM policy
    goal = PrivateGoal(
        description="Maximize your personal gold collection while keeping the settlement alive",
        goal_tier="ORTHOGONAL",
        short_label="gold_collector",
    )

    policy = ScoutLLMPolicy(model_name="gpt-5.4-mini", reasoning_effort="low")

    scout = create_scout_entity(
        name="Agent_0",
        starting_region="Forest",
        private_goal=goal,
        policy_component=policy,
    )

    print(f"Created scout: {scout.name}")
    print(f"Goal: {goal.description}")
    print(f"Model: {policy.model_name}, Reasoning effort: {policy.reasoning_effort}\n")

    # Simulate initial discovery for memory
    from info_marketplace.world import Event
    from info_marketplace.agent_components import DiscoveryLog, MemorySummary

    discovery = scout.get_component(DiscoveryLog)
    memory = scout.get_component(MemorySummary)

    test_event = Event(
        event_id="evt_001",
        event_type="RESOURCE_FOUND",
        region="Forest",
        round_generated=0,
        details={"resource": "food", "amount": 3},
    )
    discovery.record(0, "Forest", [test_event], {"food": 5, "water": 2})
    memory.update(0, "Forest", [test_event], 0, "Started exploration", "10f, 8w")

    # Test Phase 1: plan_and_communicate
    print("=== Testing Phase 1: plan_and_communicate ===\n")

    sample_observation = """Round 1 | You are in: Forest | Agents here: Agent_0, Agent_2
Resources here: 5 food, 2 water
Events here:
  - 3 food discovered.
Your inventory: 1 food, 0 water, 0 gold
Settlement: 8 food, 7 water remaining."""

    sample_received = """[PUBLIC] Agent_1 reports about River: "Found 3 water"
[PUBLIC] Agent_3 reports about Mines: "Gold deposit available" """

    print("Input observation:")
    print(sample_observation)
    print("\nReceived messages:")
    print(sample_received)
    print("\n--- Calling LLM for Phase 1 ---")

    plan, messages = policy.plan_and_communicate(sample_observation, sample_received, 1)

    print("\n=== Phase 1 Results ===")
    print(f"\nPlan: {plan}")
    print(f"\nMessages sent: {len(messages)}")
    for i, msg in enumerate(messages, 1):
        print(f"\nMessage {i}:")
        print(f"  Type: {type(msg).__name__}")
        print(f"  Public: {msg.is_public}")
        if hasattr(msg, "claim"):
            print(f"  Region: {msg.region_claimed}")
            print(f"  Claim: {msg.claim}")
        if hasattr(msg, "commitment"):
            print(f"  Target: {msg.target}")
            print(f"  Commitment: {msg.commitment}")
            print(f"  By round: {msg.by_round}")

    print(f"\n--- Raw LLM Output (Phase 1) ---")
    if policy.call_log:
        raw_output = policy.call_log[-1]["response"]
        print(raw_output)

    # Test Phase 2: act
    print("\n\n=== Testing Phase 2: act ===\n")

    sample_all_messages = """[PUBLIC] Agent_0 reports about Forest: "3 food discovered."
[PUBLIC] Agent_1 reports about River: "Found 3 water"
[PUBLIC] Agent_2 reports about Plains: "No significant resources"
[PUBLIC] Agent_3 reports about Mines: "Gold deposit available" """

    print("All messages this round:")
    print(sample_all_messages)
    print("\n--- Calling LLM for Phase 2 ---")

    action = policy.act(sample_all_messages, sample_observation, 1)

    print("\n=== Phase 2 Results ===")
    print(f"\nAction: {action.describe()}")
    print(f"Type: {action.action_type}")
    print(f"Details: {action.details}")

    print(f"\n--- Raw LLM Output (Phase 2) ---")
    if len(policy.call_log) >= 2:
        raw_output = policy.call_log[-1]["response"]
        print(raw_output)

    # Token usage analysis
    print("\n\n=== Token Usage Analysis ===")
    total_input_tokens = 0
    total_output_tokens = 0

    for i, call in enumerate(policy.call_log, 1):
        print(f"\nCall {i} (Round {call['round']}, Phase {call['phase']}):")
        input_text = call["input"]
        response_text = call["response"]

        # Rough token count (divide by 4 for approximate tokens)
        input_chars = len(input_text)
        output_chars = len(response_text)
        approx_input_tokens = input_chars // 4
        approx_output_tokens = output_chars // 4

        print(f"  Input: ~{approx_input_tokens} tokens ({input_chars} chars)")
        print(f"  Output: ~{approx_output_tokens} tokens ({output_chars} chars)")

        total_input_tokens += approx_input_tokens
        total_output_tokens += approx_output_tokens

    print(f"\nTotal (both phases):")
    print(f"  Input: ~{total_input_tokens} tokens")
    print(f"  Output: ~{total_output_tokens} tokens")
    print(f"  Total: ~{total_input_tokens + total_output_tokens} tokens")

    if total_input_tokens > 1200:
        print(f"\n⚠️  WARNING: Input tokens ({total_input_tokens}) exceed 1200 token target!")
    else:
        print(f"\n✓ Input tokens within target (<1200)")

    # Cost estimation for gpt-5.4-mini with reasoning effort "low"
    # Approximate costs (actual may vary):
    # - Input: $0.05 / 1M tokens
    # - Output (including reasoning): $0.20 / 1M tokens
    input_cost = (total_input_tokens / 1_000_000) * 0.05
    # Reasoning tokens are billed as output, so multiply output estimate by ~1.5
    output_cost = (total_output_tokens * 1.5 / 1_000_000) * 0.20
    total_cost = input_cost + output_cost

    print(f"\n=== Estimated Cost (gpt-5.4-mini, reasoning='low') ===")
    print(f"Input: ${input_cost:.6f}")
    print(f"Output (with reasoning): ${output_cost:.6f}")
    print(f"Total: ${total_cost:.6f} per round")
    print(f"Per condition (20 trials x 10 rounds x 4 agents): ${total_cost * 800:.2f}")

    print("\n=== Test Complete ===")
