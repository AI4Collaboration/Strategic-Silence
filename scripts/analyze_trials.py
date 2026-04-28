"""Analyze trial results from the 20-trial experiment."""

import json
import glob
from pathlib import Path

# Find all trial files from the most recent experiment directory
import os
exp_dirs = glob.glob("results/mixed_gpt-5.4-mini_*")
if not exp_dirs:
    print("No experiment directories found!")
    exit(1)

# Get the most recent directory
latest_exp = max(exp_dirs, key=os.path.getmtime)
print(f"Analyzing experiment: {os.path.basename(latest_exp)}")

trial_files = glob.glob(f"{latest_exp}/trial_*.json")

print(f"Found {len(trial_files)} trial files")

survived = 0
died = 0
total_food = 0
total_water = 0

for trial_file in sorted(trial_files):
    with open(trial_file) as f:
        data = json.load(f)

    trial_id = data["trial_id"]
    final_state = data["game_log"]["final_state"]
    settlement = final_state["settlement"]

    is_alive = settlement["alive"]
    food = settlement["food"]
    water = settlement["water"]

    if is_alive:
        survived += 1
        total_food += food
        total_water += water
        print(f"Trial {trial_id:2d}: SURVIVED - {food} food, {water} water")
    else:
        died += 1
        # Simplified death detection - just use final state
        print(f"Trial {trial_id:2d}: DIED - {food} food, {water} water")

total = survived + died
survival_rate = (survived / total) * 100 if total > 0 else 0

print(f"\n=== Summary ===")
print(f"Total trials: {total}")
print(f"Survived: {survived}")
print(f"Died: {died}")
print(f"Survival rate: {survival_rate:.1f}%")

if survived > 0:
    avg_food = total_food / survived
    avg_water = total_water / survived
    print(f"\nAverage final resources (survivors only):")
    print(f"  Food: {avg_food:.1f}")
    print(f"  Water: {avg_water:.1f}")
