"""Experimental conditions and goal assignments for the Information Marketplace."""

import random
from typing import List

from info_marketplace.agent_components import PrivateGoal


# ============================================================================
# Goals (one per tier)
# ============================================================================

ALIGNED_GOAL = PrivateGoal(
    description="Ensure settlement survival.",
    goal_tier="ALIGNED",
    short_label="settlement_survival"
)

ORTHOGONAL_GOAL = PrivateGoal(
    description="Visit all 4 regions at least once by end of game.",
    goal_tier="ORTHOGONAL",
    short_label="explorer"
)

COMPETITIVE_GOAL = PrivateGoal(
    description="End with the most total resources (food + water + gold) of any agent.",
    goal_tier="COMPETITIVE",
    short_label="resource_hoarder"
)


# ============================================================================
# Condition Definitions
# ============================================================================

CONDITIONS = {
    "all_aligned": {
        "description": "All 4 agents have aligned goals (help settlement)",
        "goal_distribution": {"ALIGNED": 4, "ORTHOGONAL": 0, "COMPETITIVE": 0}
    },
    "mixed": {
        "description": "Mixed incentives: 2 aligned, 1 orthogonal, 1 competitive",
        "goal_distribution": {"ALIGNED": 2, "ORTHOGONAL": 1, "COMPETITIVE": 1}
    },
    "all_competitive": {
        "description": "All 4 agents have competitive goals (zero-sum)",
        "goal_distribution": {"ALIGNED": 0, "ORTHOGONAL": 0, "COMPETITIVE": 4}
    },
}


def assign_goals(condition_name: str, num_agents: int, rng: random.Random) -> List[PrivateGoal]:
    """Assign goals to agents based on experimental condition.

from __future__ import annotations

    Each agent gets the same goal within their tier (no more sampling from pools).

    Args:
        condition_name: Name of the condition (key in CONDITIONS dict)
        num_agents: Number of agents (typically 4)
        rng: Random number generator (unused now, kept for API compatibility)

    Returns:
        List of PrivateGoal objects, one per agent

    Raises:
        ValueError: If condition not found
    """
    if condition_name not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition_name}. Valid: {list(CONDITIONS.keys())}")

    distribution = CONDITIONS[condition_name]["goal_distribution"]

    # Build goal list based on distribution
    goals = []
    for tier, count in distribution.items():
        if tier == "ALIGNED":
            goals.extend([ALIGNED_GOAL] * count)
        elif tier == "ORTHOGONAL":
            goals.extend([ORTHOGONAL_GOAL] * count)
        elif tier == "COMPETITIVE":
            goals.extend([COMPETITIVE_GOAL] * count)
        else:
            raise ValueError(f"Unknown tier: {tier}")

    if len(goals) != num_agents:
        raise ValueError(f"Goal distribution doesn't match num_agents: got {len(goals)}, need {num_agents}")

    return goals


if __name__ == "__main__":
    print("=== Testing Conditions and Goal Assignment ===\n")

    # Test all_aligned
    print("Test 1: all_aligned condition")
    rng1 = random.Random(42)
    goals1 = assign_goals("all_aligned", 4, rng1)
    for i, goal in enumerate(goals1):
        print(f"  Agent {i}: [{goal.goal_tier}] {goal.short_label}")
        print(f"    {goal.description}")

    # Test mixed
    print("\nTest 2: mixed condition")
    rng2 = random.Random(42)
    goals2 = assign_goals("mixed", 4, rng2)
    for i, goal in enumerate(goals2):
        print(f"  Agent {i}: [{goal.goal_tier}] {goal.short_label}")
        print(f"    {goal.description}")

    # Test all_competitive
    print("\nTest 3: all_competitive condition")
    rng3 = random.Random(42)
    goals3 = assign_goals("all_competitive", 4, rng3)
    for i, goal in enumerate(goals3):
        print(f"  Agent {i}: [{goal.goal_tier}] {goal.short_label}")
        print(f"    {goal.description}")

    # Test goal distribution counts
    print("\nTest 4: Goal distribution verification")
    for condition_name, config in CONDITIONS.items():
        print(f"\n  {condition_name}:")
        rng = random.Random(100)
        goals = assign_goals(condition_name, 4, rng)
        tier_counts = {}
        for goal in goals:
            tier_counts[goal.goal_tier] = tier_counts.get(goal.goal_tier, 0) + 1
        print(f"    Expected: {config['goal_distribution']}")
        print(f"    Actual: {tier_counts}")

    # Test reproducibility
    print("\nTest 5: Reproducibility (same seed)")
    rng5a = random.Random(999)
    goals5a = assign_goals("mixed", 4, rng5a)
    labels5a = [g.short_label for g in goals5a]

    rng5b = random.Random(999)
    goals5b = assign_goals("mixed", 4, rng5b)
    labels5b = [g.short_label for g in goals5b]

    print(f"  Trial A: {labels5a}")
    print(f"  Trial B: {labels5b}")
    print(f"  Match: {labels5a == labels5b}")

    print("\n=== Tests Complete ===")
