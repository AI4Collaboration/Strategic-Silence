"""Action-evidence validation tests."""
import pytest

from disclosure_causality.protocol import validate_action_evidence


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
