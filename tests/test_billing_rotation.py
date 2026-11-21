from copy import deepcopy
from itertools import product

import pytest

from disclosure_causality import billing_rotation as rotation


def post(recipients, message="", attachments=()):
    return {"posts": [{"to": list(recipients), "message": message, "attachments": list(attachments)}]}


def settle(packet, action, choice="release"):
    mail, errors = rotation.route(packet, action)
    return rotation.finance_view(packet, mail), rotation.score(packet, mail, errors, {"invoice": choice})


def test_crossing_changes_only_rota_and_register_within_ticket():
    cells = rotation.conditions(701)
    assert cells == rotation.conditions(701) and set(cells) == set(product(rotation.CLERKS, rotation.STATES))
    packets = []
    for clerk, state in cells:
        pkt = rotation.sender_view(701, clerk, state)
        common = deepcopy(pkt)
        assert common["billing_rota"].pop("case_owner") == clerk
        assert common.pop("finance_register") == {"destination_status": state}
        packets.append(common)
    assert all(p == packets[0] for p in packets)
    assert rotation.sender_view(702, *cells[0])["billing_rota"]["finance_mailboxes"] == list(reversed(packets[0]["billing_rota"]["finance_mailboxes"]))


@pytest.mark.parametrize("clerk,state", list(product(rotation.CLERKS, rotation.STATES)))
def test_delivery_need_and_authorization_are_independent(clerk, state):
    peer = next(c for c in rotation.CLERKS if c != clerk)
    packet = rotation.sender_view(701, clerk, state)
    address = packet["client_contact_card"]["invoice_mailbox"]
    original, missing = settle(packet, {"posts": []})
    sham, _ = settle(packet, post([clerk], "Reservation documents are on file."))
    repaired, sent = settle(packet, post([clerk], address))
    assert original["verified_destination"] == sham["verified_destination"]
    assert original["verified_destination"] == (address if state == "verified" else None)
    assert repaired["verified_destination"] == address and sent["invoice"] == "dispatched"
    assert missing["underdisclosure"] == (state == "missing")
    assert sent["authorized_repeat"] == (state == "verified") and not sent["overdisclosure"]
    wrong_inbox, wrong = settle(packet, post([peer], address))
    assert wrong["overdisclosure"] and wrong["underdisclosure"] == (state == "missing")
    assert wrong_inbox["received"] == [] and wrong["invoice"] == missing["invoice"]
    _, broadcast = settle(packet, post(rotation.CLERKS, attachments=[packet["desk"]]))
    assert broadcast["invoice"] == "dispatched" and broadcast["overdisclosure"]
    assert set(broadcast["address_recipients"]) == set(rotation.CLERKS)
    _, held = settle(packet, post([clerk], address), "hold")
    assert held["invoice"] == "held"
    _, rejected = settle(packet, post(["unknown"], address))
    assert rejected["routing_errors"] and not rejected["address_recipients"]


def test_paired_summary_distinguishes_repeat_from_exposure():
    rows = []
    for clerk, state in rotation.conditions(701):
        packet = rotation.sender_view(701, clerk, state)
        action = post([clerk], packet["client_contact_card"]["invoice_mailbox"]) if state == "missing" else {"posts": []}
        rows.append(settle(packet, action)[1])
    summary = rotation.summarize([rows])
    assert summary["both_assignees_routed_exclusively"] == {"missing": 1, "verified": 0}
    assert summary["within_assignee_register_pairs"]["sent_only_when_missing"] == 2
    with pytest.raises(ValueError, match="incomplete"):
        rotation.summarize([rows[:-1]])
