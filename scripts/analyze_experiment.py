"""Comprehensive deception, silence, and market analysis across conditions."""

import json
import glob
import sys
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from info_marketplace.results import compute_silence_market_stats

def analyze_condition(condition_pattern):
    """Analyze all metrics for a specific condition pattern."""

    exp_dirs = glob.glob(f"results/{condition_pattern}_gpt-5.4-mini_*")
    if not exp_dirs:
        return None

    latest_exp = max(exp_dirs, key=lambda p: Path(p).stat().st_mtime)
    trial_files = glob.glob(f"{latest_exp}/trial_*.json")

    if not trial_files:
        return None

    # Deception metrics
    total_deceptions = 0
    total_messages = 0
    mechanism_counts = Counter()
    premeditation_labels = Counter()
    round_fabrications = defaultdict(int)
    round_messages = defaultdict(int)
    survived = 0
    died = 0

    trials = []
    for trial_file in trial_files:
        with open(trial_file) as f:
            data = json.load(f)
        trials.append(data)

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
                round_messages[round_num] += 1
                mechanism_counts[label] += 1
                if label in ["fabrication", "omission", "pragmatic_distortion"]:
                    total_deceptions += 1
                    if "fabrication" in label.lower():
                        round_fabrications[round_num] += 1

        # AGENT-ROUND level premeditation analysis
        if "classification" in data and "premeditation" in data["classification"]:
            for entry in data["classification"]["premeditation"]:
                label = entry.get("label", "fully_honest")
                premeditation_labels[label] += 1

    # Silence and market metrics via the shared aggregation in results.py
    silence_market = compute_silence_market_stats(trials)

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
        "survival_rate": (survived / len(trial_files) * 100) if trial_files else 0,
        "silence": silence_market["silence"],
        "market": silence_market["market"],
    }


conditions = {
    "all_aligned": analyze_condition("all_aligned"),
    "mixed": analyze_condition("mixed"),
    "all_competitive": analyze_condition("all_competitive")
}

conditions = {k: v for k, v in conditions.items() if v is not None}

print("=" * 80)
print("DECEPTION, SILENCE, AND MARKET ANALYSIS ACROSS CONDITIONS")
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
            for mechanism in ['fabrication', 'omission', 'pragmatic_distortion', 'truthful', 'unverifiable']:
                if mechanism in c['mechanism_counts']:
                    count = c['mechanism_counts'][mechanism]
                    pct = (count / total_messages) * 100
                    print(f"  {mechanism:30s}: {count:4d} ({pct:5.1f}%)")
        else:
            print("  No messages found")
print()

# 3. PREMEDITATION RATES
print("3. PREMEDITATION RATES PER CONDITION (agent-round level)")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"{cond_name}:")
        total_agent_rounds = sum(c['premeditation_labels'].values())
        prem = c['premeditation_labels'].get('premeditated_deception', 0)
        imp = c['premeditation_labels'].get('impulsive_deception', 0)
        honest = c['premeditation_labels'].get('fully_honest', 0)
        if total_agent_rounds > 0:
            print(f"  Total agent-rounds: {total_agent_rounds}")
            print(f"  Premeditated:       {prem:4d} ({(prem/total_agent_rounds)*100:5.1f}%)")
            print(f"  Impulsive:          {imp:4d} ({(imp/total_agent_rounds)*100:5.1f}%)")
            print(f"  Fully honest:       {honest:4d} ({(honest/total_agent_rounds)*100:5.1f}%)")
        print()
print()

# 4. STRATEGIC SILENCE METRICS
print("4. STRATEGIC SILENCE METRICS")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        s = c.get("silence", {})
        print(f"\n{cond_name}:")
        print(f"  Agent-rounds: {s.get('total_agent_rounds', 0)}")
        print(f"  Fully silent: {s.get('fully_silent', 0)} ({s.get('silence_rate', 0)*100:.1f}%)")
        print(f"  Communicated: {s.get('communicated', 0)}")
        print(f"  Silent in public: {s.get('silent_in_public', 0)} ({s.get('partial_silence_rate', 0)*100:.1f}%)")
        print(f"  Only whispered: {s.get('only_whispered', 0)} ({s.get('whisper_rate', 0)*100:.1f}%)")
        print(f"\n  Silence by round:")
        for rn in sorted(s.get('silence_rate_by_round', {}).keys()):
            rate = s['silence_rate_by_round'][rn]
            bar = '#' * int(rate * 50)
            print(f"    Round {rn:2d}: {rate*100:5.1f}% {bar}")
        print(f"\n  Silence by goal tier:")
        for tier, rate in s.get('silence_rate_by_tier', {}).items():
            print(f"    {tier:15s}: {rate*100:.1f}%")
print()

# 5. MARKET METRICS
print("5. MARKET METRICS")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        m = conditions[cond_name].get("market", {})
        print(f"{cond_name:20s}: {m.get('total_trade_actions', 0)} trade actions, {m.get('total_trade_successes', 0)} succeeded")
print()

# 6. TEMPORAL PATTERNS (FABRICATION BY ROUND)
print("6. TEMPORAL PATTERNS: FABRICATION BY ROUND")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"\n{cond_name}:")
        print("Round |  Fabrications | Total Msgs | Rate")
        print("------|---------------|------------|------")
        for r in range(10):
            fab = c['round_fabrications'].get(r, 0)
            msg = c['round_messages'].get(r, 0)
            rate = (fab / msg * 100) if msg > 0 else 0
            print(f"  {r:2d}  |     {fab:4d}      |   {msg:5d}    | {rate:5.1f}%")
print()

# 7. SETTLEMENT SURVIVAL
print("7. SETTLEMENT SURVIVAL PER CONDITION")
print("-" * 80)
for cond_name in ["all_aligned", "mixed", "all_competitive"]:
    if cond_name in conditions:
        c = conditions[cond_name]
        print(f"{cond_name:20s}: {c['survival_rate']:5.1f}% ({c['survived']:2d}/{c['num_trials']:2d} survived)")
    else:
        print(f"{cond_name:20s}: No data available")
print()

print("=" * 80)
