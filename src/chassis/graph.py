"""Validate source-record relationships, independent of any renderer."""

from collections.abc import Iterable
from graphlib import CycleError, TopologicalSorter

from chassis.markdown import ParsedRecord, RecordFileError


def fail(item: ParsedRecord, message: str):
    raise RecordFileError(f"{item.path.as_posix()}: {message}")


def validate_graph(items: Iterable[ParsedRecord]) -> dict[str, ParsedRecord]:
    by_id = {}
    for item in items:
        identifier = item.record.id
        if identifier in by_id:
            fail(item, f"duplicate ID {identifier}; also in {by_id[identifier].path}")
        by_id[identifier] = item

    for item in by_id.values():
        record = item.record
        if record.type == "venture":
            if record.venture != record.id or record.parent is not None:
                fail(item, "venture must reference itself and have parent: null")
        else:
            venture = by_id.get(record.venture)
            if venture is None or venture.record.type != "venture":
                fail(item, f"venture {record.venture!r} must reference an existing venture")
            parent = by_id.get(record.parent)
            if parent is None:
                fail(item, f"parent {record.parent!r} does not exist")
            expected = "venture" if record.type in {"initiative", "agent"} else "initiative"
            if parent.record.type != expected:
                article = "an" if expected == "initiative" else "a"
                fail(item, f"parent must be {article} {expected}: {record.parent}")
            if parent.record.venture != record.venture:
                fail(item, f"parent {record.parent} belongs to a different venture")
        for dependency in record.depends_on:
            if dependency == record.id:
                fail(item, "a record cannot depend on itself")
            if dependency not in by_id:
                fail(item, f"dependency {dependency!r} does not exist")
            if record.type == "task" and by_id[dependency].record.type != "task":
                fail(item, f"dependency {dependency} must be a task")

    dependencies = {key: item.record.depends_on for key, item in by_id.items()}
    try:
        TopologicalSorter(dependencies).prepare()
    except CycleError as exc:
        cycle = exc.args[1]
        fail(by_id[cycle[0]], f"dependency cycle: {' -> '.join(cycle)}")
    return by_id
