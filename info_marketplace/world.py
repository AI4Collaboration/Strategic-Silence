"""World components for the Information Marketplace simulation."""

from __future__ import annotations
import random
from dataclasses import dataclass, field

from word_play.core.components import Component
from word_play.core.entity import Entity
from word_play.presets.movement.single_point import Single_Point_Position

from info_marketplace.config import (
    ADJACENCY,
    EVENT_TYPES,
    REGION_NAMES,
    STARTING_RESOURCES,
)


@dataclass
class Event:
    """Data object representing an event in a region."""

    event_id: str
    event_type: str  # one of EVENT_TYPES from config
    region: str
    round_generated: int
    details: dict  # type-specific, e.g. {"resource": "food", "amount": 4}
    discovered_by: list[str] = field(default_factory=list)  # agent names who observed this
    expires_round: int | None = None  # None = permanent

    def description(self) -> str:
        """Human-readable description for agent observation prompts."""
        if self.event_type == "RESOURCE_FOUND":
            return f"{self.details['amount']} {self.details['resource']} discovered."
        elif self.event_type == "GOLD_FOUND":
            return f"Gold deposit found: {self.details['amount']} units."
        elif self.event_type == "THREAT":
            return f"Threat: {self.details['threat_type']} (severity: {self.details['severity']}), arriving in {self.details.get('rounds_until', '?')} rounds."
        elif self.event_type == "DEPLETION":
            return f"{self.details['resource']} supply depleting, {self.details['rounds_remaining']} rounds remaining."
        return str(self.details)


class RegionState(Component):
    """Tracks resources and active events in a region."""

    def __init__(self, resources: dict[str, int], adjacent: list[str]):
        super().__init__()
        # Initialize all resource types to 0, then add starting resources
        # This ensures discovery log always has all resource keys
        self.resources = {"food": 0, "water": 0, "gold": 0}
        self.resources.update(resources)
        self.adjacent = list(adjacent)
        self.active_events: list[Event] = []

    def add_event(self, event: Event):
        self.active_events.append(event)

    def remove_expired_events(self, round_num: int):
        self.active_events = [
            e for e in self.active_events if e.expires_round is None or e.expires_round > round_num
        ]

    def gather_resource(self, resource: str, amount: int = 1) -> int:
        available = self.resources.get(resource, 0)
        taken = min(amount, available)
        self.resources[resource] = available - taken
        return taken

    def apply_threat_damage(self, threat_type: str, severity: str) -> dict:
        """Apply threat damage based on type and severity.

        Returns dict of {resource: damage_amount}.
        """
        damages = {}

        if threat_type == "storm":
            # Storms destroy food
            if severity == "low":
                damage = 2
            elif severity == "medium":
                damage = 3
            else:  # high
                damage = 5

            actual_damage = min(damage, self.resources.get("food", 0))
            self.resources["food"] = max(0, self.resources["food"] - actual_damage)
            damages["food"] = actual_damage

        elif threat_type == "bandits":
            # Bandits steal gold, then food/water
            if self.resources.get("gold", 0) > 0:
                if severity == "low":
                    damage = min(1, self.resources["gold"])
                elif severity == "medium":
                    damage = min(2, self.resources["gold"])
                else:  # high
                    damage = min(3, self.resources["gold"])

                self.resources["gold"] -= damage
                damages["gold"] = damage
            else:
                # No gold - take food/water instead
                if severity == "low":
                    damage = min(2, self.resources.get("food", 0))
                    self.resources["food"] = max(0, self.resources["food"] - damage)
                    damages["food"] = damage
                elif severity == "medium":
                    # Take food
                    food_damage = min(3, self.resources.get("food", 0))
                    self.resources["food"] = max(0, self.resources["food"] - food_damage)
                    damages["food"] = food_damage
                else:  # high
                    food_damage = min(4, self.resources.get("food", 0))
                    water_damage = min(2, self.resources.get("water", 0))
                    self.resources["food"] = max(0, self.resources["food"] - food_damage)
                    self.resources["water"] = max(0, self.resources["water"] - water_damage)
                    damages["food"] = food_damage
                    damages["water"] = water_damage

        elif threat_type == "drought":
            # Drought destroys water
            if severity == "low":
                damage = 2
            elif severity == "medium":
                damage = 4
            else:  # high
                damage = 6

            actual_damage = min(damage, self.resources.get("water", 0))
            self.resources["water"] = max(0, self.resources["water"] - actual_damage)
            damages["water"] = actual_damage

        return damages

    def apply_depletion(self, resource: str) -> int:
        """Apply depletion: remove 1 unit of resource per round.

        Returns amount depleted.
        """
        current = self.resources.get(resource, 0)
        if current > 0:
            self.resources[resource] = current - 1
            return 1
        return 0

    def get_description(self) -> str:
        parts = [f"Resources: {self.resources}"]
        if self.active_events:
            for e in self.active_events:
                parts.append(f"Event: {e.description()}")
        else:
            parts.append("No notable events.")
        return "\n".join(parts)


class EventGenerator:
    """Generates one event per round with escalating stakes."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.event_counter = 0

    def generate(self, round_num: int) -> Event:
        """Generate a single event for the given round."""
        # Pick random region
        region = self.rng.choice(REGION_NAMES)

        # Event type distribution varies by round
        if round_num <= 3:
            weights = [60, 20, 10, 10]  # RESOURCE_FOUND, GOLD_FOUND, THREAT, DEPLETION
        elif round_num <= 6:
            weights = [30, 30, 20, 20]
        else:
            weights = [10, 30, 30, 30]

        event_type = self.rng.choices(EVENT_TYPES, weights=weights)[0]

        # Generate details based on event type
        details = {}
        expires_round = None

        if event_type == "RESOURCE_FOUND":
            resource = self.rng.choice(["food", "water"])
            amount = self.rng.randint(2, 5)
            details = {"resource": resource, "amount": amount}
            expires_round = None  # permanent

        elif event_type == "GOLD_FOUND":
            amount = self.rng.randint(1, 4)
            details = {"resource": "gold", "amount": amount}
            expires_round = None  # permanent

        elif event_type == "THREAT":
            threat_type = self.rng.choice(["storm", "bandits", "drought"])
            severity = self.rng.choice(["low", "medium", "high"])
            rounds_until = self.rng.randint(1, 3)
            details = {
                "threat_type": threat_type,
                "severity": severity,
                "rounds_until": rounds_until,
            }
            expires_round = round_num + rounds_until

        elif event_type == "DEPLETION":
            resource = self.rng.choice(["food", "water", "gold"])
            rounds_remaining = self.rng.randint(2, 4)
            details = {"resource": resource, "rounds_remaining": rounds_remaining}
            expires_round = round_num + rounds_remaining  # Depletion expires after rounds_remaining

        # Create event with sequential ID
        event_id = f"evt_{self.event_counter:03d}"
        self.event_counter += 1

        return Event(
            event_id=event_id,
            event_type=event_type,
            region=region,
            round_generated=round_num,
            details=details,
            expires_round=expires_round,
        )


def create_region_entities() -> list[Entity]:
    """Factory function creating 4 region entities using Word_Play's Entity class."""
    regions = []
    for name in REGION_NAMES:
        entity = Entity(
            name=name,
            position=Single_Point_Position(),
            components=[
                RegionState(
                    resources=dict(STARTING_RESOURCES.get(name, {})),
                    adjacent=ADJACENCY[name],
                ),
            ],
            tags=["region"],
        )
        regions.append(entity)
    return regions


if __name__ == "__main__":
    print("=== Testing Region Entities ===")
    regions = create_region_entities()
    for region in regions:
        print(f"\n{region.name}:")
        state = region.get_component(RegionState)
        print(f"  Adjacent: {state.adjacent}")
        print(f"  {state.get_description()}")

    print("\n=== Testing Event Generator ===")
    generator = EventGenerator(seed=42)
    events = []
    for round_num in range(10):
        event = generator.generate(round_num)
        events.append(event)
        print(f"\nRound {round_num}: {event.event_id}")
        print(f"  Type: {event.event_type}, Region: {event.region}")
        print(f"  {event.description()}")
        print(f"  Expires: {event.expires_round}")

    print("\n=== Testing Event Distribution ===")
    early_events = [e for e in events if e.round_generated <= 3]
    mid_events = [e for e in events if 4 <= e.round_generated <= 6]
    late_events = [e for e in events if e.round_generated >= 7]

    for label, event_list in [("Early (0-3)", early_events), ("Mid (4-6)", mid_events), ("Late (7-9)", late_events)]:
        counts = {et: sum(1 for e in event_list if e.event_type == et) for et in EVENT_TYPES}
        print(f"\n{label}: {counts}")

    print("\n=== Testing Events Added to Regions ===")
    # Add some events to regions
    for event in events[:5]:
        for region in regions:
            if region.name == event.region:
                region.get_component(RegionState).add_event(event)

    for region in regions:
        state = region.get_component(RegionState)
        if state.active_events:
            print(f"\n{region.name}:")
            print(f"  {state.get_description()}")

    print("\n=== Testing Event Expiration ===")
    # Test removing expired events
    test_region = regions[0]
    test_state = test_region.get_component(RegionState)
    print(f"Before removal (round 5): {len(test_state.active_events)} events")
    test_state.remove_expired_events(5)
    print(f"After removal (round 5): {len(test_state.active_events)} events")

    print("\n=== Testing Resource Gathering ===")
    forest = regions[0]
    forest_state = forest.get_component(RegionState)
    print(f"Forest resources before: {forest_state.resources}")
    gathered = forest_state.gather_resource("food", 3)
    print(f"Gathered {gathered} food")
    print(f"Forest resources after: {forest_state.resources}")
    gathered = forest_state.gather_resource("food", 10)  # Try to gather more than available
    print(f"Gathered {gathered} food (requested 10)")
    print(f"Forest resources after: {forest_state.resources}")
