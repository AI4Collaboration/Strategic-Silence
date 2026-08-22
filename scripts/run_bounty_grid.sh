#!/bin/bash
# Resumable runner for the deception-bounty experiment grid.
#
# Baby-proof by design: every trial is written to disk the moment it
# finishes, experiment dirs have stable names, and completed trials are
# skipped on re-run. If this script (or the machine) dies at any point,
# just run it again — it continues exactly where it left off.
#
# Usage:
#   ./scripts/run_bounty_grid.sh            # run/resume the whole grid
#   ./scripts/run_bounty_grid.sh status     # show progress only, run nothing
#
# Arms (all: all_competitive, ring, deepseek-chat, 6 trials):
#   Supply curve (10 rounds):   b0 recount, b3, b8, b8 undisclosed
#   Feedback gradient (40 rounds, b8 undisclosed): none / itemized / attributed

set -uo pipefail
cd "$(dirname "$0")/.."

MODEL=deepseek-chat
TRIALS=6
WORKERS=6

# name | extra args
ARMS=(
  "b0_recount|--bounty 0"
  "b1_disclosed|--bounty 1"
  "b2_disclosed|--bounty 2"
  "b3_disclosed|--bounty 3"
  "b5_disclosed|--bounty 5"
  "b8_disclosed|--bounty 8"
  "b8_undisclosed|--bounty 8 --bounty-undisclosed"
  "b0_r40_control|--bounty 0 --rounds 40"
  "b8u_r40_none|--bounty 8 --bounty-undisclosed --bounty-feedback none --rounds 40"
  "b8u_r40_itemized|--bounty 8 --bounty-undisclosed --bounty-feedback itemized --rounds 40"
  "b8u_r40_attributed|--bounty 8 --bounty-undisclosed --bounty-feedback attributed --rounds 40"
)

# Completed 10-round arms from the timestamped pilot runs (already at 6/6):
# results/all_competitive_ring_deepseek-chat_20260821_154427       (b0 recount)
# results/all_competitive_b3_ring_deepseek-chat_20260821_151445    (b3)
# results/all_competitive_b8_ring_deepseek-chat_20260821_151447    (b8)
# results/all_competitive_b8u_ring_deepseek-chat_20260821_154429   (b8 undisclosed)
# The status/skip logic below counts those dirs so they are not re-run.
LEGACY_DIRS=(
  "b0_recount|results/all_competitive_ring_deepseek-chat_20260821_154427"
  "b3_disclosed|results/all_competitive_b3_ring_deepseek-chat_20260821_151445"
  "b8_disclosed|results/all_competitive_b8_ring_deepseek-chat_20260821_151447"
  "b8_undisclosed|results/all_competitive_b8u_ring_deepseek-chat_20260821_154429"
)

count_trials() {
  ls "$1"/trial_*.json 2>/dev/null | wc -l | tr -d ' '
}

legacy_count() {
  local arm="$1"
  for entry in "${LEGACY_DIRS[@]}"; do
    if [[ "${entry%%|*}" == "$arm" ]]; then
      count_trials "${entry##*|}"
      return
    fi
  done
  echo 0
}

echo "=== Bounty grid status ==="
for entry in "${ARMS[@]}"; do
  name="${entry%%|*}"
  done_new=$(count_trials "results/$name")
  done_legacy=$(legacy_count "$name")
  total=$((done_new + done_legacy))
  echo "  $name: $total/$TRIALS trials (stable dir: $done_new, legacy pilot: $done_legacy)"
done
echo

if [[ "${1:-}" == "status" ]]; then
  exit 0
fi

for entry in "${ARMS[@]}"; do
  name="${entry%%|*}"
  args="${entry##*|}"
  done_new=$(count_trials "results/$name")
  done_legacy=$(legacy_count "$name")
  total=$((done_new + done_legacy))

  if (( total >= TRIALS )); then
    echo ">>> $name complete ($total/$TRIALS), skipping"
    continue
  fi

  # Legacy trials used seeds 42..47; offset new seeds past them so a
  # topped-up arm never duplicates a seed
  need=$((TRIALS - done_legacy))
  seed=$((42 + done_legacy))

  echo ">>> $name: running (need $need trials in results/$name, seed base $seed)"
  python3 -m info_marketplace.experiment \
    --condition all_competitive --model "$MODEL" --workers "$WORKERS" \
    --trials "$need" --seed "$seed" --name "$name" $args \
    || echo "!!! $name exited nonzero — re-run this script to resume"
done

echo
echo "=== Grid pass finished. Analysis: ==="
python3 scripts/analyze_bounty.py \
  results/all_competitive_ring_deepseek-chat_20260821_154427 \
  results/b1_disclosed results/b2_disclosed \
  results/all_competitive_b3_ring_deepseek-chat_20260821_151445 \
  results/b5_disclosed \
  results/all_competitive_b8_ring_deepseek-chat_20260821_151447 \
  results/all_competitive_b8u_ring_deepseek-chat_20260821_154429 \
  results/b0_r40_control \
  results/b8u_r40_none results/b8u_r40_itemized results/b8u_r40_attributed \
  2>/dev/null || true
