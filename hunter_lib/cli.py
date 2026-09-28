"""hunter_lib CLI.

Usage:
  python -m hunter_lib.cli case open --target example.com
  python -m hunter_lib.cli case list
  python -m hunter_lib.cli evidence verify --case CASE-2026-0001
  python -m hunter_lib.cli evidence list   --case CASE-2026-0001
  python -m hunter_lib.cli monitor add  --case CASE-... --kind domain --value example.com --interval 60
  python -m hunter_lib.cli monitor list
  python -m hunter_lib.cli monitor alerts --days 7
  python -m hunter_lib.cli archive url --case CASE-... --url https://example.com
"""
from __future__ import annotations
import argparse
import json
import sys

from . import case_db
from . import evidence_log
from . import watchlist
from . import archiver


def cmd_case(args: argparse.Namespace) -> None:
    if args.op == "open":
        if not args.target:
            print("--target required", file=sys.stderr)
            sys.exit(2)
        print(case_db.open_case(target=args.target, scope_path=args.scope))
    elif args.op == "list":
        for row in case_db.list_cases(status=args.status):
            print("\t".join(map(str, row)))
    elif args.op == "close":
        if not args.case_id:
            print("--case-id required", file=sys.stderr)
            sys.exit(2)
        case_db.close_case(args.case_id)
        print(f"closed {args.case_id}")


def cmd_evidence(args: argparse.Namespace) -> None:
    if args.op == "verify":
        print(json.dumps(evidence_log.verify(args.case_id), indent=2))
    elif args.op == "list":
        for row in evidence_log.read_all(args.case_id):
            print(json.dumps(row))


def cmd_monitor(args: argparse.Namespace) -> None:
    if args.op == "add":
        if not (args.case_id and args.kind and args.value):
            print("--case / --kind / --value all required", file=sys.stderr)
            sys.exit(2)
        wid = watchlist.add(case_id=args.case_id, kind=args.kind, value=args.value, poll_interval_min=args.interval)
        print(wid)
    elif args.op == "list":
        for row in watchlist.list_active():
            print("\t".join(map(str, row)))
    elif args.op == "alerts":
        for row in watchlist.recent_alerts(days=args.days):
            print("\t".join(map(str, row)))
    elif args.op == "remove":
        if not args.watch_id:
            print("--watch-id required", file=sys.stderr)
            sys.exit(2)
        watchlist.remove(args.watch_id)
        print(f"removed {args.watch_id}")


def cmd_archive(args: argparse.Namespace) -> None:
    row = archiver.auto_capture(case_id=args.case_id, url=args.url, collected_by="cli", source_grade="A")
    print(json.dumps(row, indent=2))


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="hunter")
    s = p.add_subparsers(dest="sub", required=True)

    pc = s.add_parser("case", help="case lifecycle")
    pc.add_argument("op", choices=["open", "list", "close"])
    pc.add_argument("--target", default="")
    pc.add_argument("--scope", default="scope/scope.yaml")
    pc.add_argument("--status", default=None)
    pc.add_argument("--case-id", default=None)

    pe = s.add_parser("evidence", help="evidence ledger ops")
    pe.add_argument("op", choices=["verify", "list"])
    pe.add_argument("--case", dest="case_id", required=True)

    pm = s.add_parser("monitor", help="watchlist + alerts")
    pm.add_argument("op", choices=["add", "list", "alerts", "remove"])
    pm.add_argument("--case", dest="case_id", default=None)
    pm.add_argument("--kind", default=None)
    pm.add_argument("--value", default=None)
    pm.add_argument("--interval", type=int, default=60)
    pm.add_argument("--days", type=int, default=7)
    pm.add_argument("--watch-id", default=None)

    pa = s.add_parser("archive", help="chain-of-custody capture")
    pa.add_argument("op", choices=["url"])
    pa.add_argument("--case", dest="case_id", required=True)
    pa.add_argument("--url", required=True)

    args = p.parse_args(argv)
    dispatch = {"case": cmd_case, "evidence": cmd_evidence, "monitor": cmd_monitor, "archive": cmd_archive}
    dispatch[args.sub](args)


if __name__ == "__main__":
    main()
