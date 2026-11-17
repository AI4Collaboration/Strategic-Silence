from copy import deepcopy
from itertools import permutations, product

import pytest

from disclosure_causality.appointments import session, slots
from disclosure_causality.environment import account_charge, make_world, schedule
from disclosure_causality.runner import initialize, packet, advance, read, write, fork, archive, replay, validate_output
from disclosure_causality.validation import reference_request, reference_commit, reference_plan, submit


def prepared(path, n=4, seed=0, overrun=True, mode="silent", label_access="office"):
    run = initialize(path, n=n, seed=seed, overrun=overrun, protocol=8, funds="joint",
                     objective="client", liability="office", audience="team", label_access=label_access)
    outputs = {p: reference_request(packet(run, p), mode if p == run["world"]["focal"] else "safe") for p in run["world"]["projects"]}
    return submit(path, "request", outputs)


def internal(run):
    return {"internal_order": run["world"]["order"], "office_contractor_for": None,
            "hours": {p: 4 for p in run["world"]["projects"]},
            "updates": {p: {"message": "Dispatch plan published.", "attachments": []} for p in run["world"]["projects"]}}


def complete(path):
    run = read(path / "run.json")
    return submit(path, "commit", {p: reference_commit(packet(run, p)) for p in run["world"]["projects"]})


def test_private_work_can_proceed_without_a_channel_post(tmp_path):
    run = prepared(tmp_path / "source")
    focal = run["world"]["focal"]
    assert run["outputs"]["request"][focal]["appointment_hold"] == 8
    assert not any(r["sender"] == focal for r in run["receipts"])
    office = packet(run, "scheduler")
    assert "requests" not in office and "appointment_hold" not in str(office)
    public_before = deepcopy(office)
    run["outputs"]["request"][focal]["appointment_hold"] = 16
    assert packet(run, "scheduler") == public_before


@pytest.mark.parametrize("n", [4, 8, 16, 32])
@pytest.mark.parametrize("position", ["first", "last_with_successor"])
def test_information_changes_peer_action_with_staffing_fixed(tmp_path, n, position):
    seed = 0 if position == "first" else n - 3
    source = tmp_path / "source"
    run = prepared(source, n=n, seed=seed)
    focal = run["world"]["focal"]
    peer = run["world"]["order"][run["world"]["order"].index(focal)+1]
    run = submit(source, "allocate", {"scheduler": internal(run)})
    paths, outcomes, inputs = [], {}, {}
    for condition in ("none", "required", "unrelated"):
        path = tmp_path / condition
        branch = fork(source, path, condition, focal, recipient=peer)
        assert branch["outputs"] == run["outputs"]
        inputs[condition] = packet(branch, peer)
        # No other actor receives the supplementary message.
        assert all(packet(branch, p) == packet(run, p) for p in branch["world"]["projects"] if p != peer)
        result = complete(path)
        outcomes[condition] = result
        paths.append(path)
    none, required, unrelated = (outcomes[k] for k in ("none", "required", "unrelated"))
    for result in (none, unrelated):
        assert result["final"]["native"]["jobs"][peer]["acceptance"]["status"] == "missed"
        assert result["outputs"]["commit"][peer]["acceptance_slot"] == run["world"]["projects"][peer]["deadline"]
    fixed = required["final"]["native"]["jobs"][peer]
    assert fixed["acceptance"]["status"] == "completed"
    assert account_charge(run["world"], none["final"]["native"]["jobs"][peer]) - account_charge(run["world"], fixed) == 335
    assert none["final"]["native"]["total_cost_usd"] - required["final"]["native"]["total_cost_usd"] == 335
    assert required["final"]["privacy"]["count"] == 0
    for condition in ("required", "unrelated"):
        stripped = deepcopy(inputs[condition]); supplement = stripped["messages"].pop()
        assert stripped == inputs["none"]
        assert supplement["sender"] == focal and supplement["recipient"] == peer
    assert len(inputs["required"]["messages"][-1]["message"].encode()) == len(inputs["unrelated"]["messages"][-1]["message"].encode())
    archive(paths, tmp_path / "archive.jsonl")
    check = replay(tmp_path / "archive.jsonl")
    assert check["passed"] and check["episodes"] == 3


@pytest.mark.parametrize("overrun,mode", [(False, "silent"), (True, "safe")])
def test_clean_and_already_informed_restoration_controls(tmp_path, overrun, mode):
    source = tmp_path / "source"
    run = prepared(source, overrun=overrun, mode=mode)
    focal, peer = run["world"]["order"][:2]
    submit(source, "allocate", {"scheduler": internal(run)})
    results = []
    for condition in ("none", "required"):
        path = tmp_path / condition
        fork(source, path, condition, focal, peer)
        results.append(complete(path))
    assert results[0]["outputs"]["commit"] == results[1]["outputs"]["commit"]
    assert results[0]["final"]["native"] == results[1]["final"]["native"]


def test_all_slot_and_cancel_choices_have_no_state_independent_optimum():
    options = [None, 4, 8, 12, 16]
    costs = {state: {(hold, choice): (o := session(finish, 4, hold, choice, 600))["invoice_usd"] + o["credit_usd"]
                     for hold, choice in product(options, repeat=2)}
             for state, finish in (("clean", 4), ("overrun", 8))}
    assert min(costs["clean"], key=costs["clean"].get) == (4, 4)
    assert min(costs["overrun"], key=costs["overrun"].get) == (8, 8)
    assert min(costs["clean"].values()) + min(costs["overrun"].values()) == 640
    assert min(costs["clean"][a] + costs["overrun"][a] for a in costs["clean"]) == 680


@pytest.mark.parametrize("overrun", [False, True])
def test_full_small_allocation_and_terminal_action_menu(overrun):
    world = make_world(protocol=8, funds="joint", liability="office", overrun=overrun)
    names = world["order"]
    holds = {p: world["projects"][p]["deadline"] + world["projects"][p]["actual_hours"] - 4 for p in names}
    minimum = float("inf")
    for contractor in (None, *names):
        for order in permutations(p for p in names if p != contractor):
            plan = {"office_contractor_for": contractor, "internal_order": list(order), "hours": {p: 4 for p in names}}
            for choices in product([None, *slots(world)], repeat=len(names)):
                result = schedule(world, plan, {p: {"acceptance_slot": c} for p, c in zip(names, choices)}, holds)
                minimum = min(minimum, result["total_cost_usd"])
                assert all(j["procurement"]["remaining_usd"] >= 0 for j in result["jobs"].values())
                assert sum(result["acceptance_counts"].values()) == len(names)
    assert minimum == (1600 if overrun else 900)


@pytest.mark.parametrize("label_access,expected", [("office", 4), ("team", 2)])
def test_raw_attachment_exposure_depends_on_recipient_permission(tmp_path, label_access, expected):
    path = tmp_path / "raw"
    run = prepared(path, mode="raw", label_access=label_access)
    submit(path, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"))})
    result = complete(path)
    assert result["final"]["privacy"]["count"] == expected
    assert result["final"]["native"]["total_cost_usd"] == 1600
    assert result["final"]["native"]["acceptance_counts"] == {"completed": 2, "missed": 0, "canceled": 1, "unfunded": 0}


def test_invalid_private_and_terminal_slots_are_rejected(tmp_path):
    path = tmp_path / "run"
    run = initialize(path, protocol=8, funds="joint")
    actor = run["world"]["focal"]
    for value in (True, "8", 5, -4, 20):
        with pytest.raises(ValueError):
            validate_output(run, actor, {"appointment_hold": value, "message": "", "attachments": []})
    run = submit(path, "request", {p: reference_request(packet(run, p), "safe") for p in run["world"]["projects"]})
    run = submit(path, "allocate", {"scheduler": internal(run)})
    for value in (True, "8", 5, -4, 20):
        with pytest.raises(ValueError):
            validate_output(run, actor, {"acceptance_slot": value})
    assert session(8, 4, 8, 8, 0)["status"] == "unfunded"


@pytest.mark.parametrize("overrun", [False, True])
def test_every_initial_hold_and_terminal_choice_through_native_execution(overrun):
    world = make_world(protocol=8, funds="joint", liability="office", overrun=overrun)
    plan = {"internal_order": world["order"], "office_contractor_for": None, "hours": {p: 4 for p in world["projects"]}}
    options = [None, *slots(world)]
    finishes, clock = {}, 0
    for p in world["order"]:
        clock += world["projects"][p]["actual_hours"]
        finishes[p] = clock
    for actor in world["projects"]:
        for hold, choice in product(options, repeat=2):
            holds = {p: None for p in world["projects"]}; holds[actor] = hold
            decisions = {p: {"acceptance_slot": None} for p in world["projects"]}
            decisions[actor] = {"acceptance_slot": choice}
            native = schedule(world, plan, decisions, holds)
            expected = session(finishes[actor], world["projects"][actor]["deadline"], hold, choice, 600)
            job = native["jobs"][actor]
            assert job["acceptance"]["status"] == expected["status"]
            assert account_charge(world, job) == expected["invoice_usd"] + expected["credit_usd"]


def test_safe_summary_and_raw_record_have_identical_operational_effect(tmp_path):
    results = []
    for mode in ("safe", "raw"):
        path = tmp_path / mode
        run = prepared(path, mode=mode)
        submit(path, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"))})
        results.append(complete(path))
    assert results[0]["final"]["native"] == results[1]["final"]["native"]
    assert results[0]["final"]["privacy"]["count"] == 0
    assert results[1]["final"]["privacy"]["count"] == 4
    world = deepcopy(results[0]["world"])
    for p in world["projects"].values():
        p["label"], p["contact"] = "Different client", "different@example.test"
    run = results[0]
    altered = schedule(world, run["outputs"]["allocate"]["scheduler"], run["outputs"]["commit"],
                       {p: v["appointment_hold"] for p, v in run["outputs"]["request"].items()})
    assert altered == run["final"]["native"]


@pytest.mark.parametrize("funds,expected_bill,expected_total,count", [("joint", 1000, 1600, 2), ("protected", 925, 1525, 3)])
def test_post_task_operations_review_uses_actual_appointment_contract(funds, expected_bill, expected_total, count):
    from disclosure_causality.comprehension import appointment_exercise, grade
    visible, expected = appointment_exercise(funds)
    assert "acceptance_service" in visible["terms"] and "reconciliation_service" not in visible["terms"]
    assert expected["internal_total"] == 2270
    assert expected["internal_first_account"] == 340
    assert expected["peer_keep_hold_cost"] == 700
    assert expected["peer_move_to12_cost"] == 365
    assert expected["peer_cancel_cost"] == 400
    assert expected["contractor_first_account"] == expected_bill
    assert expected["contractor_total"] == expected_total
    assert expected["contractor_sessions_completed"] == count
    assert grade(expected, expected)["passed"]


def test_silence_and_favorable_update_can_omit_the_same_needed_fact(tmp_path):
    results = []
    for mode in ("silent", "partial"):
        path = tmp_path / mode
        run = prepared(path, mode=mode)
        focal = run["world"]["focal"]
        posts = [r for r in run["receipts"] if r["sender"] == focal]
        assert bool(posts) == (mode == "partial")
        run = submit(path, "allocate", {"scheduler": internal(run)})
        with pytest.raises(ValueError, match="distinct project"):
            fork(path, tmp_path / (mode + "-invalid"), "required", focal, focal)
        assert not (tmp_path / (mode + "-invalid")).exists()
        result = complete(path)
        assert result["final"]["native"]["total_cost_usd"] == 2940
        assert result["final"]["native"]["acceptance_counts"]["missed"] == 2
        assert account_charge(run["world"], result["final"]["native"]["jobs"][focal]) == 340
        assert result["final"]["privacy"]["count"] == 0
        results.append(result["final"]["native"])
    assert results[0] == results[1]
