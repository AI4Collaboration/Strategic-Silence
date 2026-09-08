"""Agent components for the Information Marketplace simulation."""

from __future__ import annotations
import copy
from word_play.core.components import Component
from word_play.core.entity import Entity
from word_play.presets.movement.single_point import Single_Point_Position

from info_marketplace.config import ADJACENCY
from info_marketplace.world import Event


class PrivateGoal(Component):
    """Component tracking an agent's private goal."""

    def __init__(self, description: str, goal_tier: str, short_label: str):
        """
        Args:
            description: Full description of the goal
            goal_tier: One of ALIGNED, ORTHOGONAL, COMPETITIVE
            short_label: Short label for the goal
        """
        super().__init__()
        assert goal_tier in ["ALIGNED", "ORTHOGONAL", "COMPETITIVE"]
        self.description = description
        self.goal_tier = goal_tier
        self.short_label = short_label


class ScoutInventory(Component):
    """Tracks personal resources."""

    def __init__(self):
        super().__init__()
        self.resources: dict[str, int] = {"food": 0, "water": 0, "gold": 0}

    def add(self, resource: str, amount: int):
        """Add resources to inventory."""
        if resource not in self.resources:
            self.resources[resource] = 0
        self.resources[resource] += amount

    def remove(self, resource: str, amount: int) -> int:
        """Remove resources, returns actual amount taken."""
        available = self.resources.get(resource, 0)
        taken = min(amount, available)
        self.resources[resource] = available - taken
        return taken

    def get_string(self) -> str:
        """Returns string representation of inventory."""
        return f"Inventory: {self.resources}"


class DiscoveryLog(Component):
    """Ground truth of what agent has personally observed."""

    def __init__(self):
        super().__init__()
        self.entries: list[dict] = []

    def record(self, round_num: int, region: str, events: list[Event], resources: dict):
        """Record an observation."""
        self.entries.append(
            {
                "round": round_num,
                "region": region,
                "events": list(events),  # Copy the list
                "resources": copy.deepcopy(resources),  # Deep copy to prevent mutations
            }
        )

    def has_observed_event(self, event_id: str) -> bool:
        """Check if agent has observed a specific event."""
        for entry in self.entries:
            for event in entry["events"]:
                if event.event_id == event_id:
                    return True
        return False

    def has_visited_region(self, region: str) -> bool:
        """Check if agent has visited a region."""
        return any(entry["region"] == region for entry in self.entries)

    def get_discoveries_about(self, region: str) -> list[dict]:
        """Get all discoveries about a specific region."""
        return [entry for entry in self.entries if entry["region"] == region]

    def get_latest_about(self, region: str) -> dict | None:
        """Get the most recent discovery about a region."""
        discoveries = self.get_discoveries_about(region)
        return discoveries[-1] if discoveries else None

    def get_discovery_at_round(self, region: str, round_num: int) -> dict | None:
        """Get the discovery for a specific round (or most recent before that round)."""
        discoveries = self.get_discoveries_about(region)
        # Find discoveries at or before the target round
        valid_discoveries = [d for d in discoveries if d["round"] <= round_num]
        return valid_discoveries[-1] if valid_discoveries else None


class RegionTracker(Component):
    """Tracks current region (NOT using Word_Play's position system)."""

    def __init__(self, starting_region: str):
        super().__init__()
        self.current_region = starting_region
        self.region_history: list[tuple[int, str]] = []

    def move_to(self, region: str, round_num: int) -> bool:
        """Move to a region, validates adjacency. Returns True if successful."""
        # Check if region is adjacent to current region
        if region not in ADJACENCY.get(self.current_region, []):
            return False

        self.current_region = region
        self.region_history.append((round_num, region))
        return True

    def record_stay(self, round_num: int):
        """Record staying in current region."""
        self.region_history.append((round_num, self.current_region))


class PlanLog(Component):
    """Stores Phase 1 private plans for premeditation analysis."""

    def __init__(self):
        super().__init__()
        self.plans: list[dict] = []

    def record(self, round_num: int, plan_text: str):
        """Record a plan for a specific round."""
        self.plans.append({"round": round_num, "plan_text": plan_text})

    def get_plan(self, round_num: int) -> str | None:
        """Get the plan for a specific round."""
        for plan in self.plans:
            if plan["round"] == round_num:
                return plan["plan_text"]
        return None


class ActionLog(Component):
    """Stores actions taken per round."""

    def __init__(self):
        super().__init__()
        self.actions: list[dict] = []

    def record(self, round_num: int, action: str, details: dict):
        """Record an action taken in a specific round."""
        self.actions.append({"round": round_num, "action": action, "details": dict(details)})


class MemorySummary(Component):
    """Rolling compressed summary of last 2 rounds for prompt injection."""

    def __init__(self):
        super().__init__()
        self.summaries: list[dict] = []

    def update(
        self,
        round_num: int,
        region: str,
        events_seen: list[Event],
        messages_sent: int,
        action: str,
        settlement_status: str,
    ):
        """Update the summary with new round information."""
        # Format events concisely
        event_strs = []
        for event in events_seen:
            if event.event_type == "RESOURCE_FOUND":
                event_strs.append(f"{event.details['resource']}({event.details['amount']})")
            elif event.event_type == "GOLD_FOUND":
                event_strs.append(f"gold({event.details['amount']})")
            elif event.event_type == "THREAT":
                event_strs.append(f"{event.details['threat_type']}!")
            elif event.event_type == "DEPLETION":
                event_strs.append(f"{event.details['resource']}_low")

        events_str = ", ".join(event_strs) if event_strs else "nothing"

        summary = {
            "round": round_num,
            "text": f"R{round_num}: In {region}, saw {events_str}. Sent {messages_sent} msg. {action}. Settlement: {settlement_status}.",
        }

        self.summaries.append(summary)

        # Keep only last 2 rounds
        if len(self.summaries) > 2:
            self.summaries = self.summaries[-2:]

    def to_string(self) -> str:
        """Returns formatted summary string."""
        if not self.summaries:
            return "No recent activity."
        return "\n".join(s["text"] for s in self.summaries)


def create_scout_entity(
    name: str, starting_region: str, private_goal: PrivateGoal, policy_component
) -> Entity:
    """Creates a scout Entity with all required components.

    Args:
        name: Agent name
        starting_region: Starting region name
        private_goal: PrivateGoal component
        policy_component: ScoutLLMPolicy or ScriptedScoutPolicy (extends Agent_Policy)

    Returns:
        Entity with all scout components
    """
    return Entity(
        name=name,
        position=Single_Point_Position(),
        actions=[],
        components=[
            policy_component,
            private_goal,
            ScoutInventory(),
            DiscoveryLog(),
            RegionTracker(starting_region),
            PlanLog(),
            ActionLog(),
            MemorySummary(),
        ],
        tags=["scout", "agent"],
    )


if __name__ == "__main__":
    from word_play.core.components import Agent_Policy
    from word_play.core.observation import Observation
    from info_marketplace.world import Event

    # Create a dummy policy for testing
    class DummyPolicy(Agent_Policy):
        def select_action(self, observation: Observation):
            return None, None

    print("=== Testing Scout Creation ===")
    goal1 = PrivateGoal(
        description="Maximize gold collection",
        goal_tier="COMPETITIVE",
        short_label="gold_maximizer",
    )

    scout1 = create_scout_entity(
        name="Agent_0",
        starting_region="Forest",
        private_goal=goal1,
        policy_component=DummyPolicy(),
    )

    print(f"Created scout: {scout1.name}")
    print(f"Tags: {scout1.tags}")
    print(f"Components: {[type(c).__name__ for c in scout1.components]}")

    print("\n=== Testing PrivateGoal ===")
    goal = scout1.get_component(PrivateGoal)
    print(f"Goal: {goal.short_label}")
    print(f"Tier: {goal.goal_tier}")
    print(f"Description: {goal.description}")

    print("\n=== Testing ScoutInventory ===")
    inventory = scout1.get_component(ScoutInventory)
    print(inventory.get_string())
    inventory.add("food", 3)
    inventory.add("gold", 2)
    print(f"After adding: {inventory.get_string()}")
    taken = inventory.remove("food", 5)
    print(f"Removed {taken} food (requested 5)")
    print(inventory.get_string())

    print("\n=== Testing DiscoveryLog ===")
    discovery = scout1.get_component(DiscoveryLog)

    event1 = Event(
        event_id="evt_001",
        event_type="RESOURCE_FOUND",
        region="Forest",
        round_generated=1,
        details={"resource": "food", "amount": 3},
    )

    event2 = Event(
        event_id="evt_002",
        event_type="GOLD_FOUND",
        region="Mines",
        round_generated=2,
        details={"resource": "gold", "amount": 2},
    )

    discovery.record(1, "Forest", [event1], {"food": 5})
    discovery.record(2, "Mines", [event2], {"gold": 3})

    print(f"Has observed evt_001: {discovery.has_observed_event('evt_001')}")
    print(f"Has observed evt_999: {discovery.has_observed_event('evt_999')}")
    print(f"Has visited Forest: {discovery.has_visited_region('Forest')}")
    print(f"Has visited Plains: {discovery.has_visited_region('Plains')}")

    latest_forest = discovery.get_latest_about("Forest")
    print(f"Latest about Forest: Round {latest_forest['round']}, Resources: {latest_forest['resources']}")

    print("\n=== Testing RegionTracker ===")
    tracker = scout1.get_component(RegionTracker)
    print(f"Current region: {tracker.current_region}")

    # Try valid move (Forest -> River)
    success = tracker.move_to("River", 1)
    print(f"Move to River (adjacent): {success}, now at {tracker.current_region}")

    # Try invalid move (River -> Plains, not adjacent)
    success = tracker.move_to("Plains", 2)
    print(f"Move to Plains (not adjacent): {success}, still at {tracker.current_region}")

    # Try valid move (River -> Mines)
    success = tracker.move_to("Mines", 2)
    print(f"Move to Mines (adjacent): {success}, now at {tracker.current_region}")

    tracker.record_stay(3)
    print(f"Region history: {tracker.region_history}")

    print("\n=== Testing PlanLog ===")
    plan_log = scout1.get_component(PlanLog)
    plan_log.record(1, "Scout Forest for resources")
    plan_log.record(2, "Move to Mines and collect gold")

    plan_r1 = plan_log.get_plan(1)
    plan_r2 = plan_log.get_plan(2)
    plan_r3 = plan_log.get_plan(3)

    print(f"Plan for round 1: {plan_r1}")
    print(f"Plan for round 2: {plan_r2}")
    print(f"Plan for round 3: {plan_r3}")

    print("\n=== Testing ActionLog ===")
    action_log = scout1.get_component(ActionLog)
    action_log.record(1, "scout", {"region": "Forest", "events_found": 1})
    action_log.record(2, "move", {"from": "Forest", "to": "River"})

    print(f"Actions logged: {len(action_log.actions)}")
    for action in action_log.actions:
        print(f"  Round {action['round']}: {action['action']} - {action['details']}")

    print("\n=== Testing MemorySummary ===")
    memory = scout1.get_component(MemorySummary)
    print(f"Initial: {memory.to_string()}")

    memory.update(1, "Forest", [event1], 2, "Moved to River", "8f, 7w")
    print(f"After round 1:\n{memory.to_string()}")

    memory.update(2, "River", [], 1, "Stayed", "6f, 6w")
    print(f"\nAfter round 2:\n{memory.to_string()}")

    memory.update(3, "Mines", [event2], 0, "Gathered gold", "4f, 5w")
    print(f"\nAfter round 3 (only last 2):\n{memory.to_string()}")

    print("\n=== Testing Multiple Scouts ===")
    scouts = []
    regions = ["Forest", "River", "Plains", "Mines"]
    for i in range(4):
        goal = PrivateGoal(
            description=f"Goal for Agent_{i}",
            goal_tier=["ALIGNED", "ORTHOGONAL", "COMPETITIVE", "ALIGNED"][i],
            short_label=f"goal_{i}",
        )
        scout = create_scout_entity(
            name=f"Agent_{i}",
            starting_region=regions[i],
            private_goal=goal,
            policy_component=DummyPolicy(),
        )
        scouts.append(scout)

    for scout in scouts:
        tracker = scout.get_component(RegionTracker)
        goal = scout.get_component(PrivateGoal)
        print(f"{scout.name}: {tracker.current_region}, Goal: {goal.goal_tier}")
