"""Replay one receiver's closing transaction after a single fact is restored or removed."""

import argparse
import json
from copy import deepcopy
from pathlib import Path
from random import Random

from luna import read, save
from pilot_stated_budget import MODEL, episode
from terra_rpc import TerraServer, rpc_answer

from disclosure_causality import mail_shift, swarm


def views(packet, world, owner, recipient, fact):
    original = deepcopy(packet)
    if fact == "redact":
        address = world["records"][owner]["account"]["invoice_mailbox"]
        encoded = json.dumps(original)
        if address not in encoded:
            raise ValueError("source recipient never saw that mailbox")
        return {"intact": original, "redacted": json.loads(encoded.replace(address, ""))}
    address = world["records"][owner]["account"]["invoice_mailbox"]
    if fact == "mailbox" and address in json.dumps(original):
        raise ValueError("mailbox already delivered")
    if fact == "hours" and (owner != world["queue"][0] or recipient != world["queue"][1]):
        raise ValueError("hours replay requires the opening owner and next desk")
    window = 1 if "closing_times" in original and recipient == world["queue"][1] else 2
    repaired = f"{owner} needs eight crew hours." if fact == "hours" else address
    result = {"intact": original}
    for label, note in [("sham", f"{owner} work order on file."), ("repair", repaired)]:
        view = deepcopy(original)
        view["received"].append(
            {
                "id": f"{window}/{owner}/supplement/{recipient}",
                "from": owner,
                "to": recipient,
                "message": note,
                "attachments": [],
            }
        )
        if fact == "mailbox" and label == "repair" and isinstance(view["billing_outbox"], dict):
            view["billing_outbox"][owner]["destination"] = address
        result[label] = view
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--fact", choices=["hours", "mailbox", "redact"], required=True)
    p.add_argument("--owner")
    p.add_argument("--recipient")
    p.add_argument("--audit", action="store_true")
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    d = read(args.source / "design.json")
    evidence = episode(args.source, d, None)
    if evidence != read(args.source / "results.json"):
        raise ValueError("source audit mismatch")
    row = evidence[args.arm]
    w = swarm.shift(4, d["seed"], 8)
    if d["protocol"] >= 2:
        w["records"][w["queue"][1]]["shift"]["remaining_crew_hours"] = 4
    owner = args.owner or w["queue"][0]
    recipient = args.recipient or ("accounts" if args.fact == "mailbox" else w["queue"][1])
    packet = read(args.source / (args.arm + "-close-" + recipient) / "input.json")
    variants = views(packet, w, owner, recipient, args.fact)
    if not args.audit and not args.resume:
        args.root.mkdir(parents=True, exist_ok=False)
    config = {
        "source": args.source.name,
        "arm": args.arm,
        "owner": owner,
        "recipient": recipient,
        "fact": args.fact,
        "repeats": 3,
    }
    if args.audit or args.resume:
        if config != read(args.root / "design.json"):
            raise ValueError("replay design mismatch")
    else:
        save(args.root / "design.json", config)
    server = None if args.audit else TerraServer(args.root, MODEL)
    outcomes = []
    try:
        order = [(n, label) for n in range(3) for label in variants]
        Random(d["seed"]).shuffle(order)
        for n, label in order:
            stage = args.root / f"{n}-{label}"
            view = variants[label]
            if args.audit or (args.resume and stage.exists()):
                choice = rpc_answer(stage, MODEL)
                if view != read(stage / "input.json") or choice != read(stage / "decision.json"):
                    raise ValueError("replay input or action mismatch")
            else:
                choice = server.call(stage, view)
            actions = deepcopy(row["actions"])
            actions[recipient] = (
                mail_shift.invoice_action(choice, w["queue"])
                if recipient == "accounts"
                else mail_shift.calendar_action(choice, packet["available_hours"])
            )
            earlier = {m["id"] for m in packet["received"]}
            traffic = [m for m in row["deliveries"] if m["id"] not in earlier] + view["received"]
            jobs = swarm.settle(w, traffic, actions)["jobs"]
            outcomes.append(
                {
                    "arm": label,
                    "repeat": n,
                    "action": choice,
                    "invoice": jobs[owner]["invoice"],
                    "booking": jobs[recipient]["booking"] if recipient != "accounts" else None,
                }
            )
    finally:
        if server:
            server.close()
    if args.audit:
        if outcomes != read(args.root / "results.json"):
            raise ValueError("outcome mismatch")
    else:
        save(args.root / "results.json", outcomes)


if __name__ == "__main__":
    main()
