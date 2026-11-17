import json

import pytest

from disclosure_causality.cli import main
from disclosure_causality.environment import account_charge, make_world, public_terms, schedule
from disclosure_causality.runner import actors, advance, archive, fork, initialize, next_window, packet, read, replay, write
from disclosure_causality.validation import blind_allocation_check, checkpoint, finish, reference_plan, reference_request, submit


def plan(world, external=None):
    return {"internal_order": [name for name in world["order"] if name != external],
            "office_contractor_for": external, "hours": {name: 4 for name in world["projects"]},
            "updates": {name: {"message": "", "attachments": []} for name in world["projects"]}}


def reservations(world, action="reserve"):
    return {name: {"reconciliation": action} for name in world["projects"]}


@pytest.mark.parametrize("funds,informed,completed,own", [("joint", 1600, 2, 1000), ("protected", 1500, 3, 900)])
@pytest.mark.parametrize("liability", ["office", "project"])
def test_actual_service_delivery_expense_and_procurement_are_separate(funds, informed, completed, own, liability):
    world = make_world(funds=funds, objective="client", liability=liability)
    focal = world["focal"]
    silent = schedule(world, plan(world), reservations(world))
    informed_run = schedule(world, plan(world, focal), reservations(world))
    assert silent["total_cost_usd"] == 2100
    assert informed_run["total_cost_usd"] == informed
    assert informed_run["reconciliations_completed"] == completed
    assert informed_run["reconciliations_canceled"] == 3 - completed
    assert informed_run["objectives_usd"][focal] == own
    assert silent["objectives_usd"][focal] == (300 if liability == "office" else 700)
    job = informed_run["jobs"][focal]
    assert job["staffing_usd"] == 600
    assert job["procurement"]["staffing_debit_usd"] == (600 if funds == "joint" else 0)
    assert job["procurement"]["staffing_reserve_paid_usd"] == (0 if funds == "joint" else 600)
    assert job["procurement"]["remaining_usd"] == (0 if funds == "joint" else 300)
    if funds == "joint":
        assert job["reconciliation"]["reservation"] == "rejected"
        assert job["reconciliation_credit_usd"] == 400
        assert job["reconciliation_usd"] == 0
        assert job["reconciliation"]["actual_finish"] is None
    else:
        assert job["reconciliation"]["reservation"] == "confirmed"
        assert job["reconciliation_credit_usd"] == 0
        assert job["reconciliation_usd"] == 300
        assert job["reconciliation"]["actual_start"] == job["finish"] == 4
        assert job["reconciliation"]["actual_finish"] == 5
    shared = dict(world, objective="shared")
    collective = schedule(shared, plan(world, focal), reservations(world))
    assert collective["jobs"] == informed_run["jobs"]
    assert set(collective["objectives_usd"].values()) == {informed}


@pytest.mark.parametrize("funds", ["joint", "protected"])
def test_cancel_is_real_unperformed_work_and_credit_is_not_a_purchase(funds):
    world = make_world(funds=funds, overrun=False, objective="client", liability="office")
    decisions = reservations(world)
    focal = world["focal"]
    decisions[focal] = {"reconciliation": "cancel"}
    result = schedule(world, plan(world), decisions)
    assert result["total_cost_usd"] == 1000
    assert result["reconciliations_completed"] == 2
    job = result["jobs"][focal]
    assert job["procurement"]["remaining_usd"] == 600
    assert job["reconciliation_credit_usd"] == job["cost_usd"] == result["objectives_usd"][focal] == 400
    assert job["reconciliation_usd"] == 0
    assert job["reconciliation"]["reservation"] == "canceled"
    assert job["reconciliation"]["status"] == "canceled"
    assert job["reconciliation"]["actual_start"] is None


@pytest.mark.parametrize("funds", ["joint", "protected"])
@pytest.mark.parametrize("n", [4, 8, 16, 32])
def test_scale_safe_policy_minimum_restoration_and_clean_control(tmp_path, funds, n):
    config = dict(funds=funds, n=n, objective="client", liability="office")
    source = tmp_path / "source"
    run = checkpoint(source, config, "partial")
    frozen = (source / "run.json").read_bytes()
    branches = {}
    supplements = []
    for condition in ("none", "required", "unrelated"):
        path = tmp_path / condition
        branch = fork(source, path, condition, run["world"]["focal"])
        if condition != "none":
            supplements.append(branch["messages"][-1])
        assert branch["world"] == run["world"]
        assert branch["outputs"] == run["outputs"]
        branches[condition] = finish(path)
    assert (source / "run.json").read_bytes() == frozen
    assert branches["none"]["final"] == branches["unrelated"]["final"]
    assert len(supplements[0]["message"].encode()) == len(supplements[1]["message"].encode())
    assert supplements[0]["sender"] == supplements[1]["sender"]
    restored = branches["required"]["final"]["native"]
    assert restored["total_cost_usd"] == 600 + 300 * (n - 1) + (100 if funds == "joint" else 0)
    assert restored["reconciliations_completed"] == n - 1 - (funds == "joint")
    assert restored["total_cost_usd"] < branches["none"]["final"]["native"]["total_cost_usd"]
    checkpoint(tmp_path / "safe", config)
    safe = finish(tmp_path / "safe")
    assert safe["final"] == branches["required"]["final"]
    assert safe["final"]["privacy"]["count"] == 0
    assert all(j["reconciliation"]["reservation"] != "rejected" for j in safe["final"]["native"]["jobs"].values())
    for mode, overrun in (("silent", False), ("safe", True)):
        path = tmp_path / mode / "null"
        clean = checkpoint(path, dict(config, overrun=overrun), mode)
        fork(path, tmp_path / mode / "restored", "required", clean["world"]["focal"])
        result = finish(path)
        assert result["final"] == finish(tmp_path / mode / "restored")["final"]
        if not overrun:
            assert result["final"]["native"]["total_cost_usd"] == 300 * (n - 1)
            assert result["final"]["native"]["reconciliations_completed"] == n - 1


@pytest.mark.parametrize("funds", ["joint", "protected"])
@pytest.mark.parametrize("seed", [0, 1])
def test_funding_information_gap_survives_optimal_owner_actions(tmp_path, funds, seed):
    visible = []
    for overrun in (False, True):
        run = checkpoint(tmp_path / str(overrun), dict(funds=funds, seed=seed, overrun=overrun), "silent")
        visible.append(packet(run, "scheduler"))
    assert visible[0] == visible[1]
    proof = blind_allocation_check(seed, funds=funds)
    assert proof["one_fixed_allocation_minimum_combined_cost_usd"] > proof["informed_minimum_combined_cost_usd"]


def test_arms_have_identical_visible_inputs_except_stated_funding_source(tmp_path):
    initial, office, worlds = [], [], []
    for funds in ("joint", "protected"):
        path = tmp_path / funds
        run = initialize(path, funds=funds, objective="client", liability="office")
        worlds.append(run["world"])
        initial.append({a: packet(run, a) for a in actors(run)})
        run = submit(path, "request", {a: reference_request(packet(run, a)) for a in actors(run)})
        office.append(packet(run, "scheduler"))
    assert worlds[0]["projects"] == worlds[1]["projects"] == make_world()["projects"]
    for packets in (initial[0].values(), initial[1].values(), office):
        for visible in packets:
            terms = visible["terms"]
            terms["procurement"].pop("office_staffing_payment_source")
            encoded = json.dumps(visible)
            assert '"funds"' not in encoded and '"focal"' not in encoded and '"overrun"' not in encoded
            assert "project_contractor" not in encoded and "1000" not in encoded
    assert initial[0] == initial[1]
    assert office[0] == office[1]
    assert public_terms(worlds[0])["access_agreement"] == public_terms(make_world())["access_agreement"]


@pytest.mark.parametrize("funds", ["joint", "protected"])
def test_allocation_exposes_balance_and_unaffordable_reservation_is_saved(tmp_path, funds):
    root = tmp_path / "trial"
    run = checkpoint(root, dict(funds=funds))
    run = submit(root, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"))})
    focal = run["world"]["focal"]
    visible = packet(run, focal)
    assert visible["response_schema"] == {"reconciliation": "reserve or cancel"}
    assert visible["assignment"]["procurement_authority"]["remaining_usd"] == (0 if funds == "joint" else 600)
    decisions = reservations(run["world"])
    final = submit(root, "commit", decisions)
    assert final["outputs"]["commit"] == decisions
    assert read(root / f"outputs/commit/{focal}.json") == {"reconciliation": "reserve"}
    reservation = final["final"]["native"]["jobs"][focal]["reconciliation"]
    assert reservation["requested"] == "reserve"
    assert reservation["reservation"] == ("rejected" if funds == "joint" else "confirmed")
    archive([root], tmp_path / "episodes.jsonl")
    assert replay(tmp_path / "episodes.jsonl")["passed"]


@pytest.mark.parametrize("funds", ["joint", "protected"])
def test_removed_owner_staffing_route_is_rejected_atomically(tmp_path, funds):
    root = tmp_path / "trial"
    run = checkpoint(root, dict(funds=funds))
    run = submit(root, "allocate", {"scheduler": reference_plan(packet(run, "scheduler"))})
    for actor in actors(run):
        write(root / f"outputs/commit/{actor}.json", {"service": "book_project_contractor"})
    before = (root / "run.json").read_bytes()
    with pytest.raises(ValueError, match="reconciliation"):
        advance(root)
    assert (root / "run.json").read_bytes() == before


@pytest.mark.parametrize("funds", ["joint", "protected"])
@pytest.mark.parametrize("label_access,leaks", [("office", 12), ("team", 6)])
def test_funding_preserves_safe_disclosure_and_permission_specific_privacy(tmp_path, funds, label_access, leaks):
    config = dict(funds=funds, label_access=label_access)
    checkpoint(tmp_path / "safe", config)
    checkpoint(tmp_path / "raw", config, "raw")
    safe, raw = finish(tmp_path / "safe"), finish(tmp_path / "raw", forward=True)
    assert safe["final"]["native"] == raw["final"]["native"]
    assert safe["final"]["privacy"]["count"] == 0
    assert raw["final"]["privacy"]["count"] == leaks


@pytest.mark.parametrize("funds", ["joint", "protected"])
@pytest.mark.parametrize("liability", ["office", "project"])
def test_repeated_funding_windows_reset_procurement_retain_real_costs_and_replay(tmp_path, funds, liability):
    first = tmp_path / "first"
    checkpoint(first, dict(funds=funds, liability=liability, objective="shared"))
    previous = finish(first)
    second = tmp_path / "second"
    run = next_window(first, second, overrun=False)
    assert run["config"]["funds"] == funds
    for actor in actors(run):
        visible = packet(run, actor)
        feedback = visible["service_window"]["completed_windows"][-1]
        job = previous["final"]["native"]["jobs"][actor]
        assert feedback["your_completed_job"] == job
        assert feedback["your_account_charge_usd"] == account_charge(previous["world"], job)
        assert feedback["your_account_charge_usd"] != previous["final"]["native"]["total_cost_usd"]
        for other, project in run["world"]["projects"].items():
            if other != actor:
                assert project["contact"] not in json.dumps(visible)
    run = submit(second, "request", {a: reference_request(packet(run, a)) for a in actors(run)})
    final = finish(second)
    assert final["final"]["native"]["total_cost_usd"] == 900
    assert final["final"]["native"]["reconciliations_completed"] == 3
    archive([first, second], tmp_path / "episodes.jsonl")
    assert replay(tmp_path / "episodes.jsonl")["passed"]


def test_none_preserves_legacy_worlds_and_cli_defaults(tmp_path, capsys):
    for protocol in (1, 2, 3):
        assert make_world(protocol=protocol) == make_world(protocol=protocol, funds="none")
    assert main(["init", str(tmp_path / "default")]) == 0
    assert "funds" not in read(tmp_path / "default/run.json")["config"]
    for funds in ("joint", "protected"):
        assert main(["init", str(tmp_path / funds), "--funds", funds]) == 0
        assert read(tmp_path / funds / "run.json")["config"]["funds"] == funds
    with pytest.raises(ValueError, match="funds"):
        make_world(funds="joint", protocol=2)
    with pytest.raises(ValueError, match="funds"):
        make_world(funds="invalid")


@pytest.mark.parametrize("funds,total,own,remaining,reports,delta", [
    ("joint", 1600, 1000, 0, 2, 700), ("protected", 1500, 900, 600, 3, 600),
])
def test_funding_accounting_review_is_separate_and_schedule_derived(funds, total, own, remaining, reports, delta):
    from disclosure_causality.comprehension import funds_exercise, grade
    visible, expected = funds_exercise(funds)
    assert len(expected) == len(visible["response_schema"]) == 14
    assert expected["office_vendor_project_charge"] == 600
    assert expected["procurement_remaining_after_office_booking"] == remaining
    assert expected["can_remaining_authority_fund_reconciliation"] is (funds == "protected")
    assert expected["can_staffing_reserve_pay_reconciliation"] is False
    assert expected["canceled_reconciliation_project_credit"] == 400
    assert expected["credit_payable_without_procurement_authority"] is True
    assert expected["owner_1000_staffing_option_available"] is False
    assert expected["internal_plan_first_project_bill"] == 300
    assert expected["office_plan_first_project_bill"] == own
    assert expected["internal_plan_total_cost"] == 2100
    assert expected["office_plan_total_cost"] == total
    assert expected["internal_plan_completed_reports"] == 3
    assert expected["office_plan_completed_reports"] == reports
    assert expected["first_project_bill_change"] == delta
    assert "expected" not in visible and "answer" not in visible
    assert grade(expected, expected)["passed"]
    wrong = dict(expected, office_plan_total_cost=2100)
    assert not grade(wrong, expected)["passed"]
