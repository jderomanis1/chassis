"""Local commands for the Chassis vault."""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from chassis.index import FILTER_FIELDS, RecordIndex
from chassis.validation import load_vault


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chassis", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate all working-tree records")
    validate.add_argument("vault", type=Path, nargs="?", default=Path.cwd())
    index = commands.add_parser("index", help="Manage the disposable SQLite index")
    actions = index.add_subparsers(dest="index_command", required=True)
    rebuild = actions.add_parser("rebuild", help="Rebuild from authoritative working-tree files")
    listing = commands.add_parser("list", help="List records matching all supplied filters")
    choices = {"type": ("venture", "initiative", "task"),
               "status": ("planned", "in_progress", "blocked", "done"),
               "sensitivity": ("normal", "restricted")}
    for field in FILTER_FIELDS:
        listing.add_argument("--" + field.replace("_", "-"), default=argparse.SUPPRESS,
                             choices=choices.get(field),
                             help="Exact match; use null for unassigned/no parent" if field in {
                                 "parent", "assigned_agent"} else "Exact match")
    get = commands.add_parser("get", help="Read a complete record by ID")
    get.add_argument("identifier")
    search = commands.add_parser("search", help="Search title, next_step, and body")
    search.add_argument("query")
    for command in (rebuild, listing, get, search):
        command.add_argument("--vault", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _validate(args.vault)
        index = RecordIndex(args.vault)
        if args.command == "index":
            print(f"INDEXED: {index.rebuild()} records | {index.path}")
            return 0
        if args.command == "list":
            filters = {field: value for field, value in vars(args).items() if field in FILTER_FIELDS}
            for field in ("parent", "assigned_agent"):
                if filters.get(field) == "null":
                    filters[field] = None
            result = index.list_records(filters)
        elif args.command == "get":
            result = index.get_record(args.identifier)
            if result is None:
                print(f"NOT FOUND: {args.identifier}", file=sys.stderr)
                return 1
        else:
            result = index.search(args.query)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


def _validate(root: Path) -> int:
    records = load_vault(root)
    counts = Counter(item.record.type for item in records.values())
    dependencies = sum(len(item.record.depends_on) for item in records.values())
    print(f"VALID: {len(records)} records | {counts['venture']} ventures | "
          f"{counts['initiative']} initiatives | {counts['task']} tasks | "
          f"{dependencies} dependencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
