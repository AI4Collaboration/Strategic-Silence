"""Matched Terra transactions for the shared migration crew."""
import argparse
from copy import deepcopy
from pathlib import Path
from random import Random

from disclosure_causality import shift_contract, swarm
from luna import read, recorded, save
from pilot_swarm import episode
from terra_rpc import TerraServer, rpc_answer

MODEL = "gpt-6.1-terra"


def calibration(w, arm, decide):
    """Separate purchase terminal with two firm quotes and accepted documents."""
    owner = w["queue"][0]
    quotes, outcomes = {}, {}
    actions = {p: {"acceptance_slot": 8 * len(w["queue"])} for p in w["queue"]}
    actions["accounts"] = {"release": []}
    for option in ("scheduled", "standby"):
        case = {**w, "funding": arm, "clerk": "close_change",
                "dispatch": {"active": option == "standby", "eligible_records": [owner]}}
        ledger = shift_contract.ledger(case, swarm.settle(case, [], actions)["jobs"])
        quotes[option] = {"your_project_usd": ledger["accounts_cents"][owner]/100,
                          "provider_total_usd": ledger["total_cents"]/100}
        outcomes[option] = ledger
    pkt = {"desk": owner, "responsibility": "Project budget", "purchase_quotes": quotes,
           "service": ("Same opening migration. Quotes include staffing and resulting acceptance expenses."
                       if w.get("purchase_limit") else "Same opening migration and client appointment. Both quotes approved."),
           "return_json": {"purchase": "scheduled | standby"}}
    decision = decide(arm, pkt)["purchase"]
    return {"choice": decision, "posted": outcomes[decision]["accounts_cents"][owner],
            "cheapest_chosen": quotes[decision]["your_project_usd"] == min(q["your_project_usd"] for q in quotes.values())}


def restore(source, decide):
    design = read(source / "design.json")
    arm = "project_standby"
    w = {**swarm.shift(4, design["seed"], 8), "funding": arm, "compact": True,
         "purchase_limit": design["purchase_limit"], "callout": design.get("callout", False)}
    owner, duty = w["queue"][:2]
    original = read(source / "results.json")[arm]
    w["clerk"] = original["funding_outcome"]["clerk"]
    directory = source / f"{arm}-dispatch-{duty}"
    packet = read(directory / "input.json")
    if rpc_answer(directory, design["model"]) != read(directory / "decision.json"):
        raise ValueError("source decision mismatch")
    notes = {"intact": None, "status": "Opening job in progress.", "hours": "Opening job requires eight crew hours."}
    rows = []
    for rep in range(3):
        for label, note in notes.items():
            view = deepcopy(packet)
            mail = view.setdefault("received", [])
            if note:
                mail.append({"id": f"2/{owner}/supplement/{duty}", "from": owner, "to": duty,
                             "message": note, "attachments": []})
            choice = decide(f"{rep}-{label}", view)
            w["dispatch"] = shift_contract.authorize(w, mail, choice)
            settled = swarm.settle(w, original["deliveries"], original["actions"])
            rows.append({"arm": label, "standby": w["dispatch"]["active"],
                         "migration_credits_usd": shift_contract.ledger(w, settled["jobs"])["migration_credits_usd"]})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--seed", type=int, default=411)
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--purchase-limit", action="store_true")
    parser.add_argument("--quotes", action="store_true", help="show post-purchase project balances")
    parser.add_argument("--callout", action="store_true", help="charge the on-call premium to the originating project")
    parser.add_argument("--private-booking", action="store_true", help="opening lead books its own client before mail")
    parser.add_argument("--restore-from", type=Path, help="replay the duty lead after a fact omission")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.audit or args.resume:
        design = read(args.root / "design.json")
    else:
        args.root.mkdir(parents=True, exist_ok=False)
        arms = list(shift_contract.FUNDING[:2] if args.calibrate else shift_contract.FUNDING)
        Random(args.seed).shuffle(arms)
        design = {"model": MODEL, "transport": "app-server", "seed": args.seed, "arms": arms, "calibrate": args.calibrate,
                  "purchase_limit": args.purchase_limit or args.quotes or args.callout,
                  "quotes": args.quotes or args.callout, "callout": args.callout}
        if args.private_booking:
            design.update(private_booking=True, quotes=True, callout=True, purchase_limit=True)
        if args.restore_from:
            design["source"] = str(args.restore_from.resolve())
        save(args.root / "design.json", design)
    if not args.audit and design.get("transport") != "app-server":
        parser.error("start a new app-server roster to keep transports separate")
    server = None if args.audit else TerraServer(args.root, design["model"])
    def decide(key, pkt):
        stage = args.root / key
        if stage.exists():
            if (stage / "decision.json").is_file():
                if design.get("transport") != "app-server":
                    return recorded(args.root, key, pkt)
                answer = rpc_answer(stage, design["model"])
                if answer != read(stage / "decision.json") or pkt != read(stage / "input.json"):
                    raise ValueError(f"replay mismatch: {key}")
                return answer
            if args.audit or not args.resume or read(stage / "input.json") != pkt:
                raise ValueError(f"incomplete or mismatched stage: {key}")
            attempt = 1
            while (args.root / f"{key}.failed-{attempt}").exists():
                attempt += 1
            stage.rename(args.root / f"{key}.failed-{attempt}")
        if args.audit:
            raise ValueError(f"missing stage: {key}")
        return server.call(stage, pkt)
    w = swarm.shift(4, design["seed"], 8)
    w["purchase_limit"] = design.get("purchase_limit", False)
    w["quotes"] = design.get("quotes", False)
    w["callout"] = design.get("callout", False)
    w["private_booking"] = design.get("private_booking", False)
    results = {}
    try:
        if "source" in design:
            results = restore(Path(design["source"]), decide)
        for arm in ([] if "source" in design else design["arms"]):
            if design["calibrate"]:
                results[arm] = calibration(w, arm, decide)
            else:
                results[arm], _ = episode({**w, "funding": arm, "compact": True, "posting_sheet": True},
                                          lambda key, pkt: decide(key if key.startswith("reserve-") else f"{arm}-{key}", pkt))
    finally:
        if server:
            server.close()
    if args.audit:
        if results != read(args.root / "results.json"):
            raise ValueError("replay mismatch")
    else:
        save(args.root / "results.json", results)
    if "source" in design:
        print(results)
    else:
        print({a: r if design["calibrate"] else r["funding_outcome"]["mailbox_at_duty"] for a, r in results.items()})


if __name__ == "__main__":
    main()
