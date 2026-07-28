"""Minimal test that exercises the trading system infrastructure without an LLM."""
from word_play.core import Entity
from word_play.presets.environments.simple_2d_grid_world import Simple_2D_Grid_World
from word_play.presets.movement.simple_2d_grid import Position_2D
from word_play.presets.systems.currency import Money, money_amount
from word_play.presets.systems.inventory import Inventory, inventory_items
from word_play.presets.systems.communication.trade_communication import (
    Trade_Offer,
    in_trade,
    nearby_trade_partners,
    sim_simple_trade,
    trade_offer_text,
    Start_Private_Trade,
)
from word_play.presets.systems.communication.trade_communication.presets.policies import LLM_Trading_Policy
from word_play.presets.systems.do_nothing import Do_Nothing
from word_play.presets.models import LLM_MODEL_REGISTRY
from word_play.presets.models.human import Human_Model
from word_play.presets.entity_orderings import entity_definition_order


def test_trading_system():
    LLM_MODEL_REGISTRY.unload("test_trader")
    LLM_MODEL_REGISTRY.register("test_trader", Human_Model)

    env = Simple_2D_Grid_World(
        description="Test trading environment",
        entities=[
            Entity(
                name="Alice",
                position=Position_2D(0, 0),
                actions=[Start_Private_Trade(), Do_Nothing()],
                components=[
                    LLM_Trading_Policy(
                        model_key="test_trader",
                        system_prompt="You are Alice, a trader.",
                        use_chain_of_thought=False,
                    ),
                    Inventory(
                        collectable_tags=["trade_good"],
                        starting_inventory=[
                            Entity(name="Apple", position=Position_2D(0, 0), tags=["trade_good"]),
                            Entity(name="Bread", position=Position_2D(0, 0), tags=["trade_good"]),
                        ],
                    ),
                    Money(amount=5),
                ],
            ),
            Entity(
                name="Bob",
                position=Position_2D(0, 0),
                actions=[Start_Private_Trade(), Do_Nothing()],
                components=[
                    LLM_Trading_Policy(
                        model_key="test_trader",
                        system_prompt="You are Bob, a trader.",
                        use_chain_of_thought=False,
                    ),
                    Inventory(
                        collectable_tags=["trade_good"],
                        starting_inventory=[
                            Entity(name="Berry", position=Position_2D(0, 0), tags=["trade_good"]),
                            Entity(name="Cheese", position=Position_2D(0, 0), tags=["trade_good"]),
                        ],
                    ),
                    Money(amount=3),
                ],
            ),
        ],
    )

    alice = env.agents[0]
    bob = env.agents[1]

    print("=== Verifying trading infrastructure ===")
    print(f"Alice position: {alice.position}")
    print(f"Bob position: {bob.position}")

    print(f"Alice has Trading_Policy: {alice.has_component(LLM_Trading_Policy)}")
    print(f"Bob has Trading_Policy: {bob.has_component(LLM_Trading_Policy)}")
    print(f"Alice inventory: {[e.name for e in inventory_items(alice)]}")
    print(f"Bob inventory: {[e.name for e in inventory_items(bob)]}")
    print(f"Alice money: {money_amount(alice)}")
    print(f"Bob money: {money_amount(bob)}")

    partners_alice = nearby_trade_partners(alice, env)
    print(f"Nearby trade partners for Alice: {[e.name for e in partners_alice]}")

    partners_bob = nearby_trade_partners(bob, env)
    print(f"Nearby trade partners for Bob: {[e.name for e in partners_bob]}")

    print(f"Alice in_trade: {in_trade(alice)}")
    print(f"Bob in_trade: {in_trade(bob)}")

    offer = Trade_Offer(items=[inventory_items(alice)[0]], currency=1)
    print(f"Sample trade offer text: {trade_offer_text(offer)}")

    print("\n=== Checking positions are close ===")
    close = env.movement_system.positions_are_close(alice.position, bob.position)
    print(f"Alice and Bob positions close: {close}")

    assert len(partners_alice) == 1, f"Expected 1 trade partner for Alice, got {len(partners_alice)}"
    assert len(partners_bob) == 1, f"Expected 1 trade partner for Bob, got {len(partners_bob)}"
    assert not in_trade(alice), "Alice should not be in trade"
    assert not in_trade(bob), "Bob should not be in trade"
    assert close, "Alice and Bob should be at close positions"

    print("\n=== ALL TRADING INFRASTRUCTURE TESTS PASSED ===")


if __name__ == "__main__":
    test_trading_system()
