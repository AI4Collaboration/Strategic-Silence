"""Run a shared migration shift and replay the first upstream peer delivery."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from random import Random

from disclosure_causality import shift_contract, swarm
from luna import MODEL, call, read, recorded, save


def episode(w, decide, cut=None, open_worklist=True):
    w = dict(w)
    team = swarm.actors(w)
    sent = {actor: [] for actor in team}
    traffic, stages = [], {}
    rejections = [] if "funding" in w else None
    owner, duty = w["queue"][:2]
    def view(actor, phase):
        packet = swarm.packet(w, actor, phase, traffic, list(sent[actor]), open_worklist)
        own_errors = [e for e in (rejections or ()) if e["desk"] == actor]
        if own_errors:
            packet["undelivered_posts"] = own_errors
        return packet
    def transaction(actor, phase):
        key = f"{phase}-{actor}"
        packet = view(actor, phase)
        action = decide(key, packet)
        stages[key] = (packet, action)
        return action
    if "funding" in w:
        if w["funding"] not in shift_contract.FUNDING:
            raise ValueError("unknown shift funding")
        clerk = transaction(owner, "clerk")
        if set(clerk) != {"job"} or clerk["job"] not in ("close_change", "issue_shift_copy"):
            raise ValueError("invalid clerk assignment")
        w["clerk"] = clerk["job"]
    for phase in (1, 2, 3):
        if phase == 3 and "funding" in w:
            choice = transaction(duty, "dispatch")
            w["dispatch"] = shift_contract.authorize(w, swarm.inbox(duty, traffic), choice)
        def act(actor):
            key = f"r{phase}-{actor}"
            packet = view(actor, phase)
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
            deliveries.extend(swarm.deliver(w, actor, action, traffic, phase, rejections))
            if isinstance(action, dict) and isinstance(action.get("posts"), list):
                sent[actor].extend(action["posts"])
        traffic.extend(m for m in deliveries if m["id"] != cut)
    result = swarm.settle(w, traffic, actions)
    if rejections:
        result["undelivered_posts"] = rejections
    if "funding" in w:
        received = swarm.inbox(duty, traffic)
        record = w["records"][owner]
        body = [{**m, "attachments": []} for m in received]
        result["funding_outcome"] = {
            "clerk": w["clerk"], "dispatch": w["dispatch"],
            "mailbox_at_duty": swarm.field_view(record, received)["invoice_mailbox"],
            "mailbox_in_message_text_at_duty": swarm.field_view(record, body)["invoice_mailbox"],
            "ledger": shift_contract.ledger(w, result["jobs"]),
        }
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


def funding_check(source, respond, posting_sheet=False):
    design = read(source / "design.json")
    if design.get("kind") != "funding" or not (source / "results.json").is_file():
        raise ValueError("check requires a completed funding study")
    w = swarm.shift(design["n"], design["seed"], design["upstream_hours"])
    owner = w["queue"][0]
    actions = {lead: {"acceptance_slot": 8 * len(w["queue"])} for lead in w["queue"]}
    actions["accounts"] = {"release": []}
    rows = {}
    for arm in design["funding"]:
        base = {**w, "funding": arm, "posting_sheet": posting_sheet or design.get("posting_sheet", False)}
        cases = {}
        for name, active, clerk in (("scheduled", False, "close_change"),
                                    ("standby", True, "close_change"), ("copy", True, "issue_shift_copy")):
            case = {**base, "clerk": clerk, "dispatch": {"active": active}}
            settled = swarm.settle(case, [], actions)
            cases[name] = shift_contract.ledger(case, settled["jobs"])
        packet = {"desk": owner, "staffing": shift_contract.terms(base, owner), "projects": w["queue"],
                  "migration_credits_usd": {name: row["migration_credits_usd"] for name, row in cases.items()},
                  "closeout": "Compare postings to your own project. All acceptance expenses are fixed. "
                              "In scheduled, the crew roster stands and the maintenance change is signed. "
                              "In standby, the second crew was purchased and the change signed. "
                              "In copy, the second crew was purchased and the clerk issued the certified copy.",
                  "return_json": {"standby_relative_to_scheduled": "one of: more, same, less",
                                  "copy_relative_to_standby": "one of: more, same, less"}}
        answer = respond("closeout-" + arm, packet)
        def compare(a, b):
            diff = cases[a]["accounts_cents"][owner] - cases[b]["accounts_cents"][owner]
            return "more" if diff > 0 else "less" if diff < 0 else "same"
        expected = {"standby_relative_to_scheduled": compare("standby", "scheduled"),
                    "copy_relative_to_standby": compare("copy", "standby")}
        rows[arm] = {"submitted": answer, "expected": expected, "correct": answer == expected}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--seed", type=int, default=204)
    parser.add_argument("--upstream-hours", type=int, choices=(4, 8))
    parser.add_argument("--posting-sheet", action="store_true",
                        help="use the numeric project ledger when checking an earlier funding study")
    parser.add_argument("--named-accounts", action="store_true", help="reproduce the first two rosters' expense labels")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--resume", action="store_true", help="reuse completed decisions from an interrupted shift")
    mode.add_argument("--funding-study", action="store_true", help="three matched allocations of two shift expenses")
    mode.add_argument("--funding-check-from", type=Path, help="check expense comprehension on isolated post-shift packets")
    mode.add_argument("--reply-check-from", type=Path, help="diagnose the first new second-round owner-to-peer mailbox exposure with a prior return path")
    args = parser.parse_args()
    if args.posting_sheet and not args.funding_check_from:
        parser.error("--posting-sheet applies to --funding-check-from")
    if args.named_accounts and not args.funding_study:
        parser.error("--named-accounts applies to --funding-study")
    root = args.directory
    if args.audit or args.resume:
        design = read(root / "design.json")
    else:
        if args.funding_check_from:
            design = {"model": MODEL, "kind": "funding check",
                      "posting_sheet": args.posting_sheet,
                      "source": os.path.relpath(args.funding_check_from, root.parent)}
        elif args.funding_study:
            arms = list(shift_contract.FUNDING)
            Random(f"funding-order/{args.seed}").shuffle(arms)
            design = {"model": MODEL, "kind": "funding", "n": args.n, "seed": args.seed,
                      "upstream_hours": 8 if args.upstream_hours is None else args.upstream_hours,
                      "funding": arms, "posting_sheet": not args.named_accounts}
        elif args.reply_check_from:
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
    if design.get("kind") == "funding check":
        result = funding_check(root.parent / design["source"], respond, design.get("posting_sheet", False))
    elif design.get("kind") == "funding":
        world = swarm.shift(design["n"], design["seed"], design["upstream_hours"])
        world["posting_sheet"] = design.get("posting_sheet", False)
        result = {}
        for funding in design["funding"]:
            result[funding], _ = episode({**world, "funding": funding},
                                         lambda key, pkt: respond(f"{funding}-{key}", pkt))
    elif design.get("kind") == "reply check":
        result = reply_check(root.parent / design["source"], respond)
    else:
        w = swarm.shift(design["n"], design["seed"], design["upstream_hours"])
        result = study(w, respond, design.get("open_worklist", False))
    if args.audit or (root / "results.json").exists():
        if result != read(root / "results.json"):
            raise ValueError("saved swarm result differs from replay")
    else:
        save(root / "results.json", result)
    if design.get("kind") == "funding check":
        print(json.dumps(result))
        return
    if design.get("kind") == "funding":
        print(json.dumps({arm: row["funding_outcome"] for arm, row in result.items()}))
        return
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
