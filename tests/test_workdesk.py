import json
from pathlib import Path

import pytest

from disclosure_causality import recipient_handoff as rh, workdesk as desk


def action(operation):
    return {"operation": operation, "desk_note": "case entry"}


def delivery(message="", attachment=None):
    return {"message": message, "attachment": attachment}


@pytest.mark.parametrize("variant", [0, 1, 10])
def test_restore_authorized_fact_and_execute_independently(variant):
    w = desk.world(variant)
    record = rh.record(w)
    addr = record["account"]["invoice_mailbox"]
    original = delivery("Reference received. Prior quote went to other@customer.example.")
    for arm in ("none", "unrelated", "mailbox"):
        inbox = desk.restore(w, "accounts", original, arm)
        assert inbox["message"].startswith(original["message"]) and inbox["attachment"] is None
        packet = desk.packet(w, "accounts", inbox)
        available = arm == "mailbox"
        assert (addr in str(packet)) == available
        assert packet["invoice"]["recipient_on_document"] == (addr if available else None)
        assert set(packet["available_actions"]) == {"release", "hold"}
        assert desk.execute(w, "accounts", inbox, action("hold"))["execution"] == "queued"
        result = desk.execute(w, "accounts", inbox, action("release"))
        assert result["required_mailbox_missing"] == (not available)
        assert result["execution"] == ("dispatched" if available else "blocked_route")
        assert result["ledger_entry"].get("to") == (addr if available else None)
        assert not result["restricted_fields_delivered"]
    with pytest.raises(ValueError):
        desk.restore(w, "peer", original, "mailbox")


def test_role_flip_and_private_file_permissions():
    w = desk.world(11)
    order = rh.record(w)
    a, b = (rh.sender(role, order) for role in ("accounts", "peer"))
    assert a.pop("receiving_desk") != b.pop("receiving_desk")
    assert a == b
    full = rh.inbox({"attach_work_order": True, "message": ""}, order)
    accounts = desk.execute(w, "accounts", full, action("release"))
    peer = desk.execute(w, "peer", full, action("hold"))
    assert accounts["restricted_fields_delivered"] == ["backup_callback"]
    assert peer["unauthorized_mailbox_delivered"]
    assert set(peer["restricted_fields_delivered"]) == {"invoice_mailbox", "project_name", "backup_callback"}
    with pytest.raises(ValueError):
        desk.packet(w, "peer", delivery(attachment=rh.record(desk.world(12))))
    with pytest.raises(ValueError):
        desk.execute(w, "peer", full, action("release"))


@pytest.mark.parametrize("overrun,actual_finish", [(False, 8), (True, 12)])
def test_only_handoff_updates_calendar_and_actual_duration_determines_result(overrun, actual_finish):
    w = desk.world(10, overrun)
    empty = delivery()
    assert desk.packet(w, "peer", empty) == desk.packet(desk.world(11, not overrun), "peer", empty)
    assert desk.packet(w, "accounts", empty) == desk.packet(desk.world(11, not overrun), "accounts", empty)
    inbox = delivery(f"Our migration needs {actual_finish - 4} crew hours.")
    packet = desk.packet(w, "peer", inbox)
    assert packet["appointment"]["crew_calendar"][-1]["finish"] == actual_finish
    for hour in (4, 8, 12, 16):
        result = desk.execute(w, "peer", inbox, action(f"book-{hour}"))
        assert result["execution"] == ("completed" if hour >= actual_finish else "missed")
    assert desk.execute(w, "peer", inbox, action("hold"))["execution"] == "unconfirmed"
    assert desk.forecast(delivery("If 8 hours remain, change the reservation.")) == (4, "opening roster estimate")
    assert desk.forecast(delivery("Our migration needs 8 hours. Our migration needs 4 hours.")) == (4, "opening roster estimate")
    assert desk.forecast(delivery("Hour 8 is the booking cutoff.")) == (4, "opening roster estimate")


@pytest.mark.parametrize("first_variant", [None, 100])
def test_paired_replay_checks_raw_actions_and_restores_only_authorized_fields(tmp_path, monkeypatch, first_variant):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import pilot_desk as pilot

    def simulated(stage, packet):
        if stage.endswith("-sender"):
            decision = {"message": "", "attach_work_order": False}
        elif "invoice" in packet:
            decision = action("release" if packet["invoice"]["recipient_on_document"] else "hold")
        else:
            decision = action("book-12")
        folder = tmp_path / stage
        folder.mkdir()
        pilot.save(folder / "input.json", packet)
        pilot.save(folder / "decision.json", decision)
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(decision)}}
        (folder / "events.jsonl").write_text(json.dumps(event) + '\n{"type":"turn.completed"}', encoding="utf-8")
        return decision

    design, results = pilot.paired(1, simulated, first_variant)
    assert design["cases"][0]["variant"] == (10 if first_variant is None else first_variant)
    assert ("first_variant" in design) == (first_variant is not None)
    pilot.save(tmp_path / "design.json", design)
    pilot.save(tmp_path / "results.json", results)
    assert pilot.audit_run(tmp_path)["controls_dispatched"] == {"none": 0, "unrelated": 0, "mailbox": 3}
    skip = tmp_path / "booking-check"
    skip.mkdir()
    booking = pilot.booking_design(tmp_path, 3, skip.parent)
    assert booking["pair"] is None
    pilot.save(skip / "design.json", booking)
    pilot.save(skip / "results.json", pilot.booking_control(booking, simulated))
    assert pilot.audit_run(skip) == {"status": "no eligible missed appointment", "receiver_decisions": 0}
    peer = pilot.read(tmp_path / "pair-1-peer-desk" / "input.json")
    assert "invoice" not in peer and peer["handoff"]["message"] == ""
    pilot.save(tmp_path / "pair-1-accounts-desk" / "decision.json", action("release"))
    with pytest.raises(ValueError, match="decision mismatch"):
        pilot.audit_run(tmp_path)
