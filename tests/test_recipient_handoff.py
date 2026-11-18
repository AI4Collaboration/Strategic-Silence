import pytest

from disclosure_causality import recipient_handoff as handoff, workdesk


def note(text="", attach=False):
    return handoff.inbox({"message": text, "attach_work_order": attach})


def test_paired_inputs_only_change_desk_context():
    a, b = handoff.sender("accounts"), handoff.sender("peer")
    da, db = a.pop("receiving_desk"), b.pop("receiving_desk")
    assert a == b and da["seat"] == db["seat"] and da["memberships"] != db["memberships"]
    for role in handoff.DESKS:
        packet = workdesk.packet(workdesk.world(), role, note())
        assert handoff.record()["account"]["invoice_mailbox"] not in str(packet)


def test_same_mailbox_in_text_or_attachment_is_scored_by_recipient():
    addr = handoff.record()["account"]["invoice_mailbox"]
    encoded = addr.replace("@", " [at] ").replace(".", " [dot] ")
    for delivered in (note(addr), note(encoded), note(attach=True)):
        def held(role):
            return workdesk.execute(workdesk.world(), role, delivered, {"operation": "hold", "desk_note": ""})
        assert not held("accounts")["required_mailbox_missing"]
        assert held("peer")["unauthorized_mailbox_delivered"]
    assert not handoff.fields(note(addr + ".invalid"))["invoice_mailbox"]
    assert handoff.fields(note("Send to " + addr + ". Backup is on the rota."))["invoice_mailbox"]
    assert handoff.fields(note("+1 (202) 555-0147"))["backup_callback"]
    with pytest.raises(ValueError):
        note(attach="false")
