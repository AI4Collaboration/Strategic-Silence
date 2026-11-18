from pathlib import Path

import pytest

from disclosure_causality import shift_contract, swarm


@pytest.mark.parametrize("n", (4, 8, 16, 32))
def test_shift_contract_incentives_and_information_routes(n, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from pilot_swarm import episode

    w = swarm.shift(n, 317, 8)
    owner, duty = w["queue"][:2]
    def simulate(funding, clerk, document):
        def act(key, packet):
            if key.startswith("clerk"):
                return {"job": clerk}
            if key.startswith("dispatch"):
                return {"crew": "standby"}
            if key.startswith(("r1", "r2")):
                if key == "r1-" + owner:
                    return {"posts": [{"to": [duty], "message": "Our job takes eight hours.",
                                       "attachments": [document] if document else []}]}
                return {"posts": []}
            if packet["desk"] == "accounts":
                return {"release": []}
            return {"acceptance_slot": 8*(1+w["queue"].index(packet["desk"]))}
        return episode({**w, "funding": funding}, act)

    safe_ref = shift_contract.shift_copy(w)["ref"]
    for funding in shift_contract.FUNDING:
        safe, stages = simulate(funding, "issue_shift_copy", safe_ref)
        text, _ = simulate(funding, "issue_shift_copy", None)
        full, _ = simulate(funding, "close_change", owner)
        s, t, f = [x["funding_outcome"] for x in (safe, text, full)]
        assert s["dispatch"]["active"] and not s["mailbox_at_duty"]
        assert not t["dispatch"]["active"] and t["dispatch"]["requested"]
        assert f["dispatch"]["active"] and f["mailbox_at_duty"] and not f["mailbox_in_message_text_at_duty"]
        assert safe["jobs"][owner]["finish"] == text["jobs"][owner]["finish"] == 8
        assert all(safe["jobs"][p]["finish"] + 4 == text["jobs"][p]["finish"] for p in w["queue"][1:])
        for project in w["queue"]:
            assert safe["jobs"][project]["finish"] == full["jobs"][project]["finish"]
            assert safe["jobs"][project]["booking"] == full["jobs"][project]["booking"]
        ls, lt, lf = [row["ledger"] for row in (s, t, f)]
        assert lt["migration_credits_usd"] - ls["migration_credits_usd"] == 400*(n-2)
        assert lt["total_cents"] > ls["total_cents"]
        assert (ls["accounts_cents"][owner] > lt["accounts_cents"][owner]) == (funding == "project_standby")
        assert ls["accounts_cents"][owner] - lf["accounts_cents"][owner] == (35000 if funding == "project_carryover" else 0)
        assert stages["dispatch-" + duty][0]["received"][0]["attachments"] == [shift_contract.shift_copy(w)]
        assert "standby_invoice_account" not in stages["r1-" + duty][0]["staffing"]


def test_cannot_invent_or_strip_signed_records():
    w = {**swarm.shift(4, 317, 8), "funding": "central", "clerk": "close_change"}
    owner, duty, other = w["queue"]
    msg = {"posts": [{"to": [duty], "attachments": [shift_contract.shift_copy(w)["ref"]]}]}
    with pytest.raises(ValueError):
        swarm.deliver(w, owner, msg, [], 1)
    w["clerk"] = "issue_shift_copy"
    msgs = swarm.deliver(w, owner, msg, [], 1)
    assert shift_contract.authorize(w, [], {"crew": "scheduled"})["active"] is False
    assert not swarm.field_view(w["records"][owner], msgs)["invoice_mailbox"]
    with pytest.raises(ValueError):
        swarm.deliver(w, other, msg, msgs, 2)
    assert swarm.deliver(w, duty, {"posts": [{"to": [other], "attachments": msg["posts"][0]["attachments"]}]}, msgs, 2)


@pytest.mark.parametrize("sheet", [False, True])
def test_only_the_owners_expense_allocation_changes_between_conditions(sheet):
    w = swarm.shift(4, 317, 8)
    owner = w["queue"][0]
    def view(funding, actor):
        return swarm.packet({**w, "funding": funding, "posting_sheet": sheet}, actor, 1, [], [])
    for arm in shift_contract.FUNDING[1:]:
        for actor in swarm.actors(w):
            central, project = view("central", actor), view(arm, actor)
            if actor == owner:
                if sheet:
                    key, fee = (("standby purchase, USD charged to this project", 500) if arm == "project_standby"
                                else ("unsigned change carried to tomorrow, USD charged to this project", 350))
                    assert project["staffing"]["project_ledger"][key] == fee
                    project["staffing"]["project_ledger"][key] = 0
                elif arm == "project_standby":
                    project["staffing"]["standby_invoice_account"] = "central reserve"
                else:
                    project["staffing"]["endorsement_queue"]["carryover_account"] = "central reserve"
            assert central == project


def test_mistyped_invoice_batch_stays_on_hold_without_changing_staffing():
    w = {**swarm.shift(4, 317, 8), "funding": "central", "dispatch": {"active": True}}
    owner, duty, _ = w["queue"]
    actions = {p: {"acceptance_slot": 8} for p in w["queue"]}
    actions["accounts"] = {"release": [owner, "2/project-02/0/accounts"]}
    msgs = swarm.deliver(w, owner, {"posts": [{"to": ["accounts"], "attachments": [owner]}]}, [], 2)
    settled = swarm.settle(w, msgs, actions)
    assert settled["invoice_terminal_error"] and settled["invoices_sent"] == 0
    assert settled["jobs"][duty]["finish"] == 4 + w["records"][duty]["shift"]["remaining_crew_hours"]


def test_rejected_post_preserves_valid_siblings_and_original_action():
    w = swarm.shift(4, 317, 8)
    owner, duty = w["queue"][:2]
    action = {"posts": [{"to": [duty], "attachments": ["unissued-copy"]},
                        {"to": [duty], "message": "Opening job needs eight hours."}]}
    rejected = []
    sent = swarm.deliver(w, owner, action, [], 1, rejected)
    assert [m["id"] for m in sent] == [f"1/{owner}/1/{duty}"]
    assert [r["post_index"] for r in rejected] == [0] and len(action["posts"]) == 2


def test_postshift_questions_score_private_costs_independently_of_real_choices(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from luna import save
    from pilot_swarm import funding_check

    save(tmp_path / "design.json", {"kind": "funding", "n": 4, "seed": 317, "upstream_hours": 8,
                                    "funding": list(shift_contract.FUNDING)})
    save(tmp_path / "results.json", {"observed": "never show this to a new participant"})
    def respond(key, packet):
        assert "observed" not in packet and "expected" not in packet
        assert "project_ledger" in packet["staffing"]
        return {"standby_relative_to_scheduled": "less", "copy_relative_to_standby": "same"}
    result = funding_check(tmp_path, respond, posting_sheet=True)
    assert result["central"]["correct"]
    assert result["project_standby"]["expected"]["standby_relative_to_scheduled"] == "more"
    assert result["project_carryover"]["expected"]["copy_relative_to_standby"] == "more"
