"""Shared-resource experiments; model participants are dispatched externally."""
import argparse
import json
from pathlib import Path

from .runner import initialize, advance, archive, replay, fork, next_window
from .validation import offline


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("path", type=Path)
    init.add_argument("--n", type=int, default=4)
    init.add_argument("--seed", type=int, default=0)
    init.add_argument("--clean", action="store_true")
    init.add_argument("--objective", choices=["shared", "client"], default="shared")
    init.add_argument("--label-access", choices=["office", "team"], default="office")
    init.add_argument("--reporting", choices=["truthful", "general", "specific"], default="truthful")
    init.add_argument("--liability", choices=["project", "office"])
    init.add_argument("--funds", choices=["none", "joint", "protected"])
    init.add_argument("--audience", choices=["office", "team"])
    init.add_argument("--protocol", type=int, choices=range(1, 12), default=8)
    step = sub.add_parser("advance")
    step.add_argument("path", type=Path)
    validation = sub.add_parser("offline")
    validation.add_argument("--output", type=Path, default=Path("output/offline"))
    validation.add_argument("--funds", choices=["none", "joint", "protected"])
    validation.add_argument("--protocol", type=int, choices=[7, 8, 9, 10, 11], default=8)
    check = sub.add_parser("replay")
    check.add_argument("path", type=Path)
    save = sub.add_parser("archive")
    save.add_argument("destination", type=Path)
    save.add_argument("paths", type=Path, nargs="+")
    branch = sub.add_parser("fork")
    branch.add_argument("source", type=Path)
    branch.add_argument("destination", type=Path)
    branch.add_argument("--condition", choices=["none", "required", "unrelated"], required=True)
    branch.add_argument("--owner", required=True)
    branch.add_argument("--recipient", help="restore to this peer after allocation, before acceptance confirmation")
    window = sub.add_parser("next-window")
    window.add_argument("source", type=Path)
    window.add_argument("destination", type=Path)
    window.add_argument("--clean", action="store_true")
    window.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    if args.command == "init":
        args.funds = args.funds or ("joint" if args.protocol >= 8 else "none")
        args.audience = args.audience or ("team" if args.protocol >= 8 else "office")
        args.liability = args.liability or ("office" if args.protocol >= 8 else "project")
        run = initialize(args.path, n=args.n, seed=args.seed, overrun=not args.clean, objective=args.objective,
                         label_access=args.label_access, reporting=args.reporting, liability=args.liability, funds=args.funds,
                         audience=args.audience, protocol=args.protocol)
        result = {"stage": run["stage"], "actors": list(run["world"]["projects"])}
    elif args.command == "advance":
        run = advance(args.path)
        result = {"stage": run["stage"], "final": run.get("final")}
    elif args.command == "offline":
        report = offline(args.output, funds=args.funds or ("joint" if args.protocol >= 8 else "none"), protocol=args.protocol)
        result = {k: report[k] for k in ("passed", "cases", "executions", "replay")}
    elif args.command == "archive":
        result = archive(args.paths, args.destination)
    elif args.command == "fork":
        run = fork(args.source, args.destination, args.condition, args.owner, args.recipient)
        result = {"stage": run["stage"]}
    elif args.command == "next-window":
        run = next_window(args.source, args.destination, overrun=not args.clean, seed=args.seed)
        result = {"stage": run["stage"], "window": len(run["config"]["history"]["scheduler"]) + 1}
    else:
        result = replay(args.path)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("passed", True) else 1
