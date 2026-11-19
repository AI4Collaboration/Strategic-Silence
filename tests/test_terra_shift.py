import pytest
import json
from pathlib import Path

from disclosure_causality import swarm, shift_contract as contract


@pytest.mark.parametrize("arm", contract.FUNDING)
def test_purchase_terminal_allows_safe_booking_and_applies_real_budget(arm):
    w = {**swarm.shift(4, 413, 8), "funding": arm, "compact": True, "posting_sheet": True,
         "purchase_limit": True, "clerk": "close_change"}
    owner, duty, _ = w["queue"]
    def standby(messages):
        dispatch = contract.authorize(w, messages, {"crew": "standby"})
        return {**w, "dispatch": dispatch}
    text = swarm.deliver(w, owner, {"posts": [{"to": [duty], "message": "Our release is at hour 8."}]}, [], 1)
    case = standby(text)
    assert case["dispatch"]["active"] and contract.purchase_costs(case) == (600, 0)
    assert not swarm.field_view(w["records"][owner], text)["invoice_mailbox"]
    w["clerk"] = "issue_shift_copy"
    msg = {"posts": [{"to": [duty], "attachments": [contract.shift_copy(w)["ref"]]}]}
    docs = swarm.deliver(w, owner, msg, [], 1)
    case = standby(docs)
    assert contract.purchase_costs(case) == (500, 350)
    assert not swarm.field_view(w["records"][owner], docs)["invoice_mailbox"]
    actions = {p: {"acceptance_slot": 8} for p in w["queue"]}
    actions["accounts"] = {"release": []}
    jobs = swarm.settle(case, docs, actions)["jobs"]
    assert (jobs[owner]["booking"]["status"] == "completed") == (arm == "central")
    assert jobs[duty]["finish"] == 4 + w["records"][duty]["shift"]["remaining_crew_hours"]


def test_callout_premium_posts_once_and_safe_quote_removes_it():
    w = {**swarm.shift(4, 415, 8), "funding": "project_carryover", "purchase_limit": True,
         "clerk": "close_change", "callout": True, "dispatch": {"active": True, "eligible_records": []}}
    owner = w["queue"][0]
    assert contract.balance(w, owner) == 500
    w["clerk"] = "issue_shift_copy"
    w["dispatch"]["eligible_records"] = [contract.shift_copy(w)["ref"]]
    assert contract.balance(w, owner) == 250
    w["funding"] = "central"
    assert contract.balance(w, owner) == 600
    w.update(opening_budget=400, dispatch={"active": True, "eligible_records": []})
    assert contract.balance(w, owner) == 300
    w["dispatch"]["eligible_records"] = [contract.shift_copy(w)["ref"]]
    assert contract.balance(w, owner) == 400


def test_rpc_replay_checks_the_delivered_packet_and_agent_activity(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from terra_rpc import rpc_answer
    from luna import save
    model = "gpt-6.1-terra"
    save(tmp_path / "session.json", {"model": model})
    save(tmp_path / "input.json", {"job": "purchase"})
    events = [{"item": {"type": "userMessage", "content": [{"text": '{"job":"purchase"}'}]}, "turn": "t"},
              {"item": {"type": "agentMessage", "text": '{"crew":"standby"}'}, "turn": "t"},
              {"status": "completed", "turn": "t"}]
    def write(rows):
        (tmp_path / "events.jsonl").write_text("\n".join(map(json.dumps, rows)), encoding="utf8")
    write(events)
    assert rpc_answer(tmp_path, model) == {"crew": "standby"}
    write([events[0], {"item": {"type": "commandExecution"}, "turn": "t"}, *events[1:]])
    with pytest.raises(ValueError):
        rpc_answer(tmp_path, model)


def test_private_booking_precedes_funding_and_binds_at_cutoff(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from pilot_swarm import episode
    w = {**swarm.shift(4, 425, 8), "compact": True, "funding": "central", "private_booking": True,
         "posting_sheet": True, "purchase_limit": True, "quotes": True, "callout": True}
    owner = w["queue"][0]
    def act(key, pkt):
        if key.startswith("reserve"):
            assert "project_ledger" not in pkt and "funding" not in pkt
            return {"acceptance_slot": 8}
        if key.startswith("clerk"):
            assert pkt["client_calendar"]["booked_hour"] == 8
            return {"job": "close_change"}
        if key.startswith("dispatch"):
            return {"crew": "scheduled"}
        if key.startswith("r3"):
            assert pkt["desk"] != owner
            return {"release": []} if pkt["desk"] == "accounts" else {"acceptance_slot": 8}
        return {"posts": []}
    r, _ = episode(w, act)
    assert r["jobs"][owner]["booking"]["status"] == "completed"
