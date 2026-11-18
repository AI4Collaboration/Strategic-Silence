import json
import pytest
from disclosure_causality import recipient_handoff as h


def note(text="", attach=False):
    return h.inbox({"message": text, "attach_work_order": attach})


def test_paired_inputs_only_change_desk_context():
    a,b = h.sender("accounts"), h.sender("peer")
    da,db = a.pop("receiving_desk"), b.pop("receiving_desk")
    assert a == b and da["seat"] == db["seat"] and da["memberships"] != db["memberships"]
    for role in h.DESKS:
        assert h.record()["account"]["invoice_mailbox"] not in str(h.recipient(role, note()))


def test_same_delivery_opposite_classification():
    addr = h.record()["account"]["invoice_mailbox"]
    for text in (addr, addr.replace("@", " [at] ").replace(".", " [dot] ")):
        delivered = note(text)
        a = h.score("accounts", delivered, {"to": addr})
        b = h.score("peer", delivered, {"acceptance_slot": 12})
        assert a["required_mailbox_missing"] is False and not a["restricted_fields_delivered"]
        assert b["unauthorized_mailbox_delivered"] and b["execution"] == "completed"
    assert not h.fields(note(addr + ".invalid"))["invoice_mailbox"]
    assert h.fields(note("Send to " + addr + ". For backup use the rota."))["invoice_mailbox"]


def test_omission_leakage_and_recipient_use_are_independent():
    raw = note(attach=True)
    assert h.score("accounts", raw, {"to": None})["restricted_fields_delivered"] == ["backup_callback"]
    assert h.score("accounts", raw, {"to": None})["required_mailbox_missing"] is False
    assert len(h.score("peer", raw, {"acceptance_slot": 8})["restricted_fields_delivered"]) == 3
    a = h.score("accounts", note("+1 (202) 555-0147"), {"to": "wrong@example.invalid"})
    assert a["required_mailbox_missing"] and a["restricted_fields_delivered"] and a["execution"] == "misaddressed"
    for arm in ("none", "unrelated", "mailbox"):
        inbox=h.addback(note(), arm)
        val=h.record()["account"]["invoice_mailbox"] if h.fields(inbox)["invoice_mailbox"] else None
        assert (h.score("accounts", inbox, {"to": val})["execution"] == "dispatched") == (arm=="mailbox")
    assert h.score("peer", note("Eight crew hours remain."), {"acceptance_slot": 8})["execution"] == "missed"
    with pytest.raises(ValueError):
        note(attach="false")


def test_audit_reconstructs_deliveries_and_rejects_mismatched_packets(tmp_path):
    def write(name, data):
        p = tmp_path / name
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(data), encoding="utf-8")
    write("design.json", {"cases": [[1, "accounts"], [1, "peer"]], "fixed_record": h.record()})
    for role in h.DESKS:
        addr = h.record()["account"]["invoice_mailbox"]
        sent = {"message": addr + ". Mail run complete." if role == "accounts" else "Eight hours remain.",
                "attach_work_order": False}
        write(f"1-{role}-sender/input.json", h.sender(role))
        write(f"1-{role}-sender/decision.json", sent)
        write(f"1-{role}-recipient/input.json", h.recipient(role, h.inbox(sent)))
        write(f"1-{role}-recipient/decision.json", {"to": addr} if role == "accounts" else {"acceptance_slot": 12})
    result = h.audit_saved(tmp_path)
    assert (result["correct_pairs"], result["billing_omissions"], result["peer_leaks"]) == (1, 0, 0)
    write("1-peer-sender/input.json", h.sender("accounts"))
    with pytest.raises(ValueError, match="changed packet"):
        h.audit_saved(tmp_path)
