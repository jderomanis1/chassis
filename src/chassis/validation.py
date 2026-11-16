"""Validate the working-tree vault; no index or Git state is consulted."""

from pathlib import Path

from chassis.graph import fail, validate_graph
from chassis.markdown import ParsedRecord, RecordFileError, read_record
from chassis.policy import load_policy


def load_vault(root: Path) -> dict[str, ParsedRecord]:
    record_root = root / "records"
    if record_root.is_symlink():
        raise RecordFileError(f"{record_root}: record directory cannot be a symlink")
    records = []
    for path in sorted(record_root.rglob("*")):
        if path.is_symlink():
            raise RecordFileError(f"{path}: record paths cannot be symlinks")
        if not path.is_file() or path.suffix != ".md":
            continue
        item = read_record(path)
        expected = Path(f"{item.record.type}s") / f"{item.record.id}.md"
        if path.relative_to(record_root) != expected:
            raise RecordFileError(f"{path}: expected records/{expected.as_posix()}")
        records.append(item)
    if not records:
        raise RecordFileError(f"{record_root}: No record files found")
    by_id = validate_graph(records)
    policy = load_policy(root)
    for item in records:
        agent = item.record.assigned_agent
        if agent is not None and agent not in policy.agents:
            fail(item, f"assigned_agent {agent!r} is not a known agent id")
    return by_id
