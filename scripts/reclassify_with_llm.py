#!/usr/bin/env python3
"""Reclassify all existing trials using LLM-based message classifier.

This script:
1. Finds all trial JSONs in results/ directories
2. Re-runs classification with USE_LLM_MESSAGE_CLASSIFICATION=true
3. Saves updated JSONs with new classifications
4. Uses 50 parallel workers for speed
"""

import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
import traceback
from tqdm import tqdm

# Load .env file if it exists (manual parsing, no dependencies)
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Set environment variables BEFORE importing classifier
os.environ['USE_LLM_MESSAGE_CLASSIFICATION'] = 'true'
os.environ['USE_LLM_PREMEDITATION'] = 'true'

# Verify API key is set
if not os.environ.get('OPENAI_API_KEY'):
    print("ERROR: OPENAI_API_KEY not found in environment or .env file")
    print("Please create a .env file with:")
    print("  OPENAI_API_KEY=your_key_here")
    print()
    print("Or export it:")
    print("  export OPENAI_API_KEY=your_key_here")
    sys.exit(1)

from info_marketplace.classifier import classify_all, DeceptionLabel
from info_marketplace.messages import Report, Promise
from info_marketplace.agent_components import DiscoveryLog, ActionLog, RegionTracker, PrivateGoal, ScoutInventory, MemorySummary, PlanLog
from info_marketplace.ground_truth import GroundTruthLog
from word_play.core.entity import Entity
from word_play.presets.movement.single_point import Single_Point_Position


def reconstruct_agent_from_trial(trial_data: Dict, agent_name: str) -> Entity:
    """Reconstruct an agent Entity from trial JSON data."""
    # Find agent's goal
    agent_goal = None
    for goal_data in trial_data['goals']:
        if goal_data['agent'] == agent_name:
            agent_goal = PrivateGoal(
                description=goal_data['description'],
                goal_tier=goal_data['tier'],
                short_label=goal_data['label']
            )
            break

    if not agent_goal:
        raise ValueError(f"Goal not found for {agent_name}")

    # Reconstruct DiscoveryLog from game_log
    discovery_log = DiscoveryLog()
    for round_log in trial_data['game_log']['rounds']:
        round_num = round_log['round']

        # Get observation for this agent
        obs = round_log['observations'].get(agent_name, '')
        if obs:
            # Parse observation to extract ALL fields (region, resources, events, agents, inventory, settlement)
            lines = obs.split('\n')
            region = None
            resources = {'food': 0, 'water': 0, 'gold': 0}
            events = []
            agents_present = []
            inventory = {}
            settlement_status = None

            for line in lines:
                if 'You are in:' in line:
                    region = line.split('You are in:')[1].split('|')[0].strip()
                    # Also extract agents present from same line
                    if 'Agents here:' in line:
                        agents_part = line.split('Agents here:')[1].strip()
                        agents_present = [a.strip() for a in agents_part.split(',')]
                elif 'Resources here:' in line:
                    # Parse resources from line
                    res_part = line.split('Resources here:')[1].strip()
                    if 'No resources' not in res_part:
                        # Extract numbers and resource names
                        import re
                        food_match = re.search(r'(\d+)\s+food', res_part)
                        water_match = re.search(r'(\d+)\s+water', res_part)
                        gold_match = re.search(r'(\d+)\s+gold', res_part)
                        if food_match:
                            resources['food'] = int(food_match.group(1))
                        if water_match:
                            resources['water'] = int(water_match.group(1))
                        if gold_match:
                            resources['gold'] = int(gold_match.group(1))
                elif 'Events here:' in line:
                    # Next lines until we hit another section are events
                    continue
                elif line.startswith('  - '):
                    # This is an event
                    events.append(line.strip('  - ').strip())
                elif 'Your inventory:' in line:
                    # Parse inventory
                    inv_part = line.split('Your inventory:')[1].strip()
                    import re
                    food_match = re.search(r'(\d+)\s+food', inv_part)
                    water_match = re.search(r'(\d+)\s+water', inv_part)
                    gold_match = re.search(r'(\d+)\s+gold', inv_part)
                    inventory = {
                        'food': int(food_match.group(1)) if food_match else 0,
                        'water': int(water_match.group(1)) if water_match else 0,
                        'gold': int(gold_match.group(1)) if gold_match else 0
                    }
                elif 'Settlement:' in line:
                    # Capture full settlement status
                    settlement_status = line.split('Settlement:')[1].strip()

            if region:
                discovery_log.entries.append({
                    'round': round_num,
                    'region': region,
                    'resources': resources,
                    'events': events,
                    'agents_present': agents_present,
                    'inventory': inventory,
                    'settlement_status': settlement_status
                })

    # Create entity with all components
    agent = Entity(
        name=agent_name,
        position=Single_Point_Position(),
        actions=[],
        components=[
            agent_goal,
            discovery_log,
            ActionLog(),
            RegionTracker(starting_region='Forest'),  # Placeholder
            ScoutInventory(),
            MemorySummary(),
            PlanLog()
        ],
        tags=["scout", "agent"]
    )

    return agent


def reclassify_single_trial(trial_path: str) -> Dict[str, Any]:
    """Reclassify a single trial and return updated data."""
    try:
        # Load trial
        with open(trial_path, 'r') as f:
            trial_data = json.load(f)

        # Reconstruct agents
        agent_names = [f"Agent_{i}" for i in range(4)]
        agents = []
        for agent_name in agent_names:
            try:
                agent = reconstruct_agent_from_trial(trial_data, agent_name)
                agents.append(agent)
            except Exception as e:
                print(f"Warning: Could not reconstruct {agent_name} in {trial_path}: {e}")
                continue

        if not agents:
            return {'success': False, 'trial': trial_path, 'error': 'No agents reconstructed'}

        # Reconstruct ground truth
        ground_truth = GroundTruthLog()

        # Reconstruct message log (simplified - not used by promise classifier)
        # Just create a simple object with messages attribute
        from types import SimpleNamespace
        message_log = SimpleNamespace(messages=[])

        # Run classification
        game_log = trial_data['game_log']
        new_classification = classify_all(game_log, ground_truth, message_log, agents)

        # Update trial data
        trial_data['classification'] = new_classification
        trial_data['classifier_version'] = 'llm_v1'  # Mark as LLM-classified

        # Save updated trial
        with open(trial_path, 'w') as f:
            json.dump(trial_data, f, indent=2)

        # Compute stats
        old_fabrication_count = sum(1 for m in trial_data.get('classification', {}).get('messages', [])
                                      if m.get('label') == 'fabrication')
        new_fabrication_count = new_classification['summary'].get('fabrications', 0)

        return {
            'success': True,
            'trial': trial_path,
            'old_fabrications': old_fabrication_count,
            'new_fabrications': new_fabrication_count,
            'total_messages': new_classification['summary'].get('total_messages', 0)
        }

    except Exception as e:
        return {
            'success': False,
            'trial': trial_path,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def find_all_trials(results_dir: Path) -> List[str]:
    """Find all trial JSON files in results directory."""
    trials = []
    for exp_dir in results_dir.iterdir():
        if exp_dir.is_dir() and not exp_dir.name.startswith('.'):
            for trial_file in exp_dir.glob('trial_*.json'):
                trials.append(str(trial_file))
    return sorted(trials)


def main():
    print("=" * 80)
    print("RECLASSIFYING TRIALS WITH LLM MESSAGE CLASSIFIER")
    print("=" * 80)
    print()

    # Find all trials
    results_dir = Path('results')
    if not results_dir.exists():
        print(f"Error: {results_dir} not found")
        return 1

    trials = find_all_trials(results_dir)
    print(f"Found {len(trials)} trials to reclassify")
    print()

    # Group by condition for reporting
    by_condition = {}
    for trial_path in trials:
        condition = None
        if 'all_aligned' in trial_path:
            condition = 'all_aligned'
        elif 'all_competitive' in trial_path:
            condition = 'all_competitive'
        elif 'mixed' in trial_path:
            condition = 'mixed'
        else:
            condition = 'unknown'

        if condition not in by_condition:
            by_condition[condition] = []
        by_condition[condition].append(trial_path)

    for condition, paths in by_condition.items():
        print(f"  {condition}: {len(paths)} trials")
    print()

    # Ask for confirmation
    response = input(f"Reclassify {len(trials)} trials with 50 workers? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return 0

    print()
    print("Starting reclassification with 50 concurrent API requests...")
    print("(This will make many LLM API calls - ensure OPENAI_API_KEY is set)")
    print()

    # Use ThreadPoolExecutor for true concurrent API requests
    # As each request completes, the next one starts immediately
    num_workers = 50
    print(f"Using {num_workers} concurrent threads")
    print()

    results = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks and track with futures
        future_to_trial = {executor.submit(reclassify_single_trial, trial): trial
                          for trial in trials}

        # Process results as they complete
        for future in tqdm(as_completed(future_to_trial),
                          total=len(trials),
                          desc="Reclassifying trials",
                          unit="trial"):
            result = future.result()
            results.append(result)

    print()
    print("=" * 80)
    print("RECLASSIFICATION COMPLETE")
    print("=" * 80)
    print()

    # Summary statistics
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Successful: {len(successful)}/{len(trials)}")
    print(f"Failed: {len(failed)}/{len(trials)}")
    print()

    if failed:
        print("Failed trials:")
        for r in failed[:10]:  # Show first 10
            print(f"  {r['trial']}: {r['error']}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
        print()

    # Fabrication rate changes
    if successful:
        print("Fabrication rate changes:")
        by_condition_stats = {}

        for r in successful:
            trial_path = r['trial']
            condition = None
            if 'all_aligned' in trial_path:
                condition = 'all_aligned'
            elif 'all_competitive' in trial_path:
                condition = 'all_competitive'
            elif 'mixed' in trial_path:
                condition = 'mixed'

            if condition:
                if condition not in by_condition_stats:
                    by_condition_stats[condition] = {
                        'trials': 0,
                        'old_fabrications': 0,
                        'new_fabrications': 0,
                        'total_messages': 0
                    }

                stats = by_condition_stats[condition]
                stats['trials'] += 1
                stats['old_fabrications'] += r.get('old_fabrications', 0)
                stats['new_fabrications'] += r.get('new_fabrications', 0)
                stats['total_messages'] += r.get('total_messages', 0)

        for condition, stats in sorted(by_condition_stats.items()):
            old_rate = 100 * stats['old_fabrications'] / stats['total_messages'] if stats['total_messages'] > 0 else 0
            new_rate = 100 * stats['new_fabrications'] / stats['total_messages'] if stats['total_messages'] > 0 else 0
            change = new_rate - old_rate

            print(f"\n  {condition}:")
            print(f"    Trials: {stats['trials']}")
            print(f"    Messages: {stats['total_messages']}")
            print(f"    Old fabrication rate: {old_rate:.2f}%")
            print(f"    New fabrication rate: {new_rate:.2f}%")
            print(f"    Change: {change:+.2f}%")

    print()
    print("Done! All trials have been reclassified with LLM message classifier.")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
