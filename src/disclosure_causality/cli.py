"""Reproducible offline validation and replay. No model clients or network calls."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import socket

from .cases import SOURCES, build_case, digest
from .engine import Action, Session
from .runner import PROFILES, prepare, run_comparison, run_episode


@contextmanager
def network_disabled():
    original = socket.socket.connect, socket.socket.connect_ex, socket.create_connection
    def denied(*args, **kwargs):
        raise RuntimeError("Network access is disabled during offline validation")
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    try:
        yield
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.create_connection = original


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_offline(output: Path, environments: list[str], sizes: list[int], seeds: list[int],
                     *, work_units: int | None = None) -> dict:
    rows, failures, examples, controls = [], [], [], []
    def check(condition: bool, name: str, context: dict):
        if not condition:
            failures.append({"check": name, **context})
    with network_disabled():
        for env in environments:
            for n in sizes:
                for seed in seeds:
                    case = build_case(env, n, seed, work_units=work_units)
                    context = {"environment": env, "n": n, "seed": seed}
                    sessions = {p: run_episode(case, p) for p in PROFILES}
                    scores = {p: s.score() for p, s in sessions.items()}
                    for session in sessions.values():
                        session.evidence_record()
                    check(scores["compliant"]["joint_disclosure_success"] and scores["compliant"]["task_success"],
                          "compliant_path", context)
                    check(scores["overshare"]["prohibited_disclosures"] > 0 and
                          scores["overshare"]["required_omissions"] == 0, "privacy_counterexample", context)
                    for p in ("silent", "selective"):
                        check(scores[p]["known_omissions"] > 0 and scores[p]["prohibited_disclosures"] == 0,
                              f"{p}_counterexample", context)
                    check(all(x["active_owners"] == n for x in scores.values()), "all_owners_execute", context)
                    checkpoint = prepare(case, "selective")
                    comparison, branches = run_comparison(checkpoint)
                    effect = comparison["effect"]
                    check(effect is not None and effect["P_minus_M"] > 0 and
                          effect["O_minus_M"] == effect["P_minus_M"], "information_only_positive_control", context)
                    check(all(x["prohibited_disclosures"] == 0 for x in comparison["scores"].values()),
                          "restoration_preserves_confidentiality", context)
                    rows.append({**context, "work_units": len(case.units), "case_hash": case.fingerprint,
                                 "profiles": scores, "restoration": comparison})
                    if n == sizes[0] and seed == seeds[0]:
                        examples.append({"environment": env, "checkpoint": checkpoint.snapshot(),
                                         "expected_final_hashes": {a: s.snapshot()["snapshot_hash"] for a, s in branches.items()},
                                         "evidence": {a: s.evidence_record() for a, s in branches.items()},
                                         "privacy_evidence": sessions["overshare"].evidence_record()})
            # These are null controls, not cases selected for a positive effect.
            for control in ("clean", "query_recovery", "already_informed"):
                case = build_case(env, sizes[0], seeds[0], work_units=work_units, adverse=control != "clean")
                checkpoint = prepare(case, "selective")
                if control == "already_informed":
                    first = case.units[0]
                    checkpoint.step(Action(first["recipient"], "query", {"fact_id": first["coord"]}))
                result, _ = run_comparison(checkpoint, verify=control == "query_recovery")
                check(result["effect"] == {"O_minus_M": 0, "P_minus_M": 0}, control, {"environment": env})
                controls.append({"environment": env, "control": control, "result": result})
    summary = {"schema_version": 1, "kind": "offline_scripted_validation",
               "scope": "synthetic local simulators; no LLM results or industry-conformance claim",
               "network_access": "blocked", "api_experiments": 0,
               "environments": environments, "sizes": sizes, "seeds": seeds,
               "matrix_cases": len(rows), "main_episodes": len(rows) * (len(PROFILES) + 3),
               "null_control_episodes": len(controls) * 3,
               "passed": not failures, "failures": failures,
               "rows": rows, "null_controls": controls}
    example_file = {"schema_version": 1, "kind": "synthetic_replay_evidence", "examples": examples}
    write_json(output / "examples.json", example_file)
    summary["examples_digest"] = digest(example_file)
    write_json(output / "summary.json", summary)
    return summary


def replay_examples(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    failures, checked = [], 0
    with network_disabled():
        for example in data["examples"]:
            checkpoint = Session.from_snapshot(example["checkpoint"])
            _, branches = run_comparison(checkpoint)
            for arm, session in branches.items():
                checked += 1
                if session.snapshot()["snapshot_hash"] != example["expected_final_hashes"][arm]:
                    failures.append({"environment": example["environment"], "arm": arm})
    return {"passed": not failures, "checked_continuations": checked, "failures": failures,
            "network_access": "blocked"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("offline", help="execute all six environments using scripted control policies")
    run.add_argument("--environments", nargs="+", choices=list(SOURCES), default=list(SOURCES))
    run.add_argument("--sizes", nargs="+", type=int, default=[4, 7, 8, 16, 32])
    run.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    run.add_argument("--work-units", type=int)
    run.add_argument("--output", type=Path, default=Path("output/offline"))
    replay = sub.add_parser("replay", help="replay saved checkpoints and verify final state hashes")
    replay.add_argument("examples", type=Path)
    args = parser.parse_args(argv)
    if args.command == "offline":
        summary = validate_offline(args.output, args.environments, args.sizes, args.seeds,
                                   work_units=args.work_units)
        print(json.dumps({k: summary[k] for k in ["passed", "matrix_cases", "main_episodes",
                                                  "null_control_episodes", "api_experiments", "failures"]}))
    else:
        summary = replay_examples(args.examples)
        print(json.dumps(summary))
    return 0 if summary["passed"] else 1
