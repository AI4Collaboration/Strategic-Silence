"""Main game environment for the Information Marketplace simulation."""

import json
from dataclasses import dataclass, field
from typing import Optional
from word_play.core.entity import Entity
from word_play.core.components import Agent_Policy

from info_marketplace.config import REGION_NAMES
from info_marketplace.world import EventGenerator, RegionState, Event
from info_marketplace.settlement import MarketState, SettlementState
from info_marketplace.agent_components import (
    DiscoveryLog,
    RegionTracker,
    ScoutInventory,
    PlanLog,
    ActionLog,
    MemorySummary,
)
from info_marketplace.messages import CommunicationChoice, MessageLog, Report, Promise
from info_marketplace.marketplace_actions import ScoutAction


@dataclass
class GameConfig:
    """Configuration for a game instance."""

    num_rounds: int = 10
    num_agents: int = 4
    random_seed: int = 42
    condition_name: str = "default"
    starting_regions: list[str] = field(default_factory=lambda: ["Forest", "River", "Plains", "Mines"])
    settlement_starting_food: int = 10
    settlement_starting_water: int = 8


class MarketplaceEnv:
    """Custom game controller using Word_Play entities but managing its own loop."""

    def __init__(
        self,
        config: GameConfig,
        agents: list[Entity],
        region_entities: list[Entity],
        settlement_entity: Entity,
    ):
        self.config = config
        self.agents = agents
        self.settlement = settlement_entity
        self.settlement_state = settlement_entity.get_component(SettlementState)
        self.market_state = settlement_entity.get_component(MarketState)

        # Build regions dict
        self.regions: dict[str, Entity] = {r.name: r for r in region_entities}

        # Create message log and event generator
        self.message_log = MessageLog()
        self.event_generator = EventGenerator(seed=config.random_seed)

        # Ground truth log (stub for now)
        self.ground_truth_log: list[dict] = []

        # Full game log
        self.game_log: dict = {
            "config": {
                "num_rounds": config.num_rounds,
                "num_agents": config.num_agents,
                "random_seed": config.random_seed,
                "condition_name": config.condition_name,
            },
            "rounds": [],
            "final_state": {},
        }

    def run(self) -> dict:
        """Main game loop. Returns full game log."""
        for round_num in range(self.config.num_rounds):
            if not self.settlement_state.alive:
                print(f"\n!!! Settlement died in round {round_num}. Game over. !!!")
                break

            round_log = self.run_round(round_num)
            self.game_log["rounds"].append(round_log)

        self.game_log["final_state"] = self._get_final_state()
        return self.game_log

    def run_round(self, round_num: int) -> dict:
        """Execute one round of the game.

        Steps:
        1. Generate event and add to region
        2. Apply event effects
        3. Observe: agents see their region
        4. Phase 1: plan_and_communicate
        5. Phase 2: act
        6. Resolve actions
        7. Settlement consumption
        8. Cleanup
        9. Update memory summaries
        10. Record ground truth

        Returns:
            Round log dict
        """
        round_log = {
            "round": round_num,
            "event": None,
            "observations": {},
            "plans": {},
            "messages": [],
            "communication_choices": [],
            "actions": {},
            "action_results": {},
            "settlement_status": {},
        }

        # 1. Generate event
        event = self.event_generator.generate(round_num)
        region_entity = self.regions[event.region]
        region_state = region_entity.get_component(RegionState)
        region_state.add_event(event)

        round_log["event"] = {
            "event_id": event.event_id,
            "type": event.event_type,
            "region": event.region,
            "description": event.description(),
        }

        # 2. Apply immediate event effects (RESOURCE_FOUND, GOLD_FOUND)
        self._apply_event_effects(event, region_state)

        # 2.5. Apply ongoing event effects (THREAT expiration, DEPLETION drain)
        self._apply_ongoing_event_effects(round_num)

        # 2.6. Remove expired events
        for region_entity in self.regions.values():
            region_entity.get_component(RegionState).remove_expired_events(round_num)

        # 2.7. Update market prices from current settlement supply, so every
        # price shown to agents this round (observation and Phase 2) agrees
        self.market_state.update_prices(self.settlement_state.food, self.settlement_state.water)
        round_log["market_prices"] = self.market_state.prices.copy()

        # 3. Observe: agents see their current region
        for agent in self.agents:
            tracker = agent.get_component(RegionTracker)
            discovery = agent.get_component(DiscoveryLog)
            current_region_name = tracker.current_region

            region_entity = self.regions[current_region_name]
            region_state = region_entity.get_component(RegionState)

            # Record observation
            discovery.record(
                round_num,
                current_region_name,
                region_state.active_events.copy(),
                region_state.resources.copy(),
            )

            # Mark agent in event's discovered_by
            for evt in region_state.active_events:
                if agent.name not in evt.discovered_by:
                    evt.discovered_by.append(agent.name)

        # 4. Build observations for each agent
        observations = {}
        for agent in self.agents:
            obs = self._build_observation(agent, round_num)
            observations[agent.name] = obs
            round_log["observations"][agent.name] = obs

        # 5. Phase 1: plan_and_communicate
        plans = {}
        for agent in self.agents:
            policy = agent.get_component(Agent_Policy)
            received_messages = self.message_log.format_for_agent(agent.name, round_num)

            plan, messages, comm_choice = policy.plan_and_communicate(observations[agent.name], received_messages, round_num)

            # Store plan
            plan_log = agent.get_component(PlanLog)
            plan_log.record(round_num, plan)
            plans[agent.name] = plan
            round_log["plans"][agent.name] = plan

            # Store communication choice (including silence)
            round_log["communication_choices"].append(comm_choice.to_dict())

            # Add messages to log
            for msg in messages:
                self.message_log.add(msg)
                msg_dict = {
                    "message_id": msg.message_id,
                    "sender": msg.sender,
                    "is_public": msg.is_public,
                }
                if isinstance(msg, Report):
                    msg_dict["type"] = "report"
                    msg_dict["region_claimed"] = msg.region_claimed
                    msg_dict["claim"] = msg.claim
                    msg_dict["recipient"] = msg.recipient
                elif isinstance(msg, Promise):
                    msg_dict["type"] = "promise"
                    msg_dict["target"] = msg.target
                    msg_dict["commitment"] = msg.commitment
                    msg_dict["by_round"] = msg.by_round

                round_log["messages"].append(msg_dict)

        # 6. Phase 2: act
        market_prices_str = f"  {self.market_state.describe()}"
        actions = {}
        for agent in self.agents:
            policy = agent.get_component(Agent_Policy)
            all_messages = self.message_log.format_for_agent(agent.name, round_num)

            action = policy.act(all_messages, observations[agent.name], round_num, market_prices_str)
            actions[agent.name] = action
            round_log["actions"][agent.name] = {
                "type": action.action_type,
                "details": action.details,
                "description": action.describe(),
            }

        # 7. Resolve actions
        for agent in self.agents:
            action = actions[agent.name]
            success = self._resolve_action(agent, action, round_num)
            round_log["action_results"][agent.name] = {
                "action": action.describe(),
                "success": success,
            }

            # Log action
            action_log = agent.get_component(ActionLog)
            action_log.record(round_num, action.action_type, action.details)

        # 8. Settlement consumption
        self.settlement_state.consume(round_num)
        round_log["settlement_status"] = {
            "alive": self.settlement_state.alive,
            "food": self.settlement_state.food,
            "water": self.settlement_state.water,
        }

        # 9. Cleanup expired events
        for region_entity in self.regions.values():
            region_state = region_entity.get_component(RegionState)
            region_state.remove_expired_events(round_num)

        # 10. Update memory summaries
        for agent in self.agents:
            tracker = agent.get_component(RegionTracker)
            discovery = agent.get_component(DiscoveryLog)
            memory = agent.get_component(MemorySummary)

            latest = discovery.get_latest_about(tracker.current_region)
            events_seen = latest.get("events", []) if latest else []
            messages_sent = len([m for m in round_log["messages"] if m["sender"] == agent.name])
            action_desc = actions[agent.name].describe()
            settlement_status = f"{self.settlement_state.food}f, {self.settlement_state.water}w"

            memory.update(round_num, tracker.current_region, events_seen, messages_sent, action_desc, settlement_status)

        # 11. Record ground truth snapshot
        snapshot = {
            "round": round_num,
            "regions": {name: region.get_component(RegionState).resources.copy() for name, region in self.regions.items()},
            "agent_positions": {agent.name: agent.get_component(RegionTracker).current_region for agent in self.agents},
            "agent_inventories": {agent.name: agent.get_component(ScoutInventory).resources.copy() for agent in self.agents},
            "market_prices": self.market_state.prices.copy(),
            "settlement": {
                "food": self.settlement_state.food,
                "water": self.settlement_state.water,
                "alive": self.settlement_state.alive,
            },
        }
        self.ground_truth_log.append(snapshot)

        return round_log

    def _apply_event_effects(self, event: Event, region_state: RegionState):
        """Apply immediate effects of events (RESOURCE_FOUND, GOLD_FOUND)."""
        if event.event_type == "RESOURCE_FOUND":
            # Add resources to region
            resource = event.details["resource"]
            amount = event.details["amount"]
            region_state.resources[resource] += amount

        elif event.event_type == "GOLD_FOUND":
            # Add gold to region
            amount = event.details["amount"]
            region_state.resources["gold"] += amount

        # THREAT and DEPLETION have delayed/ongoing effects, handled in _apply_ongoing_event_effects

    def _apply_ongoing_event_effects(self, round_num: int):
        """Apply ongoing effects from active events (threat expiration, depletion drain).

        Called each round to:
        - Apply threat damage when threats expire (arrive)
        - Apply depletion drain each round until expiration
        """
        for region_name, region_entity in self.regions.items():
            region_state = region_entity.get_component(RegionState)

            for event in region_state.active_events[:]:  # Copy list for safe iteration
                # Handle THREAT expiration (when threat "arrives")
                if event.event_type == "THREAT":
                    if event.expires_round is not None and round_num == event.expires_round:
                        # Threat has arrived - apply damage
                        threat_type = event.details["threat_type"]
                        severity = event.details["severity"]
                        damages = region_state.apply_threat_damage(threat_type, severity)
                        event.details["damage_dealt"] = damages
                        # Event will be removed by remove_expired_events later

                # Handle ongoing DEPLETION (every round)
                elif event.event_type == "DEPLETION":
                    created_round = event.round_generated
                    rounds_elapsed = round_num - created_round
                    rounds_remaining = event.details["rounds_remaining"]

                    # Apply depletion each round until it expires
                    if 0 <= rounds_elapsed < rounds_remaining:
                        resource = event.details["resource"]
                        depleted = region_state.apply_depletion(resource)
                        event.details.setdefault("total_depleted", 0)
                        event.details["total_depleted"] += depleted

    def _build_observation(self, agent: Entity, round_num: int) -> str:
        """Build observation string for an agent (<150 tokens)."""
        tracker = agent.get_component(RegionTracker)
        inventory = agent.get_component(ScoutInventory)
        current_region = tracker.current_region

        region_entity = self.regions[current_region]
        region_state = region_entity.get_component(RegionState)

        # Format resources
        resource_parts = []
        for resource, amount in region_state.resources.items():
            if amount > 0:
                resource_parts.append(f"{amount} {resource}")
        resources_str = ", ".join(resource_parts) if resource_parts else "No resources"

        # Format events
        events_str = "\n".join([f"  - {evt.description()}" for evt in region_state.active_events])
        if not events_str:
            events_str = "  No notable events."

        # Get agents in this region
        agents_here = self._get_agents_in_region(current_region)
        agents_str = ", ".join(agents_here)

        # Build observation
        market_info = f"Market rates: {self.market_state.describe()}\n"
        obs = f"""Round {round_num} | You are in: {current_region} | Agents here: {agents_str}
Resources here: {resources_str}
{market_info}Events here:
{events_str}
Your inventory: {inventory.resources['food']} food, {inventory.resources['water']} water, {inventory.resources['gold']} gold
Settlement: {self.settlement_state.food} food, {self.settlement_state.water} water remaining."""

        return obs

    def _resolve_action(self, agent: Entity, action: ScoutAction, round_num: int) -> bool:
        """Validate and execute one action. Returns True if successful."""
        tracker = agent.get_component(RegionTracker)
        inventory = agent.get_component(ScoutInventory)

        if action.action_type == "move":
            destination = action.details.get("destination")
            if destination:
                success = tracker.move_to(destination, round_num)
                return success
            return False

        elif action.action_type == "gather":
            resource = action.details.get("resource")
            if resource:
                current_region = tracker.current_region
                region_entity = self.regions[current_region]
                region_state = region_entity.get_component(RegionState)

                gathered = region_state.gather_resource(resource, 1)
                if gathered > 0:
                    inventory.add(resource, gathered)
                    return True
            return False

        elif action.action_type == "deposit":
            resource = action.details.get("resource")
            amount = action.details.get("amount", 1)
            if resource:
                taken = inventory.remove(resource, amount)
                if taken > 0:
                    self.settlement_state.deposit(resource, taken, agent.name)
                    return True
            return False

        elif action.action_type == "trade":
            give_resource = action.details.get("give_resource")
            give_amount = action.details.get("give_amount", 0)
            recv_resource = action.details.get("receive_resource")
            recv_amount = action.details.get("receive_amount", 0)
            partner_name = action.details.get("partner")
            if not (give_resource and recv_resource and partner_name):
                return False

            # Both sides must exchange something real, and not with yourself —
            # otherwise "TRADE food 0 FOR gold 5" drains the partner for free
            if give_amount <= 0 or recv_amount <= 0:
                return False
            if partner_name == agent.name:
                return False

            partner = self._find_agent(partner_name)
            if not partner:
                return False

            partner_inv = partner.get_component(ScoutInventory)
            partner_tracker = partner.get_component(RegionTracker)

            if partner_tracker.current_region != tracker.current_region:
                return False

            if inventory.resources.get(give_resource, 0) < give_amount:
                return False
            if partner_inv.resources.get(recv_resource, 0) < recv_amount:
                return False

            inventory.remove(give_resource, give_amount)
            partner_inv.remove(recv_resource, recv_amount)
            inventory.add(recv_resource, recv_amount)
            partner_inv.add(give_resource, give_amount)

            return True

        elif action.action_type == "stay":
            tracker.record_stay(round_num)
            return True

        return False

    def _find_agent(self, name: str) -> Optional[Entity]:
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None

    def _get_agents_in_region(self, region_name: str) -> list[str]:
        """Returns list of agent names in the specified region."""
        agents_here = []
        for agent in self.agents:
            tracker = agent.get_component(RegionTracker)
            if tracker.current_region == region_name:
                agents_here.append(agent.name)
        return agents_here

    def _get_final_state(self) -> dict:
        """Returns final game state summary."""
        return {
            "settlement": {
                "alive": self.settlement_state.alive,
                "food": self.settlement_state.food,
                "water": self.settlement_state.water,
            },
            "agents": {
                agent.name: {
                    "region": agent.get_component(RegionTracker).current_region,
                    "inventory": agent.get_component(ScoutInventory).resources.copy(),
                }
                for agent in self.agents
            },
            "regions": {name: region.get_component(RegionState).resources.copy() for name, region in self.regions.items()},
        }


if __name__ == "__main__":
    from info_marketplace.world import create_region_entities
    from info_marketplace.settlement import create_settlement_entity
    from info_marketplace.agent_components import create_scout_entity, PrivateGoal
    from info_marketplace.scripted_agent import ScriptedScoutPolicy

    print("=== Testing MarketplaceEnv ===")

    # Create config
    config = GameConfig(
        num_rounds=10,
        num_agents=4,
        random_seed=42,
        condition_name="test_game",
    )

    # Create regions and settlement
    regions = create_region_entities()
    settlement = create_settlement_entity(
        starting_food=config.settlement_starting_food,
        starting_water=config.settlement_starting_water,
    )

    # Create 4 scouts: 2 honest, 1 silent, 1 liar
    agents = []
    behaviors = ["honest", "honest", "silent", "liar"]
    starting_regions = config.starting_regions

    for i, (behavior, region) in enumerate(zip(behaviors, starting_regions)):
        goal = PrivateGoal(
            description=f"Test goal for Agent_{i}",
            goal_tier=["ALIGNED", "ALIGNED", "ORTHOGONAL", "COMPETITIVE"][i],
            short_label=f"goal_{i}",
        )
        policy = ScriptedScoutPolicy(behavior=behavior)

        agent = create_scout_entity(
            name=f"Agent_{i}",
            starting_region=region,
            private_goal=goal,
            policy_component=policy,
        )
        agents.append(agent)

    print(f"Created {len(agents)} agents with behaviors: {behaviors}")
    print(f"Starting regions: {starting_regions}")

    # Create environment
    env = MarketplaceEnv(config, agents, regions, settlement)

    print("\n=== Running 10-round game ===\n")

    # Run game
    game_log = env.run()

    # Print summary of each round
    for round_log in game_log["rounds"]:
        print(f"\n--- Round {round_log['round']} ---")
        print(f"Event: {round_log['event']['description']} in {round_log['event']['region']}")
        print(f"Messages sent: {len(round_log['messages'])}")
        for msg in round_log['messages']:
            if msg['type'] == 'report':
                print(f"  - {msg['sender']}: {msg['claim']} (about {msg['region_claimed']})")
        print(f"Actions:")
        for agent_name, action_info in round_log['actions'].items():
            result = round_log['action_results'][agent_name]
            print(f"  - {agent_name}: {action_info['description']} ({'success' if result['success'] else 'failed'})")
        print(f"Settlement: {round_log['settlement_status']['food']}f, {round_log['settlement_status']['water']}w ({'alive' if round_log['settlement_status']['alive'] else 'DEAD'})")

    # Print final state
    print("\n=== Final State ===")
    final = game_log["final_state"]
    print(f"Settlement: {final['settlement']['food']}f, {final['settlement']['water']}w ({'ALIVE' if final['settlement']['alive'] else 'DEAD'})")
    print("\nAgent final positions and inventories:")
    for agent_name, agent_info in final['agents'].items():
        print(f"  {agent_name}: {agent_info['region']}, inventory: {agent_info['inventory']}")

    # Save to JSON
    output_file = "test_game_log.json"
    with open(output_file, 'w') as f:
        json.dump(game_log, f, indent=2)
    print(f"\nGame log saved to {output_file}")

    # Verification tests
    print("\n=== Verification Tests ===")

    # Check that honest agents reported truthfully
    print("\n1. Honest agent truth-telling:")
    for agent in agents[:2]:  # First two are honest
        discoveries = agent.get_component(DiscoveryLog).entries
        if discoveries:
            print(f"  {agent.name} visited {len(discoveries)} regions")

    # Check that liar fabricated
    print("\n2. Liar behavior:")
    liar = agents[3]
    liar_messages = env.message_log.get_sent_by(liar.name)
    print(f"  {liar.name} sent {len(liar_messages)} messages")
    for msg in liar_messages[:3]:  # Show first 3
        if hasattr(msg, 'claim'):
            print(f"    - Claimed: {msg.claim}")

    # Check settlement decremented correctly
    print("\n3. Settlement resource tracking:")
    print(f"  Started with: {config.settlement_starting_food}f, {config.settlement_starting_water}w")
    print(f"  Ended with: {final['settlement']['food']}f, {final['settlement']['water']}w")
    print(f"  Consumption rate: {settlement.get_component(SettlementState).food_consumption}f, {settlement.get_component(SettlementState).water_consumption}w per round")

    # Check adjacency was enforced
    print("\n4. Movement validation:")
    movement_failures = 0
    for round_log in game_log["rounds"]:
        for agent_name, result in round_log['action_results'].items():
            if "Move" in result['action'] and not result['success']:
                movement_failures += 1
    print(f"  Movement failures (invalid adjacency): {movement_failures}")

    print("\n=== Tests Complete ===")
