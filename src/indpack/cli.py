"""Command line interface for indpack."""
import argparse
import json
import sys

from indpack.core import get_pid_args, get_ps_pids, parse_pid_args


def main(argv = None) -> int:
    parser = argparse.ArgumentParser(
        prog="indpack",
        description="Cross-platform process introspection tool",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("pids", help="List all running process IDs")

    args_parser = sub.add_parser("args", help="Show command line args for a PID")
    args_parser.add_argument("pid", help="Process ID to inspect")

    parse_parser = sub.add_parser("parse", help="Parse args for a PID into key-value pairs")
    parse_parser.add_argument("pid", help="Process ID to inspect")

    inspect_parser = sub.add_parser("inspect", help="Full inspection of all running processes")
    inspect_parser.add_argument(
        "-n", "--limit", type=int, default=0,
        help="Limit number of processes (0 = all)",
    )

    parsed = parser.parse_args(argv)

    if parsed.command is None:
        parser.print_help()
        return 1

    if parsed.command == "pids":
        return _cmd_pids()
    if parsed.command == "args":
        return _cmd_args(parsed.pid)
    if parsed.command == "parse":
        return _cmd_parse(parsed.pid)
    if parsed.command == "inspect":
        return _cmd_inspect(parsed.limit)

    return 0


def _cmd_pids() -> int:
    pids = get_ps_pids()
    for pid in sorted(pids, key=int):
        print(pid)
    return 0


def _cmd_args(pid: str) -> int:
    args = get_pid_args(pid)
    if not args:
        print(f"No arguments found for PID {pid}", file=sys.stderr)
        return 1
    for arg in args:
        print(arg)
    return 0


def _cmd_parse(pid: str) -> int:
    args = get_pid_args(pid)
    if not args:
        print(f"No arguments found for PID {pid}", file=sys.stderr)
        return 1
    parsed = parse_pid_args(args)
    print(json.dumps(parsed, indent=2))
    return 0


def _cmd_inspect(limit: int) -> int:
    pids = get_ps_pids()
    pids_sorted = sorted(pids, key=int)
    if limit > 0:
        pids_sorted = pids_sorted[:limit]

    results: dict[str, dict[str, object]] = {}
    for pid in pids_sorted:
        args = get_pid_args(pid)
        results[pid] = {
            "args": args,
            "parsed": parse_pid_args(args) if args else {},
        }

    print(json.dumps(results, indent=2))
    return 0
