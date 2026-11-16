"""Local commands for the Chassis vault."""

import argparse
import sys
from collections import Counter
from pathlib import Path

from chassis.markdown import RecordFileError
from chassis.validation import load_vault


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chassis", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate all working-tree records")
    validate.add_argument("vault", type=Path, nargs="?", default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        records = load_vault(args.vault)
    except RecordFileError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    counts = Counter(item.record.type for item in records.values())
    dependencies = sum(len(item.record.depends_on) for item in records.values())
    print(f"VALID: {len(records)} records | {counts['venture']} ventures | "
          f"{counts['initiative']} initiatives | {counts['task']} tasks | "
          f"{dependencies} dependencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
