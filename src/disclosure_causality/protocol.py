"""Validate action receipts and native outcome evidence."""
from __future__ import annotations

import re

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _actor_ids(value: object, label: str) -> set[str]:
    require(isinstance(value, (list, tuple)) and bool(value), label + " required")
    require(all(isinstance(actor, str) and actor.strip() and actor != "environment"
                for actor in value), label + " must contain named participants")
    require(len(set(value)) == len(value), label + " must be unique")
    return set(value)


def validate_action_evidence(record: dict) -> None:
    """Validate trace structure, not the semantic correctness of a native oracle.

    Failed and unfinished executions remain records. This check never imputes a
    defect from an attempted action or a model's final text.
    """
    require(record.get("outcome_basis") == "environment_trace_and_state",
            "a model answer alone is not execution evidence")
    actors = _actor_ids(record.get("actor_ids"), "actor IDs")
    decision_actors = _actor_ids(record.get("decision_actor_ids"), "decision actor IDs")
    require(decision_actors <= actors, "decision actors must be registered participants")
    status = record.get("execution_status")
    require(status in {"completed", "deferred", "exhausted", "failed", "no_action"}, "execution status required")
    for field in ("initial_state_hash", "final_state_hash"):
        require(re.fullmatch(r"[0-9a-f]{64}", record.get(field, "")) is not None, "state snapshot hash required")
    events = record.get("events")
    require(isinstance(events, list), "execution events required")
    previous = record["initial_state_hash"]
    identifiers = set()
    for event in events:
        identifier = event.get("event_id")
        require(isinstance(identifier, str) and identifier and identifier not in identifiers, "unique event ID required")
        identifiers.add(identifier)
        require(event.get("actor") in actors | {"environment"}, "registered event actor required")
        require(isinstance(event.get("tool"), str) and event["tool"]
                and isinstance(event.get("arguments"), dict), "executed tool and arguments required")
        require(event.get("effect") in {"observe", "mutate", "execute", "communicate"}, "tool effect required")
        require(event.get("status") in {"ok", "rejected", "error"}, "tool status required")
        require(bool(event.get("result_reference")), "tool receipt reference required")
        require(event.get("before_state_hash") == previous, "broken state-transition chain")
        previous = event.get("after_state_hash", "")
        require(re.fullmatch(r"[0-9a-f]{64}", previous) is not None, "post-action snapshot hash required")
    require(previous == record["final_state_hash"], "final snapshot does not match the execution trace")
    if status == "completed":
        require(any(e["actor"] in decision_actors and e["status"] == "ok"
                    and e["effect"] in {"mutate", "execute"} for e in events),
                "completion requires an executed decision-actor operation")
    checks = record.get("defect_checks")
    require(isinstance(checks, list), "native defect checks required")
    if status == "completed":
        require(bool(checks), "completed tasks require native defect checks")
    for check in checks:
        require(isinstance(check.get("name"), str) and check["name"]
                and bool(check.get("oracle_reference")), "a native defect oracle is required")
        require(check.get("status") in {"observed", "unresolved"}, "defect observation status required")
        require(isinstance(check.get("event_ids"), list) and set(check["event_ids"]) <= identifiers,
                "defect evidence must refer to recorded events")
        if check["status"] == "observed":
            require(bool(check.get("state_reference")) and check.get("value") is not None
                    and bool(check.get("unit")), "observed defects require state evidence and units")
        else:
            require(check.get("value") is None, "unresolved defects cannot be scored as zero")
