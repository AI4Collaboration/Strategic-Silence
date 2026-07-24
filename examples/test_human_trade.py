"""Test trading with Human_Trading_Policy via sim_simple_trade directly."""
from word_play.core import Entity
from word_play.presets.environments.simple_2d_grid_world import Simple_2D_Grid_World
from word_play.presets.movement.simple_2d_grid import Position_2D
from word_play.presets.systems.currency import Money
from word_play.presets.systems.inventory import Inventory, inventory_items
from word_play.presets.systems.communication.trade_communication import (
    sim_simple_trade,
    Trade_Offer,
    trade_offer_text,
)
from word_play.presets.systems.communication.trade_communication.presets.policies import Human_Trading_Policy
from word_play.presets.systems.do_nothing import Do_Nothing


alice = Entity(
    name="Alice",
    position=Position_2D(0, 0),
    actions=[],
    components=[
        Human_Trading_Policy(),
        Inventory(
            collectable_tags=["trade_good"],
            starting_inventory=[
                Entity(name="Apple", position=Position_2D(0, 0), tags=["trade_good"]),
                Entity(name="Bread", position=Position_2D(0, 0), tags=["trade_good"]),
            ],
        ),
        Money(amount=5),
    ],
)
bob = Entity(
    name="Bob",
    position=Position_2D(0, 0),
    actions=[],
    components=[
        Human_Trading_Policy(),
        Inventory(
            collectable_tags=["trade_good"],
            starting_inventory=[
                Entity(name="Berry", position=Position_2D(0, 0), tags=["trade_good"]),
                Entity(name="Cheese", position=Position_2D(0, 0), tags=["trade_good"]),
            ],
        ),
        Money(amount=3),
    ],
)

env = Simple_2D_Grid_World(
    description="Test human trading",
    entities=[alice, bob],
)

print("=== Starting human-trading test ===")
print(f"Alice before: {[e.name for e in inventory_items(alice)]}, money={alice.get_component(Money)}")
print(f"Bob before: {[e.name for e in inventory_items(bob)]}, money={bob.get_component(Money)}")

result = sim_simple_trade(
    participants=[alice, bob],
    env=env,
    initial_offers={
        "Alice": {"Bob": Trade_Offer(items=[inventory_items(alice)[0]], currency=1)},
        "Bob": {"Alice": Trade_Offer(items=[inventory_items(bob)[0]], currency=0)},
    },
    trade_duration=1,
)

print(f"\nTrade result: {result}")
print(f"Alice after: {[e.name for e in inventory_items(alice)]}, money={alice.get_component(Money)}")
print(f"Bob after: {[e.name for e in inventory_items(bob)]}, money={bob.get_component(Money)}")

transfers = result.get("transfers", [])
if transfers:
    print(f"\n=== TRADE SUCCESSFUL ===")
    for t in transfers:
        print(f"  {t['from']} -> {t['to']}: {t['items']}, {t['currency']} currency")
else:
    print(f"\n=== No transfers (expected with no input) ===")
