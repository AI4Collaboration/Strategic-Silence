"""Shared evidence checks and restoration inputs for future native environments."""
from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Callable, Mapping

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_action_evidence(record: dict) -> None:
    """Validate trace structure, not the semantic correctness of a native oracle.

    Failed and unfinished executions remain records. This check never imputes a
    defect from an attempted action or a model's final text.
    """
    require(record.get("outcome_basis") == "environment_trace_and_state",
            "a model answer alone is not execution evidence")
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
        require(event.get("actor") in {"provider", "recipient", "environment"}, "event actor required")
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
        require(any(e["actor"] == "recipient" and e["status"] == "ok"
                    and e["effect"] in {"mutate", "execute"} for e in events),
                "completion requires an executed recipient operation")
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


def restoration_inputs(
    recipient_state: dict,
    packets: Mapping[str, str],
    token_count: Callable[[str], int],
) -> dict[str, dict]:
    """Clone checkpoint metadata; only the initial evidence payload may change.

    Arm labels belong to the return keys (audit metadata), never actor inputs.
    The caller must establish minimality/placebo irrelevance and separately fork
    mutable files and native tool state. Later agent actions may change each branch.
    """
    require("evidence_update" not in recipient_state, "state already has an intervention")
    require(set(packets) == {"M", "P", "F"}, "reviewed M/P/F packets required")
    require(all(isinstance(value, str) and value.strip() for value in packets.values()), "empty evidence packet")
    require(packets["M"] != packets["P"], "target and placebo cannot be identical")
    for field in ("history", "task", "work_product", "environment_state", "participant_states",
                  "exogenous_state", "actions", "tools", "source_access", "budget"):
        require(field in recipient_state, "frozen recipient state missing " + field)
    branches = {}
    for arm, payload in {"O": "", **packets}.items():
        branch = deepcopy(recipient_state)
        branch["evidence_update"] = {
            "channel": "authenticated_reference_update",
            "content": payload,
        }
        branches[arm] = branch
    serialized = {
        arm: json.dumps(state, ensure_ascii=False, sort_keys=True)
        for arm, state in branches.items()
    }
    require(token_count(serialized["M"]) == token_count(serialized["P"]), "M/P serialized input lengths differ")
    return branches
