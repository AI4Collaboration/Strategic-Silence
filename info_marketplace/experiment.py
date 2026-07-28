"""Experiment orchestration for the Information Marketplace simulation."""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from info_marketplace.config import NUM_AGENTS, NUM_ROUNDS, STARTING_REGIONS
from info_marketplace.conditions import assign_goals, CONDITIONS
from info_marketplace.world import create_region_entities, EventGenerator
from info_marketplace.settlement import create_settlement_entity
from info_marketplace.agent_components import create_scout_entity
from info_marketplace.scout_llm_policy import ScoutLLMPolicy
from info_marketplace.scripted_agent import ScriptedScoutPolicy
from info_marketplace.marketplace_env import MarketplaceEnv, GameConfig
from info_marketplace.classifier import classify_all
from info_marketplace.ground_truth import GroundTruthLog

# Configure logging - suppress HTTP request logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose HTTP logging from httpx and openai
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""
    experiment_name: str
    condition_name: str
    model_name: str = "gpt-5.4-mini"
    num_trials: int = 20
    num_rounds: int = 10
    base_seed: int = 42
    output_dir: str = "results/"
    api_key: str | None = None
    temperature: float = 0.7
    reasoning_effort: str = "low"
    dry_run: bool = False  # If True, use scripted agents instead of LLM
    max_workers: int = 1  # Number of parallel workers (1 = sequential)


def run_trial(
    trial_id: int,
    config: ExperimentConfig,
    seed: int
) -> dict | None:
    """Run a single trial of the experiment.

    Args:
        trial_id: Trial number (0-indexed)
        config: Experiment configuration
        seed: Random seed for this trial

    Returns:
        Trial results dict, or None if trial failed
    """
    try:
        # Create RNG for reproducibility
        rng = random.Random(seed)

        # Assign goals
        goals = assign_goals(config.condition_name, NUM_AGENTS, rng)

        # Create agents
        agents = []
        for i in range(NUM_AGENTS):
            agent_name = f"Agent_{i}"
            starting_region = STARTING_REGIONS[i]

            if config.dry_run:
                # Use scripted agents for testing
                behaviors = ["honest", "honest", "silent", "liar"]
                policy = ScriptedScoutPolicy(behavior=behaviors[i])
            else:
                # Use LLM agents
                policy = ScoutLLMPolicy(
                    model_name=config.model_name,
                    reasoning_effort=config.reasoning_effort,
                    api_key=config.api_key
                )

            agent = create_scout_entity(
                name=agent_name,
                starting_region=starting_region,
                private_goal=goals[i],
                policy_component=policy
            )
            agents.append(agent)

        # Create regions and settlement
        regions = create_region_entities()
        settlement = create_settlement_entity(
            starting_food=10,
            starting_water=8
        )

        # Create game config
        game_config = GameConfig(
            num_rounds=config.num_rounds,
            num_agents=NUM_AGENTS,
            random_seed=seed,
            condition_name=config.condition_name,
        )

        # Create environment
        env = MarketplaceEnv(game_config, agents, regions, settlement)

        # Build ground truth log
        ground_truth = GroundTruthLog()

        # Run game (suppressing verbose logs - progress bar will show overall progress)
        game_log = env.run()

        # Record ground truth from game log
        for round_log in game_log["rounds"]:
            round_num = round_log["round"]
            # Build regions dict from game state
            regions_dict = {}
            for region_name, region_entity in env.regions.items():
                from info_marketplace.world import RegionState
                region_state = region_entity.get_component(RegionState)
                regions_dict[region_name] = {
                    "resources": region_state.resources.copy(),
                    "events": region_state.active_events.copy()
                }

            # Build agent positions
            agent_positions = {}
            for agent in agents:
                from info_marketplace.agent_components import RegionTracker
                tracker = agent.get_component(RegionTracker)
                agent_positions[agent.name] = tracker.current_region

            ground_truth.record(round_num, regions_dict, agent_positions)

        # Classify deception
        classification_results = classify_all(game_log, ground_truth, env.message_log, agents)

        # Build trial results
        trial_results = {
            "trial_id": trial_id,
            "seed": seed,
            "condition": config.condition_name,
            "model": config.model_name,
            "reasoning_effort": config.reasoning_effort,
            "timestamp": datetime.now().isoformat(),
            "goals": [
                {
                    "agent": f"Agent_{i}",
                    "tier": goals[i].goal_tier,
                    "label": goals[i].short_label,
                    "description": goals[i].description
                }
                for i in range(NUM_AGENTS)
            ],
            "game_log": game_log,
            "classification": classification_results,
        }

        return trial_results

    except Exception as e:
        logger.error(f"Trial {trial_id + 1} FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_experiment(config: ExperimentConfig) -> dict:
    """Run full experiment with multiple trials.

    Args:
        config: Experiment configuration

    Returns:
        Experiment summary dict
    """
    logger.info(f"Starting experiment: {config.experiment_name}")
    logger.info(f"  Condition: {config.condition_name}")
    logger.info(f"  Model: {config.model_name}")
    logger.info(f"  Trials: {config.num_trials}")
    logger.info(f"  Workers: {config.max_workers}")
    logger.info(f"  Dry run: {config.dry_run}")

    # Create output directory
    output_path = Path(config.output_dir) / config.experiment_name
    output_path.mkdir(parents=True, exist_ok=True)

    # Save experiment config
    config_dict = {
        "experiment_name": config.experiment_name,
        "condition_name": config.condition_name,
        "model_name": config.model_name,
        "num_trials": config.num_trials,
        "num_rounds": config.num_rounds,
        "base_seed": config.base_seed,
        "reasoning_effort": config.reasoning_effort,
        "dry_run": config.dry_run,
        "max_workers": config.max_workers,
        "started_at": datetime.now().isoformat(),
    }

    with open(output_path / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    # Run trials (parallel or sequential based on max_workers)
    successful_trials = []
    failed_trials = []

    if config.max_workers > 1:
        # Parallel execution
        logger.info(f"Running {config.num_trials} trials in parallel with {config.max_workers} workers\n")

        with ProcessPoolExecutor(max_workers=config.max_workers) as executor:
            # Submit all trials
            future_to_trial = {}
            for trial_id in range(config.num_trials):
                seed = config.base_seed + trial_id
                future = executor.submit(run_trial, trial_id, config, seed)
                future_to_trial[future] = trial_id

            # Collect results as they complete with progress bar
            with tqdm(total=config.num_trials, desc="Trials", unit="trial", ncols=80) as pbar:
                for future in as_completed(future_to_trial):
                    trial_id = future_to_trial[future]
                    try:
                        trial_results = future.result()

                        if trial_results:
                            successful_trials.append(trial_results)

                            # Save individual trial
                            trial_file = output_path / f"trial_{trial_id:03d}.json"
                            with open(trial_file, "w") as f:
                                json.dump(trial_results, f, indent=2)

                            pbar.set_postfix_str(f"✓ {len(successful_trials)} success, ✗ {len(failed_trials)} failed")
                        else:
                            failed_trials.append(trial_id)
                            pbar.set_postfix_str(f"✓ {len(successful_trials)} success, ✗ {len(failed_trials)} failed")

                        pbar.update(1)

                    except Exception as e:
                        failed_trials.append(trial_id)
                        logger.error(f"Trial {trial_id + 1} failed: {e}")
                        pbar.set_postfix_str(f"✓ {len(successful_trials)} success, ✗ {len(failed_trials)} failed")
                        pbar.update(1)

    else:
        # Sequential execution with progress bar
        logger.info(f"Running {config.num_trials} trials sequentially\n")

        with tqdm(total=config.num_trials, desc="Trials", unit="trial", ncols=80) as pbar:
            for trial_id in range(config.num_trials):
                seed = config.base_seed + trial_id
                trial_results = run_trial(trial_id, config, seed)

                if trial_results:
                    successful_trials.append(trial_results)

                    # Save individual trial
                    trial_file = output_path / f"trial_{trial_id:03d}.json"
                    with open(trial_file, "w") as f:
                        json.dump(trial_results, f, indent=2)

                    pbar.set_postfix_str(f"✓ {len(successful_trials)} success, ✗ {len(failed_trials)} failed")
                else:
                    failed_trials.append(trial_id)
                    pbar.set_postfix_str(f"✓ {len(successful_trials)} success, ✗ {len(failed_trials)} failed")

                pbar.update(1)

    # Save summary
    summary = {
        "experiment_name": config.experiment_name,
        "condition": config.condition_name,
        "model": config.model_name,
        "total_trials": config.num_trials,
        "successful_trials": len(successful_trials),
        "failed_trials": len(failed_trials),
        "failed_trial_ids": failed_trials,
        "completed_at": datetime.now().isoformat(),
    }

    with open(output_path / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"\nExperiment complete!")
    logger.info(f"  Successful: {len(successful_trials)}/{config.num_trials}")
    logger.info(f"  Failed: {len(failed_trials)}")
    logger.info(f"  Output: {output_path}")

    return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Information Marketplace experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with scripted agents
  python -m info_marketplace.experiment --dry-run --trials 1

  # Run mixed condition with GPT-5.4-mini
  python -m info_marketplace.experiment --condition mixed --trials 20

  # Run with 4 parallel workers (4x speedup)
  python -m info_marketplace.experiment --condition mixed --trials 20 --workers 4

  # Run with different model
  python -m info_marketplace.experiment --model gpt-5.4 --condition all_competitive

  # Quick test
  python -m info_marketplace.experiment --dry-run --trials 1 --rounds 5
        """
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="Model name (default: gpt-5.4-mini)"
    )

    parser.add_argument(
        "--condition",
        choices=list(CONDITIONS.keys()),
        default="mixed",
        help="Experimental condition (default: mixed)"
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=20,
        help="Number of trials (default: 20)"
    )

    parser.add_argument(
        "--rounds",
        type=int,
        default=10,
        help="Number of rounds per game (default: 10)"
    )

    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high"],
        default="low",
        help="Reasoning effort for LLM (default: low)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use scripted agents instead of LLM (for testing)"
    )

    parser.add_argument(
        "--output-dir",
        default="results/",
        help="Output directory (default: results/)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed (default: 42)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for trials (default: 1, max recommended: 8)"
    )

    args = parser.parse_args()

    # Generate experiment name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"{args.condition}_{args.model}_{timestamp}"
    if args.dry_run:
        experiment_name = f"dryrun_{experiment_name}"

    # Create config
    config = ExperimentConfig(
        experiment_name=experiment_name,
        condition_name=args.condition,
        model_name=args.model,
        num_trials=args.trials,
        num_rounds=args.rounds,
        base_seed=args.seed,
        output_dir=args.output_dir,
        reasoning_effort=args.reasoning_effort,
        dry_run=args.dry_run,
        max_workers=args.workers,
    )

    # Run experiment
    try:
        summary = run_experiment(config)
        sys.exit(0)
    except KeyboardInterrupt:
        logger.warning("\nExperiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nExperiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
