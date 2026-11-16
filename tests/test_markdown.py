from pathlib import Path

import pytest

from chassis.markdown import RecordFileError, parse_record

HEADER = """---
id: venture-ridgeview
type: venture
title: Ridgeview HOA
status: planned
owner: Morgan Vale
venture: venture-ridgeview
parent: null
next_step: Review the sample plan.
updated_at: 2026-11-16T12:00:00Z
version: 1
---
"""
PATH = Path("records/ventures/venture-ridgeview.md")


def test_frontmatter_parses_and_body_is_preserved():
    body = "\n# Sample\n\n---\n\n  Preserve this spacing.\n"
    parsed = parse_record(HEADER + body, PATH)
    assert parsed.record.id == "venture-ridgeview"
    assert parsed.body == body
    assert parsed.path == PATH


@pytest.mark.parametrize(("text", "reason"), [
    ("# Missing frontmatter\n", "opening YAML frontmatter fence"),
    ("---\ntitle: missing end fence\n", "closing YAML frontmatter fence"),
    ("---\n- not a mapping\n---\n", "YAML mapping"),
    ("---\n[\n---\n", "expected the node content"),
    (HEADER.replace("version: 1", "version: 1\nversion: 2"), "duplicate YAML key"),
    (HEADER.replace("version: 1", "version: true"), "version"),
    (HEADER.replace("version: 1", "version: !!python/object:builtins.object {}"),
     "could not determine a constructor"),
    (HEADER.replace("owner: Morgan Vale\n", ""), "owner"),
    (HEADER.replace("owner: Morgan Vale", "owner: {<<: {name: Morgan}}"), "merge keys"),
])
def test_invalid_frontmatter_has_file_context(text, reason):
    with pytest.raises(RecordFileError, match=reason) as exc:
        parse_record(text, PATH)
    assert PATH.as_posix() in str(exc.value)


def test_filename_must_match_immutable_id():
    with pytest.raises(RecordFileError, match="filename must match record id"):
        parse_record(HEADER, Path("wrong-name.md"))


def test_windows_line_endings_are_accepted_without_changing_body():
    body = "\r\n# A Windows note\r\n"
    assert parse_record(HEADER.replace("\n", "\r\n") + body, PATH).body == body


def test_duplicate_key_has_clear_error():
    with pytest.raises(RecordFileError, match="duplicate YAML key: status"):
        parse_record(HEADER.replace("status: planned", "status: planned\nstatus: done"), PATH)
