"""Run or replay a single-crew shift on a hard-capable Terra Responses service."""

import argparse
import json
import os
from functools import partial
from pathlib import Path
from random import Random
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from luna import read, save

from disclosure_causality import mail_shift, swarm

MODEL = "gpt-6.1-terra"


class RejectRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Terra endpoint returned a redirect")


class Responses:
    def __init__(self):
        self.base = os.environ.get("TERRA_RESPONSES_BASE", "").rstrip("/")
        self.token = os.environ.get("TERRA_RESPONSES_KEY")
        endpoint = urlsplit(self.base)
        if (
            endpoint.scheme != "https"
            or not endpoint.hostname
            or endpoint.username
            or endpoint.query
            or endpoint.fragment
            or not self.token
        ):
            raise RuntimeError(
                "An authorized Terra HTTPS Responses endpoint with input token counting and server-side generation limits is required. No generation started."
            )
        self.http = build_opener(RejectRedirect())

    def post(self, path, body):
        req = Request(
            self.base + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.token},
        )
        with self.http.open(req, timeout=200) as response:
            return json.load(response)

    def payload(self, view):
        return {
            "model": MODEL,
            "instructions": "Return your desk transaction as JSON.",
            "input": json.dumps(view, ensure_ascii=False, separators=(",", ":")),
        }

    def count(self, view):
        return self.post("/responses/input_tokens", self.payload(view))["input_tokens"]

    def generate(self, view, limit):
        reply = self.post(
            "/responses",
            {
                **self.payload(view),
                "max_output_tokens": limit,
                "reasoning": {"effort": "medium"},
                "store": False,
            },
        )
        if reply["model"] != MODEL:
            raise ValueError("unexpected model; aborting study")
        return reply

    @staticmethod
    def action(reply):
        items = reply["output"]
        if any(i["type"] not in ("reasoning", "message") for i in items):
            raise ValueError("unexpected tool use")
        text = "".join(
            c["text"]
            for i in items
            if i["type"] == "message"
            for c in i["content"]
            if c["type"] == "output_text"
        ).strip()
        try:
            action = json.loads(text)
        except ValueError:
            return {}
        return action if isinstance(action, dict) else {}


class LoggedResponse:
    def __init__(self, stage, service=None):
        self.stage, self.service = stage, service

    def count(self, view):
        if self.service:
            value = self.service.count(view)
            save(self.stage / "count.json", {"view": view, "input_tokens": value})
            return value
        data = read(self.stage / "count.json")
        if view != data["view"]:
            raise ValueError("audit packet mismatch")
        return data["input_tokens"]

    def generate(self, view, limit):
        if self.service:
            reply = self.service.generate(view, limit)
            reply = {k: reply[k] for k in ("id", "model", "usage", "max_output_tokens", "output", "status")}
            reply["output"] = [
                {"type": "reasoning"} if item["type"] == "reasoning" else item for item in reply["output"]
            ]
            save(self.stage / "response.json", reply)
            return reply
        reply = read(self.stage / "response.json")
        if reply["model"] != MODEL:
            raise ValueError("audit model mismatch")
        return reply

    action = staticmethod(Responses.action)


def decide(key, wallet, packet, *, root, arm, final_ticket, audit, service):
    shared_booking = not final_ticket and key.startswith("reserve-")
    stage = root / (key if shared_booking else f"{arm}-{'next' if final_ticket else 'first'}-{key}")
    replay = audit or (shared_booking and stage.is_dir())
    if not replay:
        stage.mkdir()
    history = []

    def log(_, event):
        history.append(event)
        if not replay:
            save(stage / "ledger.json", history)

    action = wallet.turn(key, packet, LoggedResponse(stage, None if replay else service), log)
    if replay and history != read(stage / "ledger.json"):
        raise ValueError("audit ledger mismatch")
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--seed", type=int, default=461)
    parser.add_argument("--budget", type=int, default=mail_shift.INITIAL_TOKENS)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    limits = {
        "next_ticket_reserve": mail_shift.NEXT_TICKET_RESERVE,
        "input_limit": mail_shift.INPUT_LIMIT,
        "generation_limit": mail_shift.GENERATION_LIMIT,
        "model": MODEL,
    }
    if args.budget < 0:
        parser.error("budget must be nonnegative")
    try:
        service = None if args.audit else Responses()
    except RuntimeError as exc:
        parser.error(str(exc))
    if args.audit:
        design = read(args.root / "design.json")
        if any(design.get(k) != v for k, v in limits.items()):
            raise ValueError("audit model or token limits mismatch")
    else:
        args.root.mkdir(parents=True, exist_ok=False)
        arms = ["expire", "carry"]
        Random(args.seed).shuffle(arms)
        design = {**limits, "seed": args.seed, "budget": args.budget, "arms": arms}
        save(args.root / "design.json", design)
    w = swarm.shift(4, design["seed"], 8)
    result = {}
    for arm in design["arms"]:
        turn = partial(decide, root=args.root, arm=arm, audit=args.audit, service=service)

        accounts = {a: mail_shift.Account(design["budget"]) for a in swarm.actors(w)}
        first = mail_shift.run(w, accounts, arm == "carry", partial(turn, final_ticket=False))
        second = swarm.shift(4, design["seed"] + 100000, 8)
        next_accounts = {
            a: mail_shift.Account(mail_shift.NEXT_TICKET_RESERVE + first["next_ticket_credit"][a])
            for a in accounts
        }
        opening_balances = {desk: account.balance for desk, account in next_accounts.items()}
        followup = mail_shift.run(
            second, next_accounts, False, partial(turn, final_ticket=True), final_ticket=True
        )
        followup["carryover_spent"] = {
            desk: max(0, opening - followup["remaining"][desk] - mail_shift.NEXT_TICKET_RESERVE)
            for desk, opening in opening_balances.items()
        }
        result[arm] = {"first": first, "next": followup}
    if args.audit:
        if result != read(args.root / "results.json"):
            raise ValueError("audit mismatch")
    else:
        save(args.root / "results.json", result)


if __name__ == "__main__":
    main()
