"""Repeat a paired handoff with the same owner booking and incoming peer mail."""

import argparse
from pathlib import Path
from random import Random

from luna import read, save
from pilot_stated_budget import MODEL, episode
from terra_rpc import TerraServer, rpc_answer

from disclosure_causality import mail_shift, swarm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    design = read(args.source / "design.json")
    original = episode(args.source, design, None)
    if original != read(args.source / "results.json"):
        raise ValueError("source mismatch")
    w = swarm.shift(4, design["seed"], 8)
    owner, peer = w["queue"][:2]
    if design["protocol"] < 2:
        raise ValueError("requires a change-case comparison")
    w["records"][peer]["shift"]["remaining_crew_hours"] = 4
    first = read(args.source / f"central-mail1-{owner}" / "input.json")
    second = read(args.source / f"central-mail2-{owner}" / "input.json")
    w.update(
        change_queue=first["service_desk"],
        reservation_invoice="case_thread" in first,
        case_console="published_handoff" in first,
    )
    incoming = [m for m in second["received"] if m["from"] != owner]
    if not args.audit:
        args.root.mkdir(parents=True, exist_ok=False)
    server = None if args.audit else TerraServer(args.root, MODEL)
    rows = []
    rng = Random(design["seed"])
    try:
        for rep in range(4):
            arms = ["central", "project"]
            rng.shuffle(arms)
            for arm in arms:
                sent = []
                history = []
                windows = (first,) if "closing_times" in first else (first, second)
                for window, base in enumerate(windows, 1):
                    case = {
                        **base["service_desk"],
                        "case_owner": owner if arm == "project" else "central service desk",
                    }
                    view = {
                        **base,
                        "service_desk": case,
                        "received": [] if window == 1 else incoming + swarm.inbox(owner, sent),
                        "own_posts": list(history),
                    }
                    if "your_desk_forecast" in base:
                        source = args.source / f"{arm}-mail{window}-{owner}" / "input.json"
                        view["your_desk_forecast"] = read(source)["your_desk_forecast"]
                    stage = args.root / f"{rep}-{arm}-mail{window}"
                    if server:
                        action = server.call(stage, view)
                    else:
                        action = rpc_answer(stage, MODEL)
                        if read(stage / "input.json") != view or read(stage / "decision.json") != action:
                            raise ValueError("sender audit mismatch")
                    errors = []
                    mail = mail_shift.deliver_update(w, owner, action, view["received"], window, errors)
                    history.extend(errors)
                    history.extend(
                        {
                            "to": m["to"],
                            "message": m["message"],
                            "documents": [d["ref"] for d in m["attachments"]],
                        }
                        for m in mail
                    )
                    sent.extend(mail)
                rows.append({"repeat": rep, "arm": arm, "received_by_next_desk": swarm.inbox(peer, sent)})
    finally:
        if server:
            server.close()
    if args.audit:
        if rows != read(args.root / "results.json"):
            raise ValueError("sender result mismatch")
    else:
        save(args.root / "results.json", rows)


if __name__ == "__main__":
    main()
