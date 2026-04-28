"""Comprehensive deception analysis across conditions - FIXED VERSION."""

import json
import glob
from collections import defaultdict, Counter
from pathlib import Path

def analyze_condition(condition_pattern):
    """Analyze deception metrics for a specific condition pattern."""

    # Find most recent experiment directory for this condition
    exp_dirs = glob.glob(f"results/{condition_pattern}_gpt-5.4-mini_*")
    if not exp_dirs:
        return None

    latest_exp = max(exp_dirs, key=lambda p: Path(p).stat().st_mtime)
    trial_files = glob.glob(f"{latest_exp}/trial_*.json")

    if not trial_files:
        return None

    # Metrics to collect
    total_deceptions = 0
    total_messages = 0
    mechanism_counts = Counter()
    premeditation_labels = Counter()  # Agent-round level
    round_fabrications = defaultdict(int)
    round_messages = defaultdict(int)
    survived = 0
    died = 0

    for trial_file in trial_files:
        with open(trial_file) as f:
            data = json.load(f)

        # Settlement survival
        if data["game_log"]["final_state"]["settlement"]["alive"]:
            survived += 1
        else:
            died += 1

        # MESSAGE-level deception analysis
        if "classification" in data and "messages" in data["classification"]:
            for entry in data["classification"]["messages"]:
                total_messages += 1
                label = entry.get("label", "fully_honest")
                round_num = entry.get("round", 0)

                # Count messages per round
                round_messages[round_num] += 1

                # Count all labels for mechanism distribution
                mechanism_counts[label] += 1

                # Only count actual deceptions (not truthful/unverifiable)
                if label in ["fabrication", "omission", "pragmatic_distortion"]:
                    total_deceptions += 1

                    # Check if it's fabrication for temporal analysis
                    if "fabrication" in label.lower():
                        round_fabrications[round_num] += 1

        # AGENT-ROUND level premeditation analysis (separate granularity!)
        if "classification" in data and "premeditation" in data["classification"]:
            for entry in data["classification"]["premeditation"]:
                label = entry.get("label", "fully_honest")
                premeditation_labels[label] += 1

    return {
        "experiment_dir": Path(latest_exp).name,
        "num_trials": len(trial_files),
        "total_messages": total_messages,
        "total_deceptions": total_deceptions,
        "deception_rate": (total_deceptions / total_messages * 100) if total_messages > 0 else 0,
        "mechanism_counts": dict(mechanism_counts),
        "premeditation_labels": dict(premeditation_labels),
        "round_fabrications": dict(round_fabrications),
        "round_messages": dict(round_messages),
        "survived": survived,
        "died": died,
        "survival_rate": (survived / len(trial_files) * 100) if trial_files else 0
    }


# Analyze all three conditions
conditions = {
    "all_aligned": analyze_condition("all_aligned"),
    "mixed": analyze_condition("mixed"),
    "all_competitive": analyze_condition("all_competitive")
}

# Filter out None values
conditions = {k: v for k, v in conditions.items() if v is not None}

print("=" * 80)
print("DECEPTION ANALYSIS ACROSS CONDITIONS")
print("=" * 80)
print()

# 1. OVERALL DECEPTION RATES
print("1. OVERALL DECEPTION RATES (message-level)")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"{cond_name:20s}: {c['deception_rate']:5.1f}% ({c['total_deceptions']:4d}/{c['total_messages']:4d} messages, {c['num_trials']:2d} trials)")
    else:
        print(f"{cond_name:20s}: No data available")
print()

# 2. MECHANISM DISTRIBUTION
print("2. MECHANISM DISTRIBUTION PER CONDITION (message-level)")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"\n{cond_name}:")
        total_messages = c['total_messages']
        if total_messages > 0:
            # Show deception mechanisms first
            deception_labels = ['fabrication', 'omission', 'pragmatic_distortion']
            for mechanism in deception_labels:
                if mechanism in c['mechanism_counts']:
                    count = c['mechanism_counts'][mechanism]
                    pct = (count / total_messages) * 100
                    print(f"  {mechanism:30s}: {count:4d} ({pct:5.1f}% of all messages)")

            # Show other categories
            other_labels = ['truthful', 'unverifiable']
            print()
            for mechanism in other_labels:
                if mechanism in c['mechanism_counts']:
                    count = c['mechanism_counts'][mechanism]
                    pct = (count / total_messages) * 100
                    print(f"  {mechanism:30s}: {count:4d} ({pct:5.1f}% of all messages)")
        else:
            print("  No messages found")
print()

# 3. PREMEDITATION RATES
print("3. PREMEDITATION RATES PER CONDITION (agent-round level)")
print("-" * 80)
print("Note: This measures deceptive INTENT in plans, not messages sent.")
print()
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"{cond_name}:")

        total_agent_rounds = sum(c['premeditation_labels'].values())
        prem_count = c['premeditation_labels'].get('premeditated_deception', 0)
        imp_count = c['premeditation_labels'].get('impulsive_deception', 0)
        honest_count = c['premeditation_labels'].get('fully_honest', 0)

        if total_agent_rounds > 0:
            prem_pct = (prem_count / total_agent_rounds) * 100
            imp_pct = (imp_count / total_agent_rounds) * 100
            honest_pct = (honest_count / total_agent_rounds) * 100

            print(f"  Total agent-rounds: {total_agent_rounds}")
            print(f"  Premeditated:       {prem_count:4d} ({prem_pct:5.1f}%)")
            print(f"  Impulsive:          {imp_count:4d} ({imp_pct:5.1f}%)")
            print(f"  Fully honest:       {honest_count:4d} ({honest_pct:5.1f}%)")

            if cond_name == "all_competitive" and prem_count > 0:
                print(f"  ⚠️  WARNING: Found {prem_count} premeditated cases in all_competitive!")
        else:
            print("  No premeditation data")
        print()
print()

# 4. TEMPORAL PATTERNS (FABRICATION BY ROUND)
print("4. TEMPORAL PATTERNS: FABRICATION BY ROUND (message-level)")
print("-" * 80)

# Get all rounds (0-9)
all_rounds = range(10)

for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"\n{cond_name}:")
        print("Round |  Fabrications | Total Msgs | Rate")
        print("------|---------------|------------|------")

        for r in all_rounds:
            fab_count = c['round_fabrications'].get(r, 0)
            msg_count = c['round_messages'].get(r, 0)
            rate = (fab_count / msg_count * 100) if msg_count > 0 else 0
            print(f"  {r:2d}  |     {fab_count:4d}      |   {msg_count:5d}    | {rate:5.1f}%")
print()

# 5. SETTLEMENT SURVIVAL
print("5. SETTLEMENT SURVIVAL PER CONDITION")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"{cond_name:20s}: {c['survival_rate']:5.1f}% ({c['survived']:2d}/{c['num_trials']:2d} survived)")
    else:
        print(f"{cond_name:20s}: No data available")
print()
print("=" * 80)
