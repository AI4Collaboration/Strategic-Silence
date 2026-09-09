"""Settlement components for the Information Marketplace simulation."""

from __future__ import annotations

from word_play.core.components import Component
from word_play.core.entity import Entity
from word_play.presets.movement.single_point import Single_Point_Position


class MarketState(Component):
    """Tracks dynamic resource prices and trade activity at the settlement level.

    Prices respond to supply/demand: when the settlement is low on a resource,
    its price rises. Base prices are initialized from config constants.
    """

    BASE_PRICES = {"food": 5, "water": 3, "gold": 10}

    def __init__(self):
        super().__init__()
        self.prices: dict[str, float] = self.BASE_PRICES.copy()

    def update_prices(self, settlement_food: int, settlement_water: int):
        """Update prices based on current settlement supply.

        Lower supply increases price. Gold price is fixed (numeraire).
        """
        self.prices["food"] = round(self.BASE_PRICES["food"] * max(0.5, 10.0 / max(1, settlement_food + 5)), 1)
        self.prices["water"] = round(self.BASE_PRICES["water"] * max(0.5, 10.0 / max(1, settlement_water + 3)), 1)
        self.prices["gold"] = self.BASE_PRICES["gold"]

    def describe(self) -> str:
        """Single agent-facing rendering of current prices."""
        return (
            f"food: {self.prices['food']}g, "
            f"water: {self.prices['water']}g, "
            f"gold: {self.prices['gold']}g (numeraire)"
        )


class SettlementState(Component):
    """Word_Play Component tracking the shared settlement's resources."""

    def __init__(
        self,
        food: int = 10,
        water: int = 8,
        food_consumption: int = 1,
        water_consumption: int = 1,
    ):
        super().__init__()
        self.food = food
        self.water = water
        self.food_consumption = food_consumption
        self.water_consumption = water_consumption
        self.alive = True
        self.history: list[dict] = []
        self.deposits: list[dict] = []

    def consume(self, round_num: int):
        """Decrements food and water by consumption rates. Sets alive=False if either hits 0."""
        self.food -= self.food_consumption
        self.water -= self.water_consumption

        # Ensure resources don't go negative
        self.food = max(0, self.food)
        self.water = max(0, self.water)

        # Check if settlement is still alive
        if self.food == 0 or self.water == 0:
            self.alive = False

        # Log to history
        self.history.append(
            {
                "round": round_num,
                "action": "consume",
                "food": self.food,
                "water": self.water,
                "alive": self.alive,
            }
        )

    def deposit(self, resource: str, amount: int, agent_name: str):
        """Adds to food or water. Logs deposit."""
        if resource == "food":
            self.food += amount
        elif resource == "water":
            self.water += amount
        else:
            # For other resources like gold, we might want to track differently
            pass

        # Log deposit
        self.deposits.append(
            {
                "agent": agent_name,
                "resource": resource,
                "amount": amount,
                "food": self.food,
                "water": self.water,
            }
        )

    def get_status_string(self) -> str:
        """Returns status string like 'Settlement [ALIVE]: 6 food, 4 water.'"""
        status = "ALIVE" if self.alive else "DEAD"
        return f"Settlement [{status}]: {self.food} food, {self.water} water."


def create_settlement_entity(starting_food: int = 20, starting_water: int = 15) -> Entity:
    """Factory using Word_Play Entity.

    Updated defaults: 20 food / 15 water, consumption reduced to 1/1 per round (was 2/1).
    Tested: 20/15 with 2/1 consumption → 35% survival (agents don't deposit enough).
    New: 20/15 with 1/1 consumption → 20/15 rounds baseline (should hit 85%+ survival).
    Target: ~85% settlement survival to eliminate survivorship bias in temporal analysis.
    """
    return Entity(
        name="Settlement",
        position=Single_Point_Position(),
        components=[
            SettlementState(food=starting_food, water=starting_water),
            MarketState(),
        ],
        tags=["settlement"],
    )


if __name__ == "__main__":
    print("=== Testing Settlement Creation ===")
    settlement = create_settlement_entity(starting_food=10, starting_water=8)
    state = settlement.get_component(SettlementState)
    print(state.get_status_string())

    print("\n=== Testing Settlement Consumption (5 rounds) ===")
    for round_num in range(5):
        print(f"\nRound {round_num}:")
        print(f"  Before: {state.get_status_string()}")
        state.consume(round_num)
        print(f"  After:  {state.get_status_string()}")

    print("\n=== Testing Settlement Deposits ===")
    settlement2 = create_settlement_entity(starting_food=2, starting_water=2)
    state2 = settlement2.get_component(SettlementState)
    print(f"Initial: {state2.get_status_string()}")

    state2.deposit("food", 3, "Agent1")
    print(f"After Agent1 deposits 3 food: {state2.get_status_string()}")

    state2.deposit("water", 5, "Agent2")
    print(f"After Agent2 deposits 5 water: {state2.get_status_string()}")

    print(f"\nDeposit history: {state2.deposits}")

    print("\n=== Testing Settlement Death ===")
    settlement3 = create_settlement_entity(starting_food=3, starting_water=1)
    state3 = settlement3.get_component(SettlementState)
    print(f"Starting: {state3.get_status_string()}")

    for round_num in range(3):
        state3.consume(round_num)
        print(f"After round {round_num}: {state3.get_status_string()}")
        if not state3.alive:
            print("  ** Settlement has died! **")
            break

    print(f"\nConsumption history: {state3.history}")
