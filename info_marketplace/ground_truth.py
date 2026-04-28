"""Ground truth logging for deception detection."""

from __future__ import annotations
from typing import Dict, Any, List


class GroundTruthLog:
    """Records true world state each round for deception analysis.

    This is the authoritative source of what actually happened in the game,
    used to verify agent claims and detect fabrications.
    """

    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []

    def record(self, round_num: int, regions_dict: Dict[str, Dict], agent_positions: Dict[str, str]):
        """Record ground truth state for a round.

        Args:
            round_num: Current round number
            regions_dict: {region_name: {"resources": {...}, "events": [...]}}
            agent_positions: {agent_name: region_name}
        """
        snapshot = {
            "round": round_num,
            "regions": {name: dict(data) for name, data in regions_dict.items()},
            "agent_positions": dict(agent_positions),
        }
        self.snapshots.append(snapshot)

    def get_truth(self, region: str, round_num: int) -> Dict | None:
        """Get ground truth about a region at a specific round.

        Args:
            region: Region name
            round_num: Round number

        Returns:
            {"resources": {...}, "events": [...]} or None if not found
        """
        for snapshot in self.snapshots:
            if snapshot["round"] == round_num:
                return snapshot["regions"].get(region)
        return None

    def was_agent_in_region(self, agent_name: str, region: str, up_to_round: int) -> bool:
        """Check if agent was ever in a region up to a given round.

        Args:
            agent_name: Agent name
            region: Region name
            up_to_round: Check rounds 0 to up_to_round (inclusive)

        Returns:
            True if agent was in region at any point, False otherwise
        """
        for snapshot in self.snapshots:
            if snapshot["round"] <= up_to_round:
                if snapshot["agent_positions"].get(agent_name) == region:
                    return True
        return False

    def get_agent_position(self, agent_name: str, round_num: int) -> str | None:
        """Get agent's position at a specific round.

        Args:
            agent_name: Agent name
            round_num: Round number

        Returns:
            Region name or None if not found
        """
        for snapshot in self.snapshots:
            if snapshot["round"] == round_num:
                return snapshot["agent_positions"].get(agent_name)
        return None

    def get_all_rounds(self) -> List[int]:
        """Get list of all recorded round numbers."""
        return [s["round"] for s in self.snapshots]

    def get_snapshot(self, round_num: int) -> Dict | None:
        """Get full snapshot for a round."""
        for snapshot in self.snapshots:
            if snapshot["round"] == round_num:
                return snapshot
        return None


if __name__ == "__main__":
    print("=== Testing GroundTruthLog ===\n")

    log = GroundTruthLog()

    # Record round 0
    log.record(
        round_num=0,
        regions_dict={
            "Forest": {"resources": {"food": 5}, "events": []},
            "River": {"resources": {"water": 3}, "events": []},
        },
        agent_positions={"Agent_0": "Forest", "Agent_1": "River"}
    )

    # Record round 1
    from info_marketplace.world import Event
    event1 = Event(
        event_id="evt_001",
        event_type="RESOURCE_FOUND",
        region="Forest",
        round_generated=1,
        details={"resource": "food", "amount": 3}
    )

    log.record(
        round_num=1,
        regions_dict={
            "Forest": {"resources": {"food": 8}, "events": [event1]},
            "River": {"resources": {"water": 3}, "events": []},
        },
        agent_positions={"Agent_0": "Forest", "Agent_1": "River"}
    )

    # Test get_truth
    print("Test 1: get_truth(Forest, round 1)")
    truth = log.get_truth("Forest", 1)
    print(f"  Resources: {truth['resources']}")
    print(f"  Events: {len(truth['events'])} event(s)")

    # Test was_agent_in_region
    print("\nTest 2: was_agent_in_region")
    print(f"  Agent_0 in Forest up to round 1: {log.was_agent_in_region('Agent_0', 'Forest', 1)}")
    print(f"  Agent_0 in River up to round 1: {log.was_agent_in_region('Agent_0', 'River', 1)}")
    print(f"  Agent_1 in River up to round 1: {log.was_agent_in_region('Agent_1', 'River', 1)}")

    # Test get_agent_position
    print("\nTest 3: get_agent_position")
    print(f"  Agent_0 at round 0: {log.get_agent_position('Agent_0', 0)}")
    print(f"  Agent_1 at round 1: {log.get_agent_position('Agent_1', 1)}")

    # Test get_all_rounds
    print("\nTest 4: get_all_rounds")
    print(f"  Recorded rounds: {log.get_all_rounds()}")

    print("\n=== Tests Complete ===")
