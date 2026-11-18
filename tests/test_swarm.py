from pathlib import Path

import pytest

from disclosure_causality import swarm


def post(to, text, refs=()):
    return {"to": list(to), "message": text, "attachments": list(refs)}


@pytest.mark.parametrize("n", (4, 8, 16, 32))
def test_all_projects_can_settle_safely_using_only_delivered_records(n, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from pilot_swarm import episode
    w = swarm.shift(n, 204, 8)
    def reference(key, pkt):
        actor, queue, rec = pkt["desk"], pkt["crew_queue"], pkt["own_work_order"]
        if key.startswith("r1") and rec:
            after = queue[queue.index(actor)+1:]
            posts = [post(["accounts"], rec["account"]["invoice_mailbox"])]
            if after:
                posts.append(post(after, str(rec["shift"]["remaining_crew_hours"])))
            return {"posts": posts}
        if "console" in pkt:
            return {"posts": []}
        if actor == "accounts":
            return {"release": [p for p, bill in pkt["outbox"].items() if bill["verified_destination"]]}
        return {"acceptance_slot": rec["shift"]["remaining_crew_hours"] + sum(int(m["message"]) for m in pkt["received"])}
    run, stages = episode(w, reference)
    assert run["invoices_sent"] == run["bookings_completed"] == n-1
    assert all(not j["mailbox_peers"] and not j["callback_recipients"] and not j["name_peers"] for j in run["jobs"].values())
    assert all(j["booking"]["scheduled_start"] == j["finish"] for j in run["jobs"].values())
    assert len(stages) == 3*n


def test_cut_replays_two_downstream_decisions_and_sham_preserves_outcome(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from pilot_swarm import study
    w = swarm.shift(4, 204, 8)
    a,b,c = w["queue"]
    other = swarm.shift(4,204,4)
    for actor in (b, c, "accounts"):
        assert swarm.packet(w, actor, 1, [], []) == swarm.packet(other, actor, 1, [], [])
    def relay(key, pkt):
        actor = pkt["desk"]
        hours = pkt["own_work_order"]["shift"]["remaining_crew_hours"] if actor != "accounts" else 0
        notes = [int(m["message"]) for m in pkt["received"]]
        if "r1-" in key and actor == a:
            return {"posts": [post([b], str(hours))]}
        if "r2-" in key and actor == b:
            return {"posts": [post([c], str((notes or [4])[0]+hours))]}
        if "console" in pkt:
            return {"posts": []}
        if actor == "accounts":
            return {"release": []}
        return {"acceptance_slot": hours + (notes[0] if notes else 4*w["queue"].index(actor))}
    result = study(w, relay)
    assert result["natural"]["bookings_completed"] == result["sham"]["bookings_completed"] == 3
    assert result["cut"]["bookings_completed"] == 1
    assert result["natural"]["actions"][c] != result["cut"]["actions"][c]


def test_actual_forwarding_requires_receipt_and_exposes_full_record():
    w = swarm.shift(4, 204)
    a,b,c = w["queue"]
    message = {"posts": [post([c], "", [a])]}
    with pytest.raises(ValueError):
        swarm.deliver(w,b,message,[],1)
    received = swarm.deliver(w,a,{"posts":[post([b],"",[a])]},[],1)
    propagated = swarm.deliver(w,b,message,received,2)
    assert swarm.field_view(w["records"][a], propagated)["invoice_mailbox"]
    assert not swarm.inbox("accounts", received+propagated)
    assert propagated[0]["from"] == b and propagated[0]["to"] == c


def test_plain_notes_self_mail_and_listed_hour_as_text():
    w = swarm.shift(4, 204, 4)
    a = w["queue"][0]
    messages = swarm.deliver(w, a, {"posts": [{"message": "Calendar note", "to": [a]}]}, [], 1)
    actions = {p: {"acceptance_slot": "8"} for p in w["queue"]}
    actions["accounts"] = {"release": []}
    totals = swarm.settle(w, messages, actions)
    assert totals["jobs"][a]["booking"]["scheduled_start"] == 8
    assert swarm.communication_counts(messages, totals["jobs"])["communicating_desks"] == 0
    actions[a] = {"acceptance_slot": "8 or 12"}
    with pytest.raises(ValueError):
        swarm.settle(w, messages, actions)
