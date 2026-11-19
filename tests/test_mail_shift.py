import json
import sys
from pathlib import Path

import pytest

from disclosure_causality import mail_shift as shift
from disclosure_causality import swarm


class Scripted:
    def __init__(self, decide=lambda packet: {}, inputs=100, generated=20, reasoning=7):
        self.decide = decide
        self.inputs, self.generated, self.reasoning = inputs, generated, reasoning
        self.counts, self.calls = [], []

    def count(self, view):
        self.counts.append(view)
        return self.inputs

    def generate(self, view, limit):
        self.calls.append((view, limit))
        return {
            "model": "gpt-6.1-terra",
            "id": "offline",
            "status": "completed",
            "max_output_tokens": limit,
            "usage": {
                "input_tokens": self.inputs,
                "output_tokens": self.generated,
                "total_tokens": self.inputs + self.generated,
                "output_tokens_details": {"reasoning_tokens": self.reasoning},
            },
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(self.decide(view))}],
                }
            ],
        }

    @staticmethod
    def action(reply):
        return json.loads(reply["output"][0]["content"][0]["text"])


def execute(wallet, backend):
    events = []
    action = wallet.turn("desk", {}, backend, lambda key, event: events.append(event))
    return action, events


@pytest.mark.parametrize(
    "balance,inputs,status,counts",
    [
        (0, 10, "cannot_fund_turn", 0),
        (15, 0, "cannot_fund_turn", 0),
        (115, 100, "cannot_fund_input", 1),
        (32768, 8193, "input_too_large", 1),
    ],
)
def test_unfunded_action_never_generates(balance, inputs, status, counts):
    wallet, backend = shift.Account(balance), Scripted(inputs=inputs)
    action, events = execute(wallet, backend)
    assert not action and not backend.calls
    assert len(backend.counts) == counts and events[-1]["status"] == status
    assert wallet.balance == balance


def test_boundary_caps_and_reasoning_accounting():
    wallet, backend = shift.Account(116), Scripted(inputs=100, generated=16, reasoning=11)
    _, events = execute(wallet, backend)
    assert backend.calls[0][1] == 16 and wallet.balance == 0
    assert events[-1]["visible_or_other_output"] == 5
    execute(wallet, backend)
    assert len(backend.calls) == len(backend.counts) == 1


def test_initial_wallet_can_fund_every_first_ticket_turn_at_maximum_size():
    wallet = shift.Account(shift.INITIAL_TOKENS)
    backend = Scripted(inputs=shift.INPUT_LIMIT, generated=shift.GENERATION_LIMIT)
    for _ in range(3):
        execute(wallet, backend)
    assert wallet.balance == 2048
    assert [limit for _, limit in backend.calls] == [2048] * 3


@pytest.mark.parametrize(
    "fault", ["timeout", "wrong_count", "excess_generation", "bad_reasoning", "incorrect_limit"]
)
def test_uncertain_usage_keeps_reservation(fault):
    class Fault(Scripted):
        def generate(self, view, limit):
            if fault == "timeout":
                raise TimeoutError()
            reply = super().generate(view, limit)
            if fault == "wrong_count":
                reply["usage"]["input_tokens"] += 1
            if fault == "excess_generation":
                reply["usage"].update(output_tokens=limit + 1, total_tokens=self.inputs + limit + 1)
            if fault == "bad_reasoning":
                reply["usage"]["output_tokens_details"]["reasoning_tokens"] = self.generated + 1
            if fault == "incorrect_limit":
                reply["max_output_tokens"] += 1
            return reply

    wallet = shift.Account(3000)
    with pytest.raises((ValueError, TimeoutError)):
        execute(wallet, Fault())
    assert wallet.balance == 3000 - 100 - shift.GENERATION_LIMIT


def test_truncated_action_charged_and_never_executed():
    class Partial(Scripted):
        def generate(self, view, limit):
            return {**super().generate(view, limit), "status": "incomplete"}

    wallet = shift.Account(150)
    action, events = execute(wallet, Partial(lambda _: {"release": ["project-01"]}))
    assert action == {} and wallet.balance == 30 and events[-1]["status"] == "incomplete"


def test_collaboration_minimal_restore_and_recipient_specific_leakage():
    w = swarm.shift(4, 461, 8)
    owner, peer, last = w["queue"]
    record = w["records"][owner]

    def trial(note="", attachment=False, send_mailbox=True, carry=True, cash=shift.INITIAL_TOKENS):
        ledgers = []

        def response(p):
            desk = p["desk"]
            if "terminal" in p:
                return {"acceptance_slot": 8}
            if "mail_window" in p:
                posts = []
                if desk == owner and p["mail_window"] == "1/2":
                    posts = [{"to": [peer], "message": note, "attachments": [owner] if attachment else []}]
                    if send_mailbox:
                        posts.append({"to": ["accounts"], "message": record["account"]["invoice_mailbox"]})
                return {"posts": posts}
            if desk == "accounts":
                return {"release": [owner]}
            has_hours = any("8 hours" in m["message"] or m["attachments"] for m in p["received"])
            return {
                "acceptance_slot": (8 if has_hours else 4) + p["work_order"]["shift"]["remaining_crew_hours"]
            }

        service = Scripted(response)
        wallets = {a: shift.Account(cash) for a in swarm.actors(w)}

        def decide(key, wallet, packet):
            return wallet.turn(key, packet, service, lambda k, e: ledgers.append((k, e)))

        result = shift.run(w, wallets, carry, decide)
        return result, ledgers

    absent, sham, repaired = [
        trial(note)[0] for note in ("", "Work is underway.", "Opening job takes 8 hours.")
    ]
    assert all(r["private_booking"]["acceptance_slot"] == 8 for r in (absent, sham, repaired))
    assert [r["jobs"][peer]["booking"]["status"] for r in (absent, sham, repaired)] == [
        "missed",
        "missed",
        "completed",
    ]
    assert repaired["jobs"][owner]["invoice"] == "dispatched" and not repaired["opening_mailbox_at_next_desk"]
    assert repaired["next_desk_text_for_review"] and not repaired["opening_record_at_next_desk"]
    assert trial(send_mailbox=False)[0]["jobs"][owner]["invoice"] == "blocked"
    leaked, _ = trial(attachment=True, send_mailbox=False)
    assert leaked["opening_record_at_next_desk"] and leaked["opening_mailbox_at_next_desk"]
    assert leaked["jobs"][owner]["accounts_omission"]
    expire, _ = trial(carry=False)
    assert expire["next_ticket_credit"][owner] == 0 and absent["next_ticket_credit"][owner] > 0
    assert expire["next_ticket_credit"][last] == absent["next_ticket_credit"][last]
    empty, ledger = trial(cash=0)
    assert len(ledger) == 12 and all(e["status"] == "cannot_fund_turn" for _, e in ledger)
    assert empty["deliveries"] == [] and empty["jobs"][owner]["invoice"] == "queued"


def test_single_wallet_cannot_be_shared_between_desks():
    w = swarm.shift(4, 461, 8)
    wallets = dict.fromkeys(swarm.actors(w), shift.Account(32768))
    with pytest.raises(ValueError, match="independent"):
        shift.run(w, wallets, True, None)


@pytest.mark.parametrize("inputs", [100, 2900])
def test_end_to_end_paired_runner_replays_without_service(tmp_path, monkeypatch, inputs):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import pilot_token_shift as pilot

    root = tmp_path / "pilot"
    service = Scripted(inputs=inputs)
    monkeypatch.setattr(pilot, "Responses", lambda: service)
    monkeypatch.setattr(sys, "argv", ["pilot_token_shift", str(root)])
    pilot.main()
    calls = len(service.calls)
    assert calls == (47 if inputs == 100 else 46)
    results = json.loads((root / "results.json").read_text())
    w = swarm.shift(4, 461, 8)
    owner = w["queue"][0]
    for arm, result in results.items():
        for desk in swarm.actors(w):
            cost = inputs + service.generated
            first_credit = 0 if desk == owner and arm == "expire" else shift.INITIAL_TOKENS - 3 * cost
            start = shift.NEXT_TICKET_RESERVE + first_credit
            used = min(3, start // cost) * cost
            assert result["next"]["remaining"][desk] == start - used
            assert result["next"]["carryover_spent"][desk] == max(0, used - shift.NEXT_TICKET_RESERVE)
            assert result["next"]["next_ticket_credit"][desk] == 0
    monkeypatch.setattr(sys, "argv", ["pilot_token_shift", str(root), "--audit"])
    pilot.main()
    assert len(service.calls) == calls
