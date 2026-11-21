"""Run or audit crossed assignee/register conditions for migration deposit invoices."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from disclosure_causality import billing_rotation as rotation
from luna import read, save
from terra_rpc import TerraServer, rpc_answer


def ticket(root, model, seed, audit):
    path = root / f"ticket-{seed}"
    if not audit:
        path.mkdir()
    server = None if audit else TerraServer(path, model)

    def decide(stage, packet):
        destination = path / stage
        if server:
            return server.call(destination, packet)
        if read(destination / "input.json") != packet:
            raise ValueError(f"input mismatch at {destination}")
        action = rpc_answer(destination, model)
        if read(destination / "decision.json") != action:
            raise ValueError(f"decision mismatch at {destination}")
        return action

    try:
        rows = []
        for clerk, state in rotation.conditions(seed):
            cell = f"{clerk}-{state}"
            packet = rotation.sender_view(seed, clerk, state)
            action = decide(cell + "-handoff", packet)
            mail, errors = rotation.route(packet, action)
            close = decide(cell + "-close", rotation.finance_view(packet, mail))
            rows.append(rotation.score(packet, mail, errors, close))
        if audit:
            if rows != read(path / "outcomes.json"):
                raise ValueError(f"outcome mismatch at {path}")
        else:
            save(path / "outcomes.json", rows)
        return rows
    except Exception as error:
        if not audit:
            save(path / "failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        if server:
            server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--first-seed", type=int, default=701)
    parser.add_argument("--tickets", type=int, default=8)
    parser.add_argument("--model", default="gpt-6.1-terra")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.tickets < 1:
        parser.error("workers and tickets must be positive")
    if args.audit:
        design = read(args.root / "design.json")
    else:
        args.root.mkdir(parents=True, exist_ok=False)
        design = {"protocol": 1, "model": args.model,
                  "seeds": list(range(args.first_seed, args.first_seed + args.tickets))}
        save(args.root / "design.json", design)
    if design["protocol"] != 1:
        raise ValueError("unknown rotation protocol")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(ticket, args.root, design["model"], seed, args.audit) for seed in design["seeds"]]
        summary = rotation.summarize([f.result() for f in futures])
    if args.audit:
        if summary != read(args.root / "summary.json"):
            raise ValueError("summary mismatch")
        print(f"Verified {summary['tickets']} four-condition tickets.")
    else:
        save(args.root / "summary.json", summary)
        print(args.root / "summary.json")


if __name__ == "__main__":
    main()
