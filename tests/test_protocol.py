"""Offline checks of evidence metadata and branch isolation; no task simulator."""
from copy import deepcopy

import pytest

from disclosure_causality.protocol import restoration_inputs, validate_action_evidence


def restore(state, packets, token_count):
    return restoration_inputs(
        state, packets, token_count, source_actor="actor-0",
        recipient_actor_ids=["actor-1"],
    )


def frozen_state():
    return {"history": [{"role": "user", "content": "unchanged"}], "task": "fixture",
            "actions": ["inspect", "wait"], "tools": [{"name": "request_record"}],
            "source_access": ["public-index"], "budget": {"max_tool_steps": 20},
            "environment_state": {"committed_artifacts": []}, "participant_states": {f"actor-{i}": [] for i in range(4)},
            "message_queues": {f"actor-{i}": [] for i in range(4)},
            "pending_operations": [],
            "exogenous_state": {"event_tape": []},
            "work_product": {"revision": "frozen", "test_results": ["failed-required-check"]}}


def test_replay_preserves_every_nonpayload_field():
    state = frozen_state()
    original = deepcopy(state)
    branches = restore(state, {"M": "fact-a", "P": "fact-b", "F": "fact-a fact-c"}, len)
    assert set(branches) == {"O", "M", "P", "F"}
    for arm, branch in branches.items():
        assert "arm" not in branch
        update = branch.pop("evidence_update")
        assert branch == original
        if arm == "O":
            assert update["content"] == ""
    branches["M"]["history"][0]["content"] = "mutated"
    assert branches["P"]["history"] == original["history"]
    assert state == original


@pytest.mark.parametrize("packets", [
    {"M": "a", "P": "longer", "F": "a b"},
    {"M": "a", "P": "a", "F": "a b"},
    {"M": "", "P": "b", "F": "a b"},
    {"M": "a", "P": "b"},
])
def test_replay_rejects_unmatched_or_missing_evidence(packets):
    with pytest.raises(ValueError):
        restore(frozen_state(), packets, len)


def test_replay_requires_source_access_and_only_one_update():
    state = frozen_state()
    del state["source_access"]
    with pytest.raises(ValueError):
        restore(state, {"M": "a", "P": "b", "F": "a b"}, len)
    state = frozen_state()
    state["evidence_update"] = {}
    with pytest.raises(ValueError):
        restore(state, {"M": "a", "P": "b", "F": "a b"}, len)


def test_replay_freezes_nested_artifact_and_does_not_repair_it():
    state = frozen_state()
    branches = restore(state, {"M": "fact-a", "P": "fact-b", "F": "fact-a fact-c"}, len)
    for branch in branches.values():
        assert branch["work_product"] == state["work_product"]
    branches["M"]["work_product"]["test_results"].clear()
    assert branches["P"]["work_product"]["test_results"] == ["failed-required-check"]
    assert state["work_product"]["test_results"] == ["failed-required-check"]


def test_replay_requires_work_product():
    state = frozen_state()
    del state["work_product"]
    with pytest.raises(ValueError, match="work_product"):
        restore(state, {"M": "fact-a", "P": "fact-b", "F": "fact-a fact-c"}, len)


def test_native_world_and_participant_contexts_are_independent_across_branches():
    state = frozen_state()
    branches = restore(state, {"M": "fact-a", "P": "fact-b", "F": "fact-a fact-c"}, len)
    branches["M"]["environment_state"]["committed_artifacts"].append("artifact-A")
    branches["M"]["participant_states"]["actor-1"].append("new observation")
    assert branches["P"]["environment_state"]["committed_artifacts"] == []
    assert state["participant_states"]["actor-1"] == []


def action_record():
    # Metadata fixture only: this is not a native environment or empirical run.
    return {"outcome_basis": "environment_trace_and_state", "execution_status": "completed",
            "actor_ids": [f"actor-{i}" for i in range(4)],
            "decision_actor_ids": ["actor-1"],
            "initial_state_hash": "a" * 64, "final_state_hash": "b" * 64,
            "events": [{"event_id": "event-1", "actor": "actor-1", "tool": "commit_artifact",
                        "arguments": {"artifact": "fixture"}, "effect": "mutate", "status": "ok",
                        "result_reference": "fixture-receipt",
                        "before_state_hash": "a" * 64, "after_state_hash": "b" * 64}],
            "defect_checks": [{"name": "fixture-check", "oracle_reference": "fixture-oracle",
                              "status": "observed", "event_ids": ["event-1"],
                              "state_reference": "fixture-state", "value": 0, "unit": "units"}]}


def test_action_evidence_accepts_linked_native_receipt_metadata():
    validate_action_evidence(action_record())


@pytest.mark.parametrize("kind", ["text_only", "rejected_only", "broken_chain", "unknown_event", "missing_state"])
def test_action_evidence_rejects_unsupported_completion(kind):
    record = action_record()
    if kind == "text_only":
        record["outcome_basis"] = "final_answer"
    elif kind == "rejected_only":
        record["events"][0]["status"] = "rejected"
    elif kind == "broken_chain":
        record["events"][0]["before_state_hash"] = "c" * 64
    elif kind == "unknown_event":
        record["defect_checks"][0]["event_ids"] = ["unrecorded"]
    else:
        del record["defect_checks"][0]["state_reference"]
    with pytest.raises(ValueError):
        validate_action_evidence(record)


def test_failed_execution_is_retained_without_imputing_zero_defects():
    record = action_record()
    record["execution_status"] = "failed"
    record["events"][0]["status"] = "error"
    record["defect_checks"][0].update(status="unresolved", value=None)
    validate_action_evidence(record)
    record["defect_checks"][0]["value"] = 0
    with pytest.raises(ValueError, match="cannot be scored as zero"):
        validate_action_evidence(record)


@pytest.mark.parametrize("size", [4, 7, 8, 16, 32, 65])
def test_routed_metadata_has_no_fixed_actor_count_and_preserves_other_members(size):
    state = frozen_state()
    state["participant_states"] = {f"actor-{i}": [] for i in range(size)}
    state["message_queues"] = {f"actor-{i}": [] for i in range(size)}
    targets = ["actor-1", f"actor-{size - 1}"]
    branches = restoration_inputs(
        state, {"M": "fact-a", "P": "fact-b", "F": "fact-a fact-c"}, len,
        source_actor="actor-0", recipient_actor_ids=targets,
    )
    targets.clear()
    for branch in branches.values():
        assert branch["evidence_update"]["recipient_actor_ids"] == ["actor-1", f"actor-{size - 1}"]
        assert branch["evidence_update"]["channel"] == "ordinary_sender"
        assert branch["participant_states"] == state["participant_states"]
    branches["M"]["participant_states"][f"actor-{size - 1}"].append("received")
    branches["M"]["message_queues"]["actor-2"].append("forwarded")
    branches["M"]["pending_operations"].append("execute")
    assert branches["P"]["participant_states"] == state["participant_states"]
    assert branches["P"]["message_queues"] == state["message_queues"]
    assert branches["P"]["pending_operations"] == state["pending_operations"]


@pytest.mark.parametrize("overrides", [
    {"source_actor": "unknown"},
    {"recipient_actor_ids": ["unknown"]},
    {"recipient_actor_ids": []},
    {"recipient_actor_ids": ["actor-1", "actor-1"]},
    {"recipient_actor_ids": ["actor-0"]},
    {"channel": "broadcast_everywhere"},
])
def test_restoration_rejects_undefined_or_ambiguous_routes(overrides):
    route = {"source_actor": "actor-0", "recipient_actor_ids": ["actor-1"]}
    route.update(overrides)
    with pytest.raises(ValueError):
        restoration_inputs(frozen_state(), {"M": "a", "P": "b", "F": "a b"}, len, **route)


@pytest.mark.parametrize("field", ["message_queues", "pending_operations"])
def test_restoration_requires_pending_communication_and_execution_state(field):
    state = frozen_state()
    del state[field]
    with pytest.raises(ValueError, match=field):
        restore(state, {"M": "a", "P": "b", "F": "a b"}, len)


def test_authenticated_route_is_explicit_and_separate():
    state = frozen_state()
    state["participant_states"]["reference-service"] = []
    branches = restoration_inputs(
        state, {"M": "a", "P": "b", "F": "a b"}, len,
        source_actor="reference-service", recipient_actor_ids=["actor-1"],
        channel="authenticated_reference_update",
    )
    assert branches["M"]["evidence_update"]["source_actor"] == "reference-service"
    assert branches["M"]["evidence_update"]["channel"] == "authenticated_reference_update"


def test_nonfocal_or_environment_action_cannot_establish_decision_completion():
    for actor in ["actor-2", "environment", "unknown"]:
        record = action_record()
        record["events"][0]["actor"] = actor
        with pytest.raises(ValueError):
            validate_action_evidence(record)


@pytest.mark.parametrize("size", [4, 7, 16, 32, 65])
def test_execution_receipt_can_belong_to_any_registered_decision_actor(size):
    record = action_record()
    record["actor_ids"] = [f"actor-{i}" for i in range(size)]
    last = record["actor_ids"][-1]
    record["decision_actor_ids"] = [last]
    record["events"][0]["actor"] = last
    validate_action_evidence(record)


@pytest.mark.parametrize("field,value", [
    ("actor_ids", []), ("actor_ids", ["actor-1", "actor-1"]),
    ("actor_ids", ["environment"]), ("decision_actor_ids", []),
    ("decision_actor_ids", ["unknown"]),
])
def test_action_receipts_require_unambiguous_registered_actors(field, value):
    record = action_record()
    record[field] = value
    with pytest.raises(ValueError):
        validate_action_evidence(record)
