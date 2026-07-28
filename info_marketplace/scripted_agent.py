"""Scripted agent policies for the Information Marketplace simulation."""

from word_play.core.components import Agent_Policy

from info_marketplace.marketplace_actions import ScoutAction
from info_marketplace.messages import CommunicationType, CommunicationChoice, Report, Promise
from info_marketplace.agent_components import (
    DiscoveryLog,
    RegionTracker,
    ScoutInventory,
)
from info_marketplace.config import ADJACENCY


class ScriptedScoutPolicy(Agent_Policy):
    """Scripted policy for testing the game loop."""

    def __init__(self, behavior: str = "honest"):
        super().__init__()
        assert behavior in ["honest", "silent", "liar"]
        self.behavior = behavior

    def select_action(self, observation):
        """Not used - we use plan_and_communicate() and act() instead."""
        raise NotImplementedError("Use plan_and_communicate() and act() instead")

    def plan_and_communicate(self, observation: str, received_messages: str, round_num: int) -> tuple[str, list, CommunicationChoice]:
        """Phase 1: Make a plan and send messages.

        Args:
            observation: Current observation string
            received_messages: Messages received this round
            round_num: Current round number

        Returns:
            tuple of (plan_text, messages_to_send, communication_choice)
        """
        messages = []

        if self.behavior == "honest":
            plan = f"Round {round_num}: Scout current region and report truthfully"

            # Get current region and discoveries
            tracker = self.entity.get_component(RegionTracker)
            discovery = self.entity.get_component(DiscoveryLog)

            latest = discovery.get_latest_about(tracker.current_region)
            if latest:
                # Report truthfully about what we see
                events = latest.get("events", [])
                resources = latest.get("resources", {})

                if events:
                    for event in events:
                        claim = event.description()
                        report = Report(
                            sender=self.entity.name,
                            region_claimed=tracker.current_region,
                            claim=claim,
                            is_public=True,
                            recipient=None,
                            round_sent=round_num,
                        )
                        messages.append(report)
                else:
                    # Report resources
                    resource_str = ", ".join(f"{v} {k}" for k, v in resources.items() if v > 0)
                    if resource_str:
                        claim = f"Resources available: {resource_str}"
                    else:
                        claim = "No significant resources"

                    report = Report(
                        sender=self.entity.name,
                        region_claimed=tracker.current_region,
                        claim=claim,
                        is_public=True,
                        recipient=None,
                        round_sent=round_num,
                    )
                    messages.append(report)

        elif self.behavior == "liar":
            plan = f"Round {round_num}: Fabricate report to mislead others"

            # Fabricate report about unvisited region
            tracker = self.entity.get_component(RegionTracker)
            discovery = self.entity.get_component(DiscoveryLog)

            # Find a region we haven't visited
            unvisited = [r for r in ADJACENCY.keys() if not discovery.has_visited_region(r)]
            if unvisited:
                fake_region = unvisited[0]
                fake_claim = "Abundant resources found! Gold and food plentiful."

                report = Report(
                    sender=self.entity.name,
                    region_claimed=fake_region,
                    claim=fake_claim,
                    is_public=True,
                    recipient=None,
                    round_sent=round_num,
                )
                messages.append(report)
            else:
                # All visited, fabricate about current region
                fake_claim = "Severe threat detected! Area extremely dangerous."
                report = Report(
                    sender=self.entity.name,
                    region_claimed=tracker.current_region,
                    claim=fake_claim,
                    is_public=True,
                    recipient=None,
                    round_sent=round_num,
                )
                messages.append(report)

        else:  # silent
            plan = f"Round {round_num}: Scout silently, no communication"
            # No messages

        has_report = any(isinstance(m, Report) for m in messages)
        has_promise = any(isinstance(m, Promise) for m in messages)

        if has_report:
            public_type = CommunicationType.REPORT
        elif has_promise:
            public_type = CommunicationType.PROMISE
        else:
            public_type = CommunicationType.NONE

        comm_choice = CommunicationChoice(
            agent_name=self.entity.name,
            round_num=round_num,
            public_type=public_type,
            private_type=CommunicationType.NONE,
            private_recipient=None,
        )

        return plan, messages, comm_choice

    def act(self, all_messages: str, observation: str, round_num: int, market_prices: str = "") -> ScoutAction:
        """Phase 2: Choose action based on observation and messages.

        Args:
            all_messages: All messages from this round
            observation: Current observation
            round_num: Current round number

        Returns:
            ScoutAction to execute
        """
        tracker = self.entity.get_component(RegionTracker)
        inventory = self.entity.get_component(ScoutInventory)

        if self.behavior == "liar":
            # Always try to gather gold or move toward Mines
            if tracker.current_region == "Mines":
                # Gather gold
                return ScoutAction(action_type="gather", details={"resource": "gold"})
            else:
                # Move toward Mines
                # Simple pathfinding: try adjacent regions
                adjacent = ADJACENCY.get(tracker.current_region, [])
                if "Mines" in adjacent:
                    return ScoutAction(action_type="move", details={"destination": "Mines"})
                elif adjacent:
                    # Move to first adjacent region
                    return ScoutAction(action_type="move", details={"destination": adjacent[0]})

        # Honest or silent behavior (same actions, different communication)
        # Strategy: deposit if have food and settlement likely needs it, else gather, else move

        # Check if we have food to deposit
        if inventory.resources.get("food", 0) > 0:
            # Deposit food
            amount = min(inventory.resources["food"], 2)
            return ScoutAction(action_type="deposit", details={"resource": "food", "amount": amount})

        if inventory.resources.get("water", 0) > 0:
            # Deposit water
            amount = min(inventory.resources["water"], 2)
            return ScoutAction(action_type="deposit", details={"resource": "water", "amount": amount})

        # Try to gather
        discovery = self.entity.get_component(DiscoveryLog)
        latest = discovery.get_latest_about(tracker.current_region)

        if latest:
            resources = latest.get("resources", {})
            # Gather food first, then water, then gold
            for resource in ["food", "water", "gold"]:
                if resources.get(resource, 0) > 0:
                    return ScoutAction(action_type="gather", details={"resource": resource})

        # Nothing to gather, try to move
        adjacent = ADJACENCY.get(tracker.current_region, [])
        if adjacent:
            # Move to first adjacent region
            return ScoutAction(action_type="move", details={"destination": adjacent[0]})

        # Stay if nothing else to do
        return ScoutAction(action_type="stay", details={})


if __name__ == "__main__":
    from info_marketplace.agent_components import create_scout_entity, PrivateGoal

    print("=== Testing ScriptedScoutPolicy ===")

    # Create test scouts with different behaviors
    behaviors = ["honest", "silent", "liar"]
    scouts = []

    for i, behavior in enumerate(behaviors):
        goal = PrivateGoal(
            description=f"Test goal for {behavior}",
            goal_tier="ALIGNED",
            short_label=f"{behavior}_test",
        )
        policy = ScriptedScoutPolicy(behavior=behavior)

        scout = create_scout_entity(
            name=f"Agent_{behavior}",
            starting_region=["Forest", "River", "Plains"][i],
            private_goal=goal,
            policy_component=policy,
        )
        scouts.append(scout)

    print(f"Created {len(scouts)} scouts with behaviors: {behaviors}")

    # Test plan_and_communicate
    print("\n=== Testing plan_and_communicate ===")
    for scout in scouts:
        policy = scout.get_component(ScriptedScoutPolicy)
        tracker = scout.get_component(RegionTracker)

        # Simulate observation
        from info_marketplace.world import Event
        discovery = scout.get_component(DiscoveryLog)
        test_event = Event(
            event_id="test_001",
            event_type="RESOURCE_FOUND",
            region=tracker.current_region,
            round_generated=1,
            details={"resource": "food", "amount": 3},
        )
        discovery.record(1, tracker.current_region, [test_event], {"food": 5, "water": 2})

        plan, messages, _ = policy.plan_and_communicate("test observation", "no messages", 1)
        print(f"\n{scout.name} ({policy.behavior}):")
        print(f"  Plan: {plan}")
        print(f"  Messages sent: {len(messages)}")
        for msg in messages:
            if hasattr(msg, 'claim'):
                print(f"    - Report: {msg.claim}")

    # Test act
    print("\n=== Testing act ===")
    for scout in scouts:
        policy = scout.get_component(ScriptedScoutPolicy)
        inventory = scout.get_component(ScoutInventory)

        # Add some food to inventory for testing
        inventory.add("food", 3)

        action = policy.act("test messages", "test observation", 1)
        print(f"\n{scout.name} ({policy.behavior}):")
        print(f"  Action: {action.describe()}")

    # Test with empty inventory
    print("\n=== Testing act with empty inventory ===")
    for scout in scouts:
        policy = scout.get_component(ScriptedScoutPolicy)
        inventory = scout.get_component(ScoutInventory)

        # Clear inventory
        inventory.resources = {"food": 0, "water": 0, "gold": 0}

        action = policy.act("test messages", "test observation", 2)
        print(f"\n{scout.name} ({policy.behavior}):")
        print(f"  Action: {action.describe()}")
