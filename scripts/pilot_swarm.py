"""Run a shared migration shift and replay the first upstream peer delivery."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path

from disclosure_causality import swarm
from luna import MODEL, call, read, recorded, save


def episode(w, decide, cut=None, open_worklist=True):
    team = swarm.actors(w)
    sent = {actor: [] for actor in team}
    traffic, stages = [], {}
    for phase in (1, 2, 3):
        def act(actor):
            key = f"r{phase}-{actor}"
            packet = swarm.packet(w, actor, phase, traffic, sent[actor].copy(), open_worklist)
            return key, packet, decide(key, packet)
        with ThreadPoolExecutor(max_workers=3) as pool:
            decisions = list(pool.map(act, team))
        actions = {}
        for actor, (key, packet, decision) in zip(team, decisions):
            stages[key] = (packet, decision)
            actions[actor] = decision
        if phase == 3:
            break
        deliveries = []
        for actor, action in actions.items():
            deliveries.extend(swarm.deliver(w, actor, action, traffic, phase))
            sent[actor].extend(action["posts"])
        traffic.extend(m for m in deliveries if m["id"] != cut)
    result = swarm.settle(w, traffic, actions)
    return {"deliveries": traffic, "actions": actions, **result}, stages


def study(w, interact, open_worklist=True):
    natural, saved = episode(w, lambda key, packet: interact("natural-" + key, packet), open_worklist=open_worklist)
    order = w["queue"]
    edge = next((m for m in natural["deliveries"] if m["id"].startswith("1/") and
                 m["from"] in order and m["to"] in order and order.index(m["from"]) < order.index(m["to"])), None)
    results = {"natural": natural, "cut_edge": edge["id"] if edge else None}
    if edge is None:
        return results
    requery = set()
    for branch in ("cut", "sham"):
        def decide(key, packet):
            old, decision = saved[key]
            if packet == old and not (branch == "sham" and key in requery):
                return decision
            if branch == "cut":
                requery.add(key)
            return interact(branch + "-" + key, packet)
        result, _ = episode(w, decide, cut=edge["id"] if branch == "cut" else None, open_worklist=open_worklist)
        results[branch] = result
    results["cut_requeried"] = sorted(requery)
    return results


def reply_check(source, respond):
    source_design = read(source / "design.json")
    w = swarm.shift(source_design["n"], source_design["seed"], source_design["upstream_hours"])
    natural, decisions = episode(w, lambda key, pkt: recorded(source, "natural-" + key, pkt),
                                 open_worklist=source_design.get("open_worklist", False))
    if natural != read(source / "results.json")["natural"]:
        raise ValueError("parent episode differs from source")
    traffic = natural["deliveries"]
    first = [m for m in traffic if m["id"].startswith("1/")]
    for m in traffic:
        owner, peer = m["from"], m["to"]
        if (not m["id"].startswith("2/") or owner == peer or owner not in w["records"]
                or peer not in w["records"]):
            continue
        record = w["records"][owner]
        if (not swarm.field_view(record, [m])["invoice_mailbox"]
                or swarm.field_view(record, swarm.inbox(peer, first))["invoice_mailbox"]):
            continue
        incoming = next((q for q in first if q["from"] == peer and q["to"] == owner), None)
        if incoming is None:
            continue
        original, _ = decisions["r2-" + owner]
        def one(job):
            rep, arm = job
            keep = first if arm == "intact" else [q for q in first if q["id"] != incoming["id"]]
            pkt = {**original, "received": swarm.inbox(owner, keep),
                   "available_records": list(swarm.documents(w, owner, swarm.inbox(owner, keep)))}
            action = respond(f"r{rep}-{arm}", pkt)
            sent = swarm.deliver(w, owner, action, keep, 2)
            return {"repeat": rep, "arm": arm, "action": action,
                    "mailbox_delivered": swarm.field_view(record, swarm.inbox(peer, sent))["invoice_mailbox"]}
        with ThreadPoolExecutor(max_workers=3) as pool:
            rows = list(pool.map(one, [(i,a) for i in (1,2,3) for a in ("intact","cut")]))
        return {"source_reply": m["id"], "tested_delivery": incoming["id"], "rows": rows,
                "exposures": {a: sum(r["mailbox_delivered"] for r in rows if r["arm"] == a) for a in ("intact","cut")}}
    return {"source_reply": None, "rows": [], "exposures": {}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--seed", type=int, default=204)
    parser.add_argument("--upstream-hours", type=int, choices=(4, 8))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--resume", action="store_true", help="reuse completed decisions from an interrupted shift")
    mode.add_argument("--reply-check-from", type=Path, help="diagnose the first new second-round owner-to-peer mailbox exposure with a prior return path")
    args = parser.parse_args()
    root = args.directory
    if args.audit or args.resume:
        design = read(root / "design.json")
    else:
        if args.reply_check_from:
            design = {"model": MODEL, "source": os.path.relpath(args.reply_check_from, root.parent),
                      "kind": "reply check", "repeats": 3, "selection": "first newly exposed owner mailbox in a reply to a first-round correspondent"}
        else:
            design = {"model": MODEL, "n": args.n, "seed": args.seed, "upstream_hours": args.upstream_hours,
                      "open_worklist": True, "rounds": 2,
                      "cut_rule": "first round-one delivery from an earlier to a later crew job, in queue and post order",
                      "sham_rule": "retain delivery and resample the actors queried in cut, plus any actors whose inputs change"}
        root.mkdir(parents=True, exist_ok=False)
        save(root / "design.json", design)
    def respond(key, packet):
        if args.audit or (args.resume and (root / key).exists()):
            return recorded(root, key, packet)
        return call(root, key, packet)
    if design.get("kind") == "reply check":
        result = reply_check(root.parent / design["source"], respond)
    else:
        w = swarm.shift(design["n"], design["seed"], design["upstream_hours"])
        result = study(w, respond, design.get("open_worklist", False))
    if args.audit or (root / "results.json").exists():
        if result != read(root / "results.json"):
            raise ValueError("saved swarm result differs from replay")
    else:
        save(root / "results.json", result)
    if design.get("kind") == "reply check":
        print(json.dumps(result["exposures"]))
        return
    summary = {}
    for branch in ("natural", "cut", "sham"):
        if branch in result:
            r = result[branch]
            summary[branch] = {s: r[s] for s in ("invoices_sent", "bookings_completed", "booking_cost")}
            summary[branch].update(swarm.communication_counts(r["deliveries"], r["jobs"]))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
