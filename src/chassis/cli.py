"""Local commands for the Chassis vault."""

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from chassis.index import FILTER_FIELDS, RecordIndex
from chassis.errors import AuthorizationError, ConflictError, WriteError
from chassis.store import RecordStore
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
    update = commands.add_parser("update", help="Update a record using the configured agent identity")
    update.add_argument("identifier")
    update.add_argument("--expected-version", type=int, required=True)
    update.add_argument("--changes", required=True, help="JSON object of fields to change")
    create = commands.add_parser("create", help="Create a validated record")
    create.add_argument("type", choices=("venture", "initiative", "task"))
    create.add_argument("--fields", required=True, help="JSON object; omit type, version, updated_at")
    human = commands.add_parser("commit-human", help="Commit one manual record edit as the human")
    human.add_argument("path", type=Path)
    for command in (rebuild, listing, get, search, update, create, human):
        command.add_argument("--vault", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _validate(args.vault)
        if args.command in {"update", "create", "commit-human"}:
            print(json.dumps(_write(args), ensure_ascii=False, sort_keys=True, indent=2))
            return 0
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
    except WriteError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 3 if isinstance(exc, ConflictError) else 1
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


def _write(args) -> dict:
    store = RecordStore(args.vault)
    if args.command == "commit-human":
        return store.commit_human(args.path)
    agent = os.environ.get("CHASSIS_AGENT_ID", "").strip()
    if not agent:
        raise AuthorizationError("CHASSIS_AGENT_ID must identify the configured caller")
    if args.command == "update":
        return store.update_record(args.identifier, json.loads(args.changes), args.expected_version, agent)
    return store.create_record(args.type, json.loads(args.fields), agent)


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
