"""Scripted offline controls exercise the protocol; they are not LLM experiments."""
from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from .cases import Case, canonical, digest
from .engine import Action, Session
from .environments import LIVE_HANDOFF


PROFILES = ("compliant", "silent", "selective", "overshare")


class Policy(Protocol):
    def act(self, observation: dict, work: dict, *, retry: bool = False) -> Action: ...


class ScriptedPolicy:
    """Uses only actor observations. Disclosure faults are explicit test controls."""
    def act(self, observation: dict, work: dict, *, retry: bool = False) -> Action:
        kind = observation["environment"]
        previous = observation["evidence"].get(f'{work["previous"]}/coord', {}).get("data", {})
        args = {"unit": work["id"]}
        if kind == "M1":
            args["replace_input"] = work["index"] > 0 and previous.get("requires_retest", False)
        elif kind == "M2":
            available = previous.get("actual_capacity", work["quantity_needed"])
            args.update(route="backup" if retry or min(available, work["shared_available"]) < work["quantity_needed"] else "primary",
                        quantity=work["quantity_needed"])
        elif kind == "M3":
            args["input_revision"] = previous.get("revision", work["baseline_revision"])
        elif kind == "L1":
            args["depart_at"] = previous.get("arrival", work["planned_input_time"]) if work["index"] else 0
        elif kind == "L2":
            args["arrive_at"] = previous.get("available_after", work["planned_input_time"]) if work["index"] else 0
        elif kind == "T1":
            from .software import adapter_for_contract, legacy_adapter
            args["source"] = adapter_for_contract(previous) if previous else legacy_adapter()
        else:
            args["instruction_destination"] = previous.get("destination", work["instruction_value"])
            args["instruction_quantity"] = previous.get("quantity", work["instruction_quantity"])
        return Action(observation["actor"], work["operation"], args)


def _work(session: Session, unit: dict) -> tuple[dict, dict]:
    view = session.observe(unit["owner"])
    return view, next(w for w in view["work"] if w["id"] == unit["id"])


def announce(session: Session, unit: dict, profile: str = "compliant") -> dict:
    if profile not in PROFILES:
        raise ValueError("unknown scripted profile")
    _, work = _work(session, unit)
    ids = [] if profile == "silent" else [work["progress"]]
    if profile in {"compliant", "overshare"}:
        ids.append(work["handoff"])
    if profile == "overshare":
        ids.append(work["private"])
    return session.step(Action(unit["owner"], "send", {
        "recipient": unit["recipient"], "fact_ids": ids, "subject": unit["id"],
    }))


def prepare(case: Case, profile: str = "compliant", *,
            enforce_send_permissions: bool = False, policy: Policy | None = None) -> Session:
    """Stop after the focal report, before any recipient decision using it."""
    if profile not in PROFILES:
        raise ValueError("unknown scripted profile")
    policy = policy or ScriptedPolicy()
    session = Session(case, enforce_send_permissions=enforce_send_permissions)
    for actor in case.actors:
        session.step(Action(actor, "inspect"))
        if session.state["status"] != "active":
            return session
    if case.environment in LIVE_HANDOFF:
        first = case.units[0]
        view, work = _work(session, first)
        result = session.step(policy.act(view, work))
        if not result["accepted"]:
            return session
        announce(session, first, profile)
    else:
        for i, unit in enumerate(case.units):
            announce(session, unit, profile if i == 0 else "compliant")
            if session.state["status"] != "active":
                break
    return session


def continue_session(session: Session, *, verify: bool = False,
                     policy: Policy | None = None) -> Session:
    policy = policy or ScriptedPolicy()
    while session.state["status"] == "active" and session.state["world"]["next_unit"] < len(session.case.units):
        index = session.state["world"]["next_unit"]
        unit = session.case.units[index]
        if verify and (index or session.case.environment not in LIVE_HANDOFF):
            session.step(Action(unit["owner"], "query", {"fact_id": f'{unit["previous"]}/coord'}))
            if session.state["status"] != "active":
                break
        view, work = _work(session, unit)
        result = session.step(policy.act(view, work))
        if result.get("status") == "capacity_rejected" and session.state["status"] == "active":
            view, work = _work(session, unit)
            result = session.step(policy.act(view, work, retry=True))
        if session.state["status"] != "active":
            break
        if not result["accepted"]:
            raise RuntimeError(f"offline policy could not complete a native step: {result}")
        if session.case.environment in LIVE_HANDOFF:
            announce(session, unit)
    if session.state["status"] == "active":
        session.step(Action(session.case.units[-1]["recipient"], "finalize"))
    return session


def run_episode(case: Case, profile: str = "compliant", *, verify: bool = False,
                enforce_send_permissions: bool = False, policy: Policy | None = None) -> Session:
    return continue_session(prepare(case, profile, enforce_send_permissions=enforce_send_permissions,
                                    policy=policy), verify=verify, policy=policy)


def restoration_branches(checkpoint: Session) -> tuple[dict[str, Session], dict]:
    """Change the evidence packet only, through the ordinary sender's route.

    Wire sizes are UTF-8 byte matched; no claim is made about model token counts.
    All three arms take one sender action and advance the same discrete clock.
    """
    if checkpoint.state["status"] != "active":
        raise ValueError("restoration requires an active pre-decision checkpoint")
    focal = checkpoint.case.units[0]
    if focal["id"] in checkpoint.state["decisions"]:
        raise ValueError("recipient has already made the focal decision")
    owner, recipient = focal["owner"], focal["recipient"]
    knowledge = checkpoint.state["knowledge"][owner]
    for fid in (focal["coord"], focal["neutral"]):
        if fid not in knowledge or recipient not in knowledge[fid]["allowed"]:
            raise ValueError("restoration evidence must be known and authorized")
    packets = {"no_added_information": [],
               "required_information": [focal["coord"]],
               "unrelated_information": [focal["neutral"]]}
    sizes = [len(canonical({"sender": owner, "recipient": recipient,
                            "evidence": [knowledge[fid] for fid in ids]}).encode("utf-8"))
             for ids in packets.values()]
    width = max(sizes)
    frozen_world = deepcopy(checkpoint.state["world"])
    branches = {}
    for arm, ids in packets.items():
        branch = checkpoint.fork()
        result = branch.step(Action(owner, "send", {"recipient": recipient, "fact_ids": ids,
                                                     "wire_bytes": width, "subject": focal["id"]}))
        if not result["accepted"]:
            raise ValueError("restoration delivery failed")
        if branch.state["world"] != frozen_world or branch.state["facts"] != checkpoint.state["facts"]:
            raise AssertionError("restoration changed the native world or source facts")
        branches[arm] = branch
    return branches, {"checkpoint_hash": checkpoint.snapshot()["snapshot_hash"],
                      "native_world_hash": digest(frozen_world), "update_wire_bytes": width,
                      "match_unit": "UTF-8 bytes, not LLM tokens", "source": owner,
                      "recipient": recipient, "channel": "message"}


def run_comparison(checkpoint: Session, *, verify: bool = False) -> tuple[dict, dict[str, Session]]:
    branches, audit = restoration_branches(checkpoint)
    scores = {arm: continue_session(branch, verify=verify).score() for arm, branch in branches.items()}
    for branch in branches.values():
        branch.evidence_record()
    complete = all(score["execution_status"] == "completed" for score in scores.values())
    comparison = {"audit": audit, "scores": scores,
                  "effect": {
                      "loss_reduction": scores["no_added_information"]["native"]["loss"]
                                        - scores["required_information"]["native"]["loss"],
                      "loss_reduction_vs_unrelated": scores["unrelated_information"]["native"]["loss"]
                                                     - scores["required_information"]["native"]["loss"]}
                  if complete else None,
                  "interpretation": "scripted simulator diagnostic; not evidence of LLM strategy"}
    return comparison, branches
