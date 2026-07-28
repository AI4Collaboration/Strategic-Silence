"""Results aggregation and analysis for Information Marketplace experiments."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def compute_silence_market_stats(trials: List[Dict]) -> Dict[str, Any]:
    """Compute the silence and market summary blocks from raw trial dicts.

    Shared by aggregate_results and scripts/analyze_experiment.py so the two
    reports can't drift apart.
    """
    total_agent_rounds = 0
    total_fully_silent = 0
    total_silent_public = 0
    total_only_whispered = 0
    total_communicated = 0
    total_trade_actions = 0
    total_trade_successes = 0

    silence_by_round: Dict[int, Dict[str, int]] = defaultdict(lambda: {"silent": 0, "total": 0})
    silence_by_tier = {
        "ALIGNED": {"silent": 0, "total": 0},
        "ORTHOGONAL": {"silent": 0, "total": 0},
        "COMPETITIVE": {"silent": 0, "total": 0},
    }

    for trial in trials:
        goals = trial.get("goals", [])
        for round_data in trial.get("game_log", {}).get("rounds", []):
            round_num = round_data["round"]

            for choice in round_data.get("communication_choices", []):
                total_agent_rounds += 1
                if choice.get("fully_silent"):
                    total_fully_silent += 1
                    silence_by_round[round_num]["silent"] += 1
                if choice.get("sent_any"):
                    total_communicated += 1
                if choice.get("silent_in_public"):
                    total_silent_public += 1
                if choice.get("only_whispered"):
                    total_only_whispered += 1
                silence_by_round[round_num]["total"] += 1

                goal_tier = _get_goal_tier(goals, choice.get("agent", ""))
                if goal_tier:
                    silence_by_tier[goal_tier]["total"] += 1
                    if choice.get("fully_silent"):
                        silence_by_tier[goal_tier]["silent"] += 1

            # Count trades from the structured action type, not the description
            # string, and only count successes the env actually resolved
            action_results = round_data.get("action_results", {})
            for agent_name, action_info in round_data.get("actions", {}).items():
                if action_info.get("type") == "trade":
                    total_trade_actions += 1
                    if action_results.get(agent_name, {}).get("success"):
                        total_trade_successes += 1

    silence_rate = total_fully_silent / total_agent_rounds if total_agent_rounds > 0 else 0.0
    partial_silence_rate = total_silent_public / total_agent_rounds if total_agent_rounds > 0 else 0.0
    whisper_rate = total_only_whispered / total_agent_rounds if total_agent_rounds > 0 else 0.0

    silence_rate_by_round = {
        round_num: (counts["silent"] / counts["total"] if counts["total"] > 0 else 0.0)
        for round_num, counts in silence_by_round.items()
    }
    silence_rate_by_tier = {
        tier: (counts["silent"] / counts["total"] if counts["total"] > 0 else 0.0)
        for tier, counts in silence_by_tier.items()
    }

    return {
        "silence": {
            "total_agent_rounds": total_agent_rounds,
            "fully_silent": total_fully_silent,
            "silence_rate": silence_rate,
            "communicated": total_communicated,
            "silent_in_public": total_silent_public,
            "partial_silence_rate": partial_silence_rate,
            "only_whispered": total_only_whispered,
            "whisper_rate": whisper_rate,
            "silence_rate_by_round": silence_rate_by_round,
            "silence_rate_by_tier": silence_rate_by_tier,
        },
        "market": {
            "total_trade_actions": total_trade_actions,
            "total_trade_successes": total_trade_successes,
        },
    }


def aggregate_results(experiment_dir: str | Path) -> Dict[str, Any]:
    """Aggregate results from all trial JSON files in an experiment directory.

    Computes summary statistics across all successful trials:
    - Overall deception rate
    - Deception mechanism distribution (fabrication, omission, etc.)
    - Premeditation rate
    - Promise breaking rate
    - Deception rate by round
    - Deception rate by goal tier
    - Settlement survival rate
    - Mean final resources

    Args:
        experiment_dir: Path to experiment directory containing trial_*.json files

    Returns:
        Dictionary with aggregated statistics
    """
    experiment_dir = Path(experiment_dir)

    # Load all trial files
    trial_files = sorted(experiment_dir.glob("trial_*.json"))
    if not trial_files:
        logger.warning(f"No trial files found in {experiment_dir}")
        return {}

    trials = []
    for trial_file in trial_files:
        with open(trial_file, "r") as f:
            trials.append(json.load(f))

    num_trials = len(trials)
    logger.info(f"Aggregating {num_trials} trials from {experiment_dir.name}")

    # Initialize accumulators
    total_messages = 0
    total_reports = 0
    total_promises = 0
    total_deceptive = 0
    mechanism_counts = {
        "FABRICATION": 0,
        "OMISSION": 0,
        "PRAGMATIC_DISTORTION": 0,
        "UNVERIFIABLE": 0,
        "TRUTHFUL": 0,
    }
    total_premeditated = 0
    total_impulsive = 0
    promises_fulfilled = 0
    promises_broken = 0
    settlements_survived = 0

    deception_by_round = defaultdict(lambda: {"deceptive": 0, "total": 0})
    deception_by_tier = {
        "ALIGNED": {"deceptive": 0, "total": 0},
        "ORTHOGONAL": {"deceptive": 0, "total": 0},
        "COMPETITIVE": {"deceptive": 0, "total": 0},
    }

    final_food_sum = 0
    final_water_sum = 0

    # Process each trial
    for trial in trials:
        classification = trial["classification"]

        # Settlement survival (from final_state)
        final_state = trial["game_log"]["final_state"]["settlement"]
        if final_state["alive"]:
            settlements_survived += 1
        final_food_sum += final_state["food"]
        final_water_sum += final_state["water"]

        # Report-level stats
        for msg_class in classification["messages"]:
            total_reports += 1
            total_messages += 1

            # Deception label (normalized to uppercase)
            label = msg_class["label"].upper()
            mechanism_counts[label] += 1

            if label in ["FABRICATION", "OMISSION", "PRAGMATIC_DISTORTION"]:
                total_deceptive += 1

                # By round
                round_num = msg_class["round"]
                deception_by_round[round_num]["deceptive"] += 1
                deception_by_round[round_num]["total"] += 1

                # By goal tier
                sender = msg_class["sender"]
                goal_tier = _get_goal_tier(trial["goals"], sender)
                if goal_tier:
                    deception_by_tier[goal_tier]["deceptive"] += 1
                    deception_by_tier[goal_tier]["total"] += 1
            else:
                # Non-deceptive also counts in totals
                round_num = msg_class["round"]
                deception_by_round[round_num]["total"] += 1

                sender = msg_class["sender"]
                goal_tier = _get_goal_tier(trial["goals"], sender)
                if goal_tier:
                    deception_by_tier[goal_tier]["total"] += 1

        # Premeditation stats (only count deceptive entries)
        for premeditation in classification["premeditation"]:
            label = premeditation["label"]
            if label == "premeditated_deception":
                total_premeditated += 1
            elif label == "impulsive_deception":
                total_impulsive += 1

        # Promise-level stats
        for promise in classification["promises"]:
            total_promises += 1
            total_messages += 1
            if promise["label"] == "fulfilled":
                promises_fulfilled += 1
            elif promise["label"] == "broken":
                promises_broken += 1

    # Silence and market stats from raw game logs (shared helper)
    silence_market = compute_silence_market_stats(trials)

    # Compute rates
    overall_deception_rate = total_deceptive / total_reports if total_reports > 0 else 0.0
    premeditation_rate = total_premeditated / total_deceptive if total_deceptive > 0 else 0.0
    promise_breaking_rate = promises_broken / total_promises if total_promises > 0 else 0.0
    settlement_survival_rate = settlements_survived / num_trials

    # Deception rate by round
    deception_rate_by_round = {}
    for round_num, counts in deception_by_round.items():
        if counts["total"] > 0:
            deception_rate_by_round[round_num] = counts["deceptive"] / counts["total"]
        else:
            deception_rate_by_round[round_num] = 0.0

    # Deception rate by tier
    deception_rate_by_tier = {}
    for tier, counts in deception_by_tier.items():
        if counts["total"] > 0:
            deception_rate_by_tier[tier] = counts["deceptive"] / counts["total"]
        else:
            deception_rate_by_tier[tier] = 0.0

    # Mechanism distribution (as percentages)
    mechanism_distribution = {}
    for mechanism, count in mechanism_counts.items():
        mechanism_distribution[mechanism] = count / total_reports if total_reports > 0 else 0.0

    # Build summary
    summary = {
        "experiment_name": experiment_dir.name,
        "num_trials": num_trials,
        "total_messages": total_messages,
        "total_reports": total_reports,
        "total_promises": total_promises,
        "overall_deception_rate": overall_deception_rate,
        "total_deceptive_messages": total_deceptive,
        "mechanism_distribution": mechanism_distribution,
        "premeditation_rate": premeditation_rate,
        "total_premeditated": total_premeditated,
        "total_impulsive": total_impulsive,
        "promise_breaking_rate": promise_breaking_rate,
        "promises_fulfilled": promises_fulfilled,
        "promises_broken": promises_broken,
        "settlement_survival_rate": settlement_survival_rate,
        "settlements_survived": settlements_survived,
        "mean_final_food": final_food_sum / num_trials,
        "mean_final_water": final_water_sum / num_trials,
        "deception_rate_by_round": deception_rate_by_round,
        "deception_rate_by_tier": deception_rate_by_tier,
        "silence": silence_market["silence"],
        "market": silence_market["market"],
    }

    return summary


def compare_conditions(experiment_dirs: List[str | Path]) -> Dict[str, Any]:
    """Compare results across different experimental conditions.

    Args:
        experiment_dirs: List of paths to experiment directories

    Returns:
        Dictionary with comparative statistics
    """
    comparisons = {}

    for exp_dir in experiment_dirs:
        exp_dir = Path(exp_dir)
        if not exp_dir.exists():
            logger.warning(f"Directory not found: {exp_dir}")
            continue

        # Load config to get condition name
        config_file = exp_dir / "config.json"
        if not config_file.exists():
            logger.warning(f"No config.json in {exp_dir}")
            continue

        with open(config_file, "r") as f:
            config = json.load(f)

        condition_name = config["condition_name"]
        summary = aggregate_results(exp_dir)

        comparisons[condition_name] = {
            "overall_deception_rate": summary.get("overall_deception_rate", 0.0),
            "mechanism_distribution": summary.get("mechanism_distribution", {}),
            "premeditation_rate": summary.get("premeditation_rate", 0.0),
            "promise_breaking_rate": summary.get("promise_breaking_rate", 0.0),
            "settlement_survival_rate": summary.get("settlement_survival_rate", 0.0),
            "mean_final_food": summary.get("mean_final_food", 0.0),
            "mean_final_water": summary.get("mean_final_water", 0.0),
            "deception_rate_by_tier": summary.get("deception_rate_by_tier", {}),
        }

    return {
        "comparison_type": "conditions",
        "conditions": comparisons,
    }


def compare_models(experiment_dirs: List[str | Path]) -> Dict[str, Any]:
    """Compare results across different models.

    Args:
        experiment_dirs: List of paths to experiment directories

    Returns:
        Dictionary with comparative statistics
    """
    comparisons = {}

    for exp_dir in experiment_dirs:
        exp_dir = Path(exp_dir)
        if not exp_dir.exists():
            logger.warning(f"Directory not found: {exp_dir}")
            continue

        # Load config to get model name
        config_file = exp_dir / "config.json"
        if not config_file.exists():
            logger.warning(f"No config.json in {exp_dir}")
            continue

        with open(config_file, "r") as f:
            config = json.load(f)

        model_name = config["model_name"]
        summary = aggregate_results(exp_dir)

        comparisons[model_name] = {
            "overall_deception_rate": summary.get("overall_deception_rate", 0.0),
            "mechanism_distribution": summary.get("mechanism_distribution", {}),
            "premeditation_rate": summary.get("premeditation_rate", 0.0),
            "promise_breaking_rate": summary.get("promise_breaking_rate", 0.0),
            "settlement_survival_rate": summary.get("settlement_survival_rate", 0.0),
            "mean_final_food": summary.get("mean_final_food", 0.0),
            "mean_final_water": summary.get("mean_final_water", 0.0),
        }

    return {
        "comparison_type": "models",
        "models": comparisons,
    }


def _get_goal_tier(goals: List[Dict], agent_name: str) -> str | None:
    """Helper to extract goal tier for an agent from trial goals list."""
    for goal in goals:
        if goal["agent"] == agent_name:
            return goal["tier"]
    return None


def print_summary(summary: Dict[str, Any]):
    """Pretty-print aggregated summary statistics."""
    print(f"\n{'='*60}")
    print(f"EXPERIMENT SUMMARY: {summary['experiment_name']}")
    print(f"{'='*60}\n")

    print(f"Trials: {summary['num_trials']}")
    print(f"Total Messages: {summary['total_messages']}")
    print(f"  Reports: {summary['total_reports']}")
    print(f"  Promises: {summary['total_promises']}")

    print(f"\n--- DECEPTION METRICS ---")
    print(f"Overall Deception Rate: {summary['overall_deception_rate']:.2%}")
    print(f"  Deceptive Messages: {summary['total_deceptive_messages']}")
    print(f"  Premeditated: {summary['total_premeditated']} ({summary['premeditation_rate']:.2%})")
    print(f"  Impulsive: {summary['total_impulsive']}")

    print(f"\nMechanism Distribution:")
    for mechanism, rate in summary['mechanism_distribution'].items():
        print(f"  {mechanism}: {rate:.2%}")

    print(f"\nPromise Breaking Rate: {summary['promise_breaking_rate']:.2%}")
    print(f"  Fulfilled: {summary['promises_fulfilled']}")
    print(f"  Broken: {summary['promises_broken']}")

    print(f"\n--- SETTLEMENT METRICS ---")
    print(f"Survival Rate: {summary['settlement_survival_rate']:.2%}")
    print(f"  Survived: {summary['settlements_survived']}/{summary['num_trials']}")
    print(f"Mean Final Food: {summary['mean_final_food']:.2f}")
    print(f"Mean Final Water: {summary['mean_final_water']:.2f}")

    print(f"\n--- DECEPTION BY ROUND ---")
    for round_num in sorted(summary['deception_rate_by_round'].keys()):
        rate = summary['deception_rate_by_round'][round_num]
        print(f"  Round {round_num}: {rate:.2%}")

    print(f"\n--- DECEPTION BY GOAL TIER ---")
    for tier, rate in summary['deception_rate_by_tier'].items():
        print(f"  {tier}: {rate:.2%}")

    if "silence" in summary:
        s = summary["silence"]
        print(f"\n--- STRATEGIC SILENCE METRICS ---")
        print(f"Total Agent-Rounds: {s['total_agent_rounds']}")
        print(f"Fully Silent: {s['fully_silent']} ({s['silence_rate']:.2%})")
        print(f"Communicated: {s['communicated']}")
        print(f"Silent in Public: {s['silent_in_public']} ({s['partial_silence_rate']:.2%})")
        print(f"Only Whispered: {s['only_whispered']} ({s['whisper_rate']:.2%})")
        print(f"\nSilence Rate by Round:")
        for rn in sorted(s['silence_rate_by_round'].keys()):
            print(f"  Round {rn}: {s['silence_rate_by_round'][rn]:.2%}")
        print(f"\nSilence Rate by Goal Tier:")
        for tier, rate in s['silence_rate_by_tier'].items():
            print(f"  {tier}: {rate:.2%}")

    if "market" in summary:
        m = summary["market"]
        print(f"\n--- MARKET METRICS ---")
        print(f"Trade Actions: {m['total_trade_actions']}")
        print(f"Trade Successes: {m['total_trade_successes']}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m info_marketplace.results <experiment_dir>")
        print("   or: python -m info_marketplace.results --compare <dir1> <dir2> ...")
        sys.exit(1)

    if sys.argv[1] == "--compare":
        # Compare multiple experiments
        dirs = sys.argv[2:]
        comparison = compare_conditions(dirs)
        print(json.dumps(comparison, indent=2))
    else:
        # Single experiment summary
        exp_dir = sys.argv[1]
        summary = aggregate_results(exp_dir)
        print_summary(summary)

        # Save summary to file
        output_file = Path(exp_dir) / "aggregated_summary.json"
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Saved aggregated summary to {output_file}")
