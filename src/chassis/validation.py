"""Validate the working-tree vault; no index or Git state is consulted."""

from pathlib import Path
from collections.abc import Callable, Iterable

from chassis.graph import fail, validate_graph
from chassis.markdown import ParsedRecord, RecordFileError, read_record
from chassis.policy import Policy, load_policy, validate_policy_references


def read_vault(root: Path, *, reader: Callable[[Path], ParsedRecord] = read_record) -> list[ParsedRecord]:
    """Read schemas/paths without checking relationships until a proposal is complete."""
    record_root = root / "records"
    if record_root.is_symlink():
        raise RecordFileError(f"{record_root}: record directory cannot be a symlink")
    records = []
    for path in sorted(record_root.rglob("*")):
        if path.is_symlink():
            raise RecordFileError(f"{path}: record paths cannot be symlinks")
        if not path.is_file() or path.suffix != ".md":
            continue
        item = reader(path)
        expected = Path(f"{item.record.type}s") / f"{item.record.id}.md"
        if path.relative_to(record_root) != expected:
            raise RecordFileError(f"{path}: expected records/{expected.as_posix()}")
        records.append(item)
    if not records:
        raise RecordFileError(f"{record_root}: No record files found")
    return records


def validate_records(root: Path, items: Iterable[ParsedRecord], policy: Policy) -> dict[str, ParsedRecord]:
    records = list(items)
    by_id = validate_graph(records)
    validate_policy_references(root, policy, by_id)
    for item in records:
        agent = item.record.assigned_agent
        if agent is not None and agent not in policy.agents:
            fail(item, f"assigned_agent {agent!r} is not a known agent id")
    return by_id


def load_vault(root: Path, *, reader: Callable[[Path], ParsedRecord] = read_record) -> dict[str, ParsedRecord]:
    return validate_records(root, read_vault(root, reader=reader), load_policy(root))
