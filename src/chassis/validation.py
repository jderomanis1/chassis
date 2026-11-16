"""Validate the working-tree vault; no index or Git state is consulted."""

from pathlib import Path

from chassis.graph import validate_graph
from chassis.markdown import ParsedRecord, RecordFileError, read_record


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
    return validate_graph(records)
