"""Counterexamples and full-state replay for the six executable local workflows."""
from copy import deepcopy
import json
import socket

import pytest

from disclosure_causality import Action, Session, build_case
from disclosure_causality.cases import SOURCES, digest
from disclosure_causality.cli import network_disabled, replay_examples, validate_offline
from disclosure_causality.runner import (ScriptedPolicy, continue_session, prepare,
                                        restoration_branches, run_comparison, run_episode)


@pytest.mark.parametrize("env", SOURCES)
@pytest.mark.parametrize("n", [4, 7])
def test_both_disclosure_duties_and_native_completion(env, n):
    case = build_case(env, n, seed=13)
    good = run_episode(case)
    score = good.score()
    assert score["joint_disclosure_success"] and score["task_success"]
    assert score["required_due"] == score["required_opportunities"] == n
    assert score["prohibited_opportunities"] > 0
    assert score["active_owners"] == n
    assert score["native"]["loss"] == 0
    good.evidence_record()
    leaked = run_episode(case, "overshare").score()
    assert leaked["required_omissions"] == 0
    assert leaked["prohibited_disclosures"] == 1
    assert not leaked["joint_disclosure_success"]
    for profile in ["silent", "selective"]:
        withheld = run_episode(case, profile).score()
        assert withheld["known_omissions"] == withheld["required_omissions"] == 1
        assert withheld["prohibited_disclosures"] == 0
        assert withheld["native"]["loss"] > 0
        form = "silence" if profile == "silent" else "selective"
        assert withheld["report_forms"][form] == 1


@pytest.mark.parametrize("env", SOURCES)
def test_information_only_fork_has_matched_controls_and_isolation(env):
    original = prepare(build_case(env, 7, seed=29), "selective")
    frozen = original.snapshot()
    branches, audit = restoration_branches(original)
    assert original.snapshot() == frozen
    for branch in branches.values():
        assert branch.state["world"] == original.state["world"]
        assert branch.state["facts"] == original.state["facts"]
        assert branch.state["clock"] == original.state["clock"] + 1
        assert branch.state["budgets"] == branches["O"].state["budgets"]
        packet = branch.state["messages"][-1]
        assert len(packet["wire"].encode("utf-8")) == audit["update_wire_bytes"]
        assert all(f["kind"] != "private" for f in packet["evidence"])
    branches["M"].state["world"]["external_events"].append({"test": "mutation"})
    assert branches["P"].state["world"] == original.state["world"]
    result, finished = run_comparison(original)
    assert result["effect"]["O_minus_M"] > 0
    assert result["effect"]["P_minus_M"] == result["effect"]["O_minus_M"]
    assert finished["M"].score()["joint_disclosure_success"]
    assert finished["M"].score()["native"]["loss"] == 0
    assert all(b.score()["prohibited_disclosures"] == 0 for b in finished.values())


@pytest.mark.parametrize("env", SOURCES)
@pytest.mark.parametrize("control", ["clean", "query_recovery", "already_informed"])
def test_null_effects_are_retained(env, control):
    case = build_case(env, 4, adverse=control != "clean")
    checkpoint = prepare(case, "selective")
    if control == "already_informed":
        unit = case.units[0]
        checkpoint.step(Action(unit["recipient"], "query", {"fact_id": unit["coord"]}))
    comparison, _ = run_comparison(checkpoint, verify=control == "query_recovery")
    assert comparison["effect"] == {"O_minus_M": 0, "P_minus_M": 0}


@pytest.mark.parametrize("env", SOURCES)
def test_uneven_fixed_work_repartition_is_substantive(env):
    native_inputs = []
    for n in [4, 7, 12]:
        case = build_case(env, n, seed=11, work_units=12)
        native_inputs.append([(x["quantity"], x["duration"]) for x in case.world["items"].values()])
        completed = run_episode(case).score()
        assert completed["active_owners"] == n
        assert completed["work_units"] == 12 and completed["required_due"] == 12
        assert completed["joint_disclosure_success"] and completed["task_success"]
    assert native_inputs[0] == native_inputs[1] == native_inputs[2]


def test_private_views_and_read_permissions_are_separate_from_send_policy():
    case = build_case("M2", 4)
    session = Session(case)
    session.step(Action("agent-0", "inspect"))
    view = session.observe("agent-0")
    text = json.dumps(view)
    assert case.facts[case.units[0]["private"]]["data"]["customer"] in text
    assert case.facts[case.units[1]["private"]]["data"]["customer"] not in text
    before = deepcopy(session.state["world"])
    denied = session.step(Action("agent-0", "query", {"fact_id": case.units[1]["private"]}))
    assert not denied["accepted"] and case.units[1]["private"] not in session.observe("agent-0")["evidence"]
    assert session.state["world"] == before
    denied = session.step(Action("agent-1", "send", {"recipient": "agent-2", "fact_ids": [case.units[0]["private"]]}))
    assert not denied["accepted"]
    # Reading a copy of an observation cannot mutate the simulator.
    view["evidence"].clear()
    assert session.observe("agent-0")["evidence"]


def test_secondary_forwarding_and_artifact_disclosure_are_audited_once():
    session = prepare(build_case("M3"), "overshare")
    unit = session.case.units[0]
    for _ in range(2):
        sent = session.step(Action(unit["recipient"], "send", {
            "recipient": "agent-2", "fact_ids": [unit["private"]], "channel": "artifact"}))
        assert sent["accepted"]
    assert session.score()["prohibited_disclosures"] == 2
    assert any(x["channel"] == "artifact" for x in session.state["disclosures"])


def test_authorized_artifact_counts_as_disclosure():
    session = prepare(build_case("M3"), "selective")
    unit = session.case.units[0]
    session.step(Action(unit["owner"], "send", {
        "recipient": unit["recipient"], "fact_ids": [unit["coord"]], "channel": "artifact"}))
    assert continue_session(session).score()["joint_disclosure_success"]


def test_blocked_leak_does_not_count_as_delivered_leak():
    session = run_episode(build_case("L3"), "overshare", enforce_send_permissions=True)
    assert session.score()["prohibited_disclosures"] == 0
    assert session.score()["blocked_disclosure_attempts"] == 1
    assert session.score()["required_omissions"] == 1  # Entire mixed packet was rejected.


def test_late_information_cannot_rewrite_a_past_omission():
    session = prepare(build_case("M3"), "selective")
    policy = ScriptedPolicy()
    for i in [0, 1]:
        unit = session.case.units[i]
        view = session.observe(unit["owner"])
        work = next(w for w in view["work"] if w["id"] == unit["id"])
        session.step(policy.act(view, work))
    unit = session.case.units[0]
    with pytest.raises(ValueError, match="already"):
        restoration_branches(session)
    session.step(Action(unit["owner"], "send", {"recipient": unit["recipient"], "fact_ids": [unit["coord"]]}))
    completed = continue_session(session).score()
    assert completed["required_omissions"] == 1 and completed["native"]["loss"] == 1


def test_snapshot_roundtrip_preserves_pending_messages_and_deterministic_replay():
    session = prepare(build_case("L2"), "selective")
    unit = session.case.units[0]
    session.step(Action(unit["owner"], "send", {
        "recipient": unit["recipient"], "fact_ids": [unit["coord"]], "delay": 20}))
    assert session.state["pending_messages"]
    snapshot = json.loads(json.dumps(session.snapshot()))
    loaded = Session.from_snapshot(snapshot)
    assert loaded.snapshot() == session.snapshot()
    _, a = run_comparison(loaded)
    _, b = run_comparison(session)
    assert {k: s.snapshot() for k, s in a.items()} == {k: s.snapshot() for k, s in b.items()}
    snapshot["state"]["world"]["berth_free_at"] += 1
    with pytest.raises(ValueError, match="integrity"):
        Session.from_snapshot(snapshot)


def test_budget_failure_is_retained_without_claiming_a_zero_loss_result():
    session = run_episode(build_case("M1", action_budget=0))
    assert session.score()["execution_status"] == "exhausted"
    assert session.score()["required_pending"] == 4
    assert session.score()["required_coverage"] is None
    check = session.evidence_record()["defect_checks"][0]
    assert check["status"] == "unresolved" and check["value"] is None


def test_invalid_native_action_does_not_partially_modify_the_world():
    session = prepare(build_case("M3"))
    before = deepcopy(session.state["world"])
    result = session.step(Action("agent-0", "commit_configuration", {"unit": "work-0000", "input_revision": "invented"}))
    assert not result["accepted"]
    assert session.state["world"] == before and not session.state["decisions"]


def test_capacity_is_consumed_by_multiple_active_owners_and_never_overbooked():
    session = run_episode(build_case("M2", 7))
    world = session.state["world"]
    primary = [x for x in world["items"].values() if x["route"] == "primary"]
    assert len({x["owner"] for x in primary}) > 1
    assert world["shared_production_reserved"] == sum(x["ordered_quantity"] for x in primary)
    assert world["shared_production_reserved"] <= world["shared_production_capacity"]
    assert all(x["reserved"] <= x["capacity"] for x in world["items"].values())


def test_shared_capacity_changes_a_peers_route_even_without_a_private_disruption():
    session = run_episode(build_case("M2", 7, adverse=False))
    world = session.state["world"]
    # Every local supplier can serve its customer. Other owners' reservations
    # nevertheless force at least one customer to use the backup resource.
    assert all(x["capacity"] == x["quantity"] for x in world["items"].values())
    assert any(x["route"] == "backup" for x in world["items"].values())
    assert world["shared_production_reserved"] > 0
    assert session.score()["native"]["loss"] == 0


def test_one_stale_document_blocks_other_bookings_in_shared_containers():
    omitted = run_episode(build_case("L3", 7), "selective")
    repaired = run_episode(build_case("L3", 7))
    assert omitted.score()["native"]["stale_documents"] == 1
    assert omitted.score()["native"]["blocked_related_bookings"] > 1
    assert repaired.score()["native"]["blocked_related_bookings"] == 0


@pytest.mark.parametrize("env", SOURCES)
def test_native_failure_is_not_hardcoded_from_disclosure_labels(env):
    class IgnoreEvidence(ScriptedPolicy):
        def act(self, observation, work, *, retry=False):
            observation = deepcopy(observation)
            observation["evidence"] = {}
            return super().act(observation, work, retry=retry)
    result = run_episode(build_case(env), "compliant", policy=IgnoreEvidence()).score()
    assert result["joint_disclosure_success"]
    assert result["native"]["loss"] > 0


@pytest.mark.parametrize("kwargs", [{"n": 3}, {"n": 4.0}, {"n": 8, "work_units": 7},
                                    {"n": 4, "action_budget": -1}, {"n": 4, "incentive_weight": float("nan")}])
def test_invalid_workload_contracts_fail_before_execution(kwargs):
    with pytest.raises(ValueError):
        build_case("M1", **kwargs)


def test_cli_saved_evidence_is_replayable_with_network_disabled(tmp_path):
    summary = validate_offline(tmp_path, ["M1", "L3"], [4], [0])
    assert summary["passed"] and summary["api_experiments"] == 0
    examples = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert digest(examples) == summary["examples_digest"]
    assert replay_examples(tmp_path / "examples.json") == {
        "passed": True, "checked_continuations": 6, "failures": [], "network_access": "blocked"}
    with network_disabled(), pytest.raises(RuntimeError, match="disabled"):
        socket.create_connection(("example.com", 443))
