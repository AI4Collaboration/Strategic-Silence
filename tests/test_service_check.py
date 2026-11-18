import pytest
from disclosure_causality import service_check as s


def test_only_real_arrival_moves():
    for make in (s.audit_sender, lambda a: s.audit_desk(a, s.CONTROLS["false"])):
        a, b = make(0), make(16)
        x, y = a.pop("callbacks")[0], b.pop("callbacks")[0]
        assert a == b
        assert (x.pop("arrival_minute"), y.pop("arrival_minute")) == (0, 16)
        assert y.pop("receipt_due_minute") - x.pop("receipt_due_minute") == 16
        assert x.keys() == y.keys() == {"ref", "request"} and x["ref"] == y["ref"]
    p = str(s.sender(0))
    assert not any(x in p for x in s.CONTROLS.values())
    assert "billing." not in str(s.audit_desk(0, ""))


@pytest.mark.parametrize("arr,solo,probe", [(16, 12, 8), (0, 12, 20)])
def test_slot_changes_customer_outcome_not_message_valence(arr, solo, probe):
    assert s.execute(arr, "reply", "q_first")["customer_wait_minutes"] == solo
    assert s.execute(arr, "refer", "q_first")["customer_wait_minutes"] == probe
    assert s.execute(arr, "refer", "c_first")["customer_wait_minutes"] == solo
    assert s.execute(arr, "refer", "q_first")["customer_on_time"] == (arr == 16)
    assert s.execute(arr, "reply", "q_first", stale=False)["customer_wait_minutes"] == 8


def test_same_worker_truth_route_and_first_contact_cutoff():
    assert s.audit_run(16, "routine") == s.audit_run(16, "incident")
    assert s.audit_run(0, "routine")["customer_wait_minutes"] == 12
    assert s.audit_run(0, "incident")["customer_wait_minutes"] == 20
    assert not s.evidence_packet(16, "", "reply")["available_records"]
    real = s.evidence_packet(0, "", "reply")
    assert s.documented(real, {"decision": "documented", "record": 1})
    assert not s.documented(real, {"decision": "documented", "record": 2})
    assert all(x not in str(s.audit_sender(0)) for x in s.CONTROLS.values())


def test_unreceived_report_cannot_be_truthfully_relayed():
    for make in (s.audit_sender, lambda a: s.audit_desk(a, "Q17"), s.schedule_probe):
        a, b = make(0), make(16)
        assert "Verified missing" in a.pop("callbacks")[0]["request"]
        assert "no customer report received" in b.pop("callbacks")[0]["request"]
        assert a == b
    for a in (0, 16):
        assert s.audit_controls(a)["false"] == s.CONTROLS["false"]
    assert "has reported" in s.audit_controls(0)["relay"] and "don't yet have" in s.audit_controls(16)["relay"]


def test_release_owner_receives_a_redacted_contact_not_the_senders_private_log():
    private = s.audit_sender(16)["own_record"]
    message = f"Check Q17 for {private['client_name']}; {private['billing_contact']}"
    assert s.audit_desk(16, message)["ticket"]["text"] == message
    records = s.evidence_packet(16, message, "routine")["available_records"]
    assert records == [{"contact": "Check Q17 for [redacted]; [redacted]", "first_contact_action": "routine"}]
