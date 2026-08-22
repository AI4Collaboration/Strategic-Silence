"""Compare strategic silence across environment geometries (point vs grid vs ring).

Answers: does distance change how silence works?
- Per variant: silence rates, messages per round, trade activity, silence by goal tier.
- Grid only: splits agent-rounds into "audience present" (someone in talking
  range -> silence is a choice) vs "alone" (silence is forced by distance),
  and reports chosen-silence rates by goal tier.

Usage:
  python scripts/analyze_silence_distance.py results/expA results/expB ...
  python scripts/analyze_silence_distance.py            # auto-scan results/
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from info_marketplace.results import compute_silence_market_stats  # noqa: E402


def load_trials(exp_dir: Path) -> list[dict]:
    trials = []
    for f in sorted(exp_dir.glob("trial_*.json")):
        with open(f) as fh:
            trials.append(json.load(fh))
    return trials


def goal_tier(goals: list[dict], agent: str) -> str | None:
    for g in goals:
        if g.get("agent") == agent:
            return g.get("tier")
    return None


def audience_breakdown(trials: list[dict]) -> dict:
    """Split silence by whether anyone was in talking range that round."""
    buckets = {
        "audience_present": defaultdict(lambda: {"silent": 0, "total": 0}),
        "alone": defaultdict(lambda: {"silent": 0, "total": 0}),
    }
    for trial in trials:
        goals = trial.get("goals", [])
        for round_data in trial.get("game_log", {}).get("rounds", []):
            for choice in round_data.get("communication_choices", []):
                size = choice.get("audience_size")
                if size is None:
                    continue
                bucket = buckets["audience_present"] if size > 0 else buckets["alone"]
                tier = goal_tier(goals, choice.get("agent", "")) or "UNKNOWN"
                for key in (tier, "ALL"):
                    bucket[key]["total"] += 1
                    if choice.get("fully_silent"):
                        bucket[key]["silent"] += 1
    return buckets


def deception_summary(trials: list[dict]) -> dict:
    counts: dict[str, int] = defaultdict(int)
    total = 0
    for trial in trials:
        for msg in trial.get("classification", {}).get("messages", []):
            counts[msg.get("label", "unknown")] += 1
            total += 1
    return {"total_messages": total, "labels": dict(counts)}


def pct(silent: int, total: int) -> str:
    return f"{100 * silent / total:5.1f}% ({silent}/{total})" if total else "  n/a"


def report(exp_dir: Path):
    trials = load_trials(exp_dir)
    if not trials:
        print(f"\n== {exp_dir.name}: no trials found ==")
        return
    variant = trials[0].get("env_variant", trials[0].get("game_log", {}).get("config", {}).get("env_variant", "ring"))
    condition = trials[0].get("condition", "?")

    stats = compute_silence_market_stats(trials)
    silence = stats["silence"]
    market = stats["market"]
    print(f"\n== {exp_dir.name} ==")
    print(f"   variant={variant}  condition={condition}  trials={len(trials)}")
    print(f"   fully silent:         {pct(silence['fully_silent'], silence['total_agent_rounds'])}")
    print(f"   partial silence rate: {100 * silence['partial_silence_rate']:5.1f}%")
    print(f"   whisper rate:         {100 * silence['whisper_rate']:5.1f}%")
    n_msgs = sum(len(r.get("messages", [])) for t in trials for r in t.get("game_log", {}).get("rounds", []))
    n_rounds = sum(len(t.get("game_log", {}).get("rounds", [])) for t in trials)
    print(f"   messages per round:   {n_msgs / n_rounds:.2f}" if n_rounds else "")
    print(f"   trades:               {market['total_trade_successes']}/{market['total_trade_actions']} succeeded")

    tier_stats = silence.get("silence_rate_by_tier") or {}
    if tier_stats:
        print("   silence by goal tier:")
        for tier, val in tier_stats.items():
            if isinstance(val, dict):
                print(f"     {tier:12s} {pct(val.get('silent', 0), val.get('total', 0))}")
            else:
                print(f"     {tier:12s} {100 * val:5.1f}%")

    dec = deception_summary(trials)
    if dec["total_messages"]:
        print(f"   message labels ({dec['total_messages']} classified): {dec['labels']}")

    buckets = audience_breakdown(trials)
    ap, al = buckets["audience_present"], buckets["alone"]
    print("   --- silence while ABLE to speak (audience in range) ---")
    print(f"   able-to-speak rounds:   {pct(ap['ALL']['total'], ap['ALL']['total'] + al['ALL']['total'])}")
    print(f"   SILENT despite audience: {pct(ap['ALL']['silent'], ap['ALL']['total'])}")
    if al["ALL"]["total"]:
        print(f"   silent while alone (no one to hear): {pct(al['ALL']['silent'], al['ALL']['total'])}")
    print("   by goal tier:  (able-to-speak exposure | silent when able)")
    for tier in ("ALIGNED", "ORTHOGONAL", "COMPETITIVE"):
        exposure = ap[tier]["total"] + al[tier]["total"]
        if exposure:
            print(f"     {tier:12s} able {pct(ap[tier]['total'], exposure)}  |  "
                  f"silent-when-able {pct(ap[tier]['silent'], ap[tier]['total'])}")


def main():
    args = sys.argv[1:]
    if args:
        dirs = [Path(a) for a in args]
    else:
        results = Path("results")
        dirs = sorted(d for d in results.iterdir() if d.is_dir()) if results.exists() else []
    if not dirs:
        print("No experiment directories found. Pass paths or run experiments first.")
        return
    for d in dirs:
        report(d)


if __name__ == "__main__":
    main()
