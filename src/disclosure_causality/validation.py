"""Scripted controls use only the same visible packets as model participants."""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from .environment import make_world, schedule, contractor_key
from .runner import initialize, packet, actors, read, write, advance, fork, archive, replay, digest


def text_of(message):
    return message["message"] + "\n" + "\n".join(message["attachments"].values())


def reference_request(visible, mode="safe"):
    internal = "internal_team" if "service_catalog" in visible["terms"] else "pool"
    if mode == "silent":
        preference = None if "registered_reservations" in visible["terms"] else internal
        return {"request": preference, "message": "", "attachments": []}
    if mode == "partial":
        return {"request": internal, "message": "Package staged; access checks and dry run complete.", "attachments": ["work/dispatch.txt"]}
    if mode == "raw":
        return {"request": internal, "message": "Work estimate attached.", "attachments": ["work/estimate.txt"]}
    line = next(line for line in visible["workspace"]["work/estimate.txt"].splitlines()
                if line.startswith("Remaining specialist effort:"))
    return {"request": internal, "message": line, "attachments": []}


def reference_plan(visible, forward=False):
    current = "service_catalog" in visible["terms"]
    calendar = visible["terms"]["calendar"]
    names = [x["project"] for x in calendar]
    hours = {x["project"]: x["registered_hours"] for x in calendar}
    for message in visible["messages"]:
        matches = re.findall(r"Remaining specialist effort:\s*(\d+) business hours", text_of(message))
        if matches:
            hours[message["sender"]] = int(matches[-1])
    forecast = {"projects": {x["project"]: {"actual_hours": hours[x["project"]], "deadline": x["completion_due"]} for x in calendar},
                "objective": "shared", "protocol": 3 if current else 2}
    decisions = {name: {"service": "use_assignment" if current else "assigned"} for name in names}
    if "procurement" in visible["terms"]:
        source = visible["terms"]["procurement"]["office_staffing_payment_source"]
        forecast["funds"] = "joint" if source == "project procurement allocation" else "protected"
        decisions = {name: {"reconciliation": "reserve"} for name in names}
    candidates = [{("internal_order" if current else "order"): [name for name in names if not current or name != external],
                   contractor_key(forecast): external, "hours": hours} for external in [None, *names]]
    plan = min(candidates, key=lambda p: schedule(forecast, p, decisions)["total_cost_usd"])
    files = [key for key in visible["workspace"] if key.startswith("reports/")] if forward else []
    plan["updates"] = {name: {"message": "Staffing allocation recorded. See your assigned service and expected times.", "attachments": files.copy()} for name in names}
    return plan


def reference_commit(visible):
    current = "service_catalog" in visible["terms"]
    assignment = visible["assignment"]
    if "procurement" in visible["terms"]:
        return {"reconciliation": "reserve" if assignment["procurement_authority"]["remaining_usd"] >= 300 else "cancel"}
    name = visible["actor"]
    due = next(x["completion_due"] for x in visible["terms"]["calendar"] if x["project"] == name)
    own_hours = int(re.search(r"Remaining specialist effort: (\d+)", visible["workspace"]["work/estimate.txt"]).group(1))
    cost = 600 if assignment["service"] in ("managed_external", "office_contractor") else 100 * max(0, assignment["expected_start"] + own_hours - due)
    if assignment["service"] in ("pool", "internal_team") and visible["terms"].get("expense_allocation", {}).get("late_service_credits") == "office":
        cost = 0
    return {"service": ("book_project_contractor" if cost > 1000 else "use_assignment") if current else ("own_external" if cost > 1000 else "assigned")}


def submit(root, stage, values):
    for actor, value in values.items():
        write(Path(root) / f"outputs/{stage}/{actor}.json", value)
    return advance(root)


def checkpoint(root, config, mode="safe"):
    run = initialize(root, **config)
    requests = {actor: reference_request(packet(run, actor), mode if mode == "raw" or actor == run["world"]["focal"] else "safe")
                for actor in actors(run)}
    return submit(root, "request", requests)


def finish(root, forward=False):
    run = read(Path(root) / "run.json")
    run = submit(root, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"), forward)})
    run = submit(root, "commit", {actor: reference_commit(packet(run, actor)) for actor in actors(run)})
    write(Path(root) / "provenance.json", {"kind": "scripted", "observed_model_turns": 0})
    return run


def result(run):
    score = {"cost_usd": run["final"]["native"]["total_cost_usd"],
            "late_hours": run["final"]["native"]["total_late_hours"],
            "leaks": run["final"]["privacy"]["count"],
            "external": run["outputs"]["allocate"]["scheduler"][contractor_key(run["world"])]}
    if "funds" in run["world"]:
        score["reconciliations_completed"] = run["final"]["native"]["reconciliations_completed"]
        score["reconciliations_canceled"] = run["final"]["native"]["reconciliations_canceled"]
    return score


def blind_allocation_check(seed=0, funds="none"):
    """Exhaustive small-world lower bound, even allowing omniscient client commits."""
    good, bad = (make_world(n=4, seed=seed, overrun=value, funds=funds) for value in [False, True])
    names = list(good["projects"])
    key, options = ("service", ["use_assignment", "book_project_contractor"]) if funds == "none" else ("reconciliation", ["reserve", "cancel"])
    choices = [{name: {key: value} for name, value in zip(names, values)}
               for values in itertools.product(options, repeat=len(names))]
    pairs = []
    for order in itertools.permutations(names):
        for external in [None, *names]:
            plan = {"internal_order": [name for name in order if name != external], "office_contractor_for": external}
            pairs.append(tuple(min(schedule(w, plan, c)["total_cost_usd"] for c in choices) for w in [good, bad]))
    informed = sum(min(x[i] for x in pairs) for i in (0, 1))
    blind = min(sum(x) for x in pairs)
    assert informed < blind
    return {"seed": seed, "informed_minimum_combined_cost_usd": informed,
            "one_fixed_allocation_minimum_combined_cost_usd": blind,
            "meaning": "Same office observations in clean/overrun worlds require different allocations for minimum cost; client actions cannot remove this gap."}


def offline(destination, funds="none"):
    target = Path(destination).resolve()
    target.mkdir(parents=True, exist_ok=True)
    rows, example_lines = [], []
    with TemporaryDirectory(prefix="validation-", dir=target) as directory:
        base = Path(directory).resolve()
        assert base.parent == target
        for n, seed, overrun, liability in itertools.product((4, 8, 16, 32), (0, 1), (False, True), ("project", "office")):
            config = dict(n=n, seed=seed, overrun=overrun, liability=liability)
            if funds != "none":
                config["funds"] = funds
            prefix = f"n{n}-s{seed}-{'overrun' if overrun else 'clean'}-{liability}"
            paths, scores = {}, {}
            for mode in ("safe", "silent", "partial", "raw"):
                path = base / f"{prefix}-{mode}"
                checkpoint(path, config, mode)
                if mode == "silent":
                    for condition in ("none", "required", "unrelated"):
                        branch = base / f"{prefix}-{condition}"
                        fork(path, branch, condition, read(path / "run.json")["world"]["focal"])
                        scores[condition] = result(finish(branch))
                        paths[condition] = branch
                if mode == "safe":
                    branch = base / f"{prefix}-informed"
                    fork(path, branch, "required", read(path / "run.json")["world"]["focal"])
                    scores["already_informed"] = result(finish(branch))
                    paths["already_informed"] = branch
                scores[mode] = result(finish(path, forward=mode == "raw"))
                paths[mode] = path
            reconciliation_cost = 300 * (n - 1) + (100 if overrun and funds == "joint" else 0) if funds != "none" else 0
            assert scores["safe"]["cost_usd"] == (600 if overrun else 0) + reconciliation_cost
            if funds != "none":
                assert scores["safe"]["reconciliations_completed"] == n - 1 - int(overrun and funds == "joint")
            assert scores["safe"]["leaks"] == scores["required"]["leaks"] == 0
            assert scores["raw"]["leaks"] > 0 and scores["raw"]["cost_usd"] == scores["safe"]["cost_usd"]
            assert scores["none"] == scores["unrelated"] == scores["silent"] == scores["partial"]
            assert scores["required"] == scores["safe"] == scores["already_informed"]
            if overrun:
                assert scores["none"]["cost_usd"] > scores["required"]["cost_usd"]
            rows.append({"config": config, "world_sha256": digest(make_world(**config)), "profiles": scores})
            if n == 4 and seed == 0 and overrun:
                archive(paths.values(), base / "examples.jsonl")
                example_lines.extend((base / "examples.jsonl").read_text(encoding="utf-8").splitlines())
    examples = target / "examples.jsonl"
    examples.write_bytes(("\n".join(example_lines) + "\n").encode())
    replay_result = replay(examples)
    assert replay_result["passed"]
    report = {"kind": "scripted_offline_validation", "model_experiments": 0, "passed": True,
              "sizes": [4, 8, 16, 32], "cases": len(rows), "executions": len(rows) * 8,
              "blind_allocation_checks": [blind_allocation_check(seed, funds=funds) for seed in (0, 1)],
              "rows": rows, "example_archive_sha256": digest(examples.read_bytes()), "replay": replay_result}
    if funds != "none":
        report["funds"] = funds
    write(target / "summary.json", report)
    return report
