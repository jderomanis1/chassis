"""Parse record frontmatter without rewriting the Markdown body."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from chassis.models import Record


class RecordFileError(ValueError):
    """A record error that includes the source filename."""


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            if key_node.tag != "tag:yaml.org,2002:str":
                raise ValueError("YAML keys must be strings; merge keys are not allowed")
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f"duplicate YAML key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass(frozen=True)
class ParsedRecord:
    path: Path
    record: Record
    body: str


def parse_record(text: str, path: Path) -> ParsedRecord:
    try:
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            raise ValueError("expected opening YAML frontmatter fence")
        end = next((i for i in range(1, len(lines))
                    if lines[i].rstrip("\r\n") == "---"), None)
        if end is None:
            raise ValueError("missing closing YAML frontmatter fence")
        fields = yaml.load("".join(lines[1:end]), Loader=UniqueKeyLoader)
        if not isinstance(fields, dict):
            raise ValueError("frontmatter must be a YAML mapping")
        record = Record.model_validate(fields)
        if path.stem != record.id:
            raise ValueError(f"filename must match record id {record.id}")
        return ParsedRecord(path, record, "".join(lines[end + 1:]))
    except (ValueError, yaml.YAMLError, ValidationError) as exc:
        raise RecordFileError(f"{path.as_posix()}: {exc}") from exc


def read_record(path: Path) -> ParsedRecord:
    try:
        with path.open(encoding="utf-8", newline="") as source:
            return parse_record(source.read(), path)
    except (OSError, UnicodeError) as exc:
        raise RecordFileError(f"{path.as_posix()}: {exc}") from exc


def read_frontmatter(path: Path) -> dict:
    """Read only the header for scope checks, without decoding or returning body text."""
    try:
        with path.open("rb") as source:
            if source.readline().rstrip(b"\r\n") != b"---":
                raise ValueError("expected opening YAML frontmatter fence")
            lines = []
            for line in source:
                if line.rstrip(b"\r\n") == b"---":
                    fields = yaml.load(b"".join(lines).decode("utf-8"), Loader=UniqueKeyLoader)
                    if not isinstance(fields, dict):
                        raise ValueError("frontmatter must be a YAML mapping")
                    return fields
                lines.append(line)
            raise ValueError("missing closing YAML frontmatter fence")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise RecordFileError(f"{path.as_posix()}: {exc}") from exc


def serialize_record(record: Record, body: str) -> bytes:
    """Normalize frontmatter and retain the supplied body byte for byte."""
    if not isinstance(body, str):
        raise ValueError("body must be a string")
    header = yaml.safe_dump(record.model_dump(mode="json"), sort_keys=False, allow_unicode=True)
    return f"---\n{header}---\n{body}".encode("utf-8")
