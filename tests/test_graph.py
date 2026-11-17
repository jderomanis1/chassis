from pathlib import Path

import pytest

from chassis.graph import validate_graph
from chassis.markdown import ParsedRecord, RecordFileError
from chassis.models import Record


def note(identifier, kind, venture, parent=None, depends=()):
    record = Record(id=identifier, type=kind, title=identifier, status="planned",
                    owner="Morgan Vale", venture=venture, parent=parent,
                    next_step="Review sample work.", updated_at="2026-11-16T12:00:00Z",
                    version=1, depends_on=list(depends))
    return ParsedRecord(Path(f"records/{kind}s/{identifier}.md"), record, "")


@pytest.fixture
def graph():
    return [note("venture-ridgeview", "venture", "venture-ridgeview"),
            note("initiative-maintenance", "initiative", "venture-ridgeview", "venture-ridgeview"),
            note("task-inventory", "task", "venture-ridgeview", "initiative-maintenance"),
            note("task-quotes", "task", "venture-ridgeview", "initiative-maintenance", ["task-inventory"])]


def replace(items, index, **changes):
    old = items[index]
    items[index] = ParsedRecord(old.path, Record.model_validate(old.record.model_dump() | changes), old.body)


def test_valid_relationships(graph):
    assert set(validate_graph(graph)) == {item.record.id for item in graph}


@pytest.mark.parametrize(("index", "changes", "reason"), [
    (0, {"parent": "initiative-maintenance"}, "parent: null"),
    (0, {"venture": "venture-other"}, "reference itself"),
    (1, {"parent": None}, "parent"),
    (1, {"parent": "task-inventory"}, "parent must be a venture"),
    (2, {"parent": "venture-ridgeview"}, "parent must be an initiative"),
    (2, {"parent": "initiative-missing"}, "initiative-missing"),
    (2, {"venture": "venture-missing"}, "venture-missing"),
    (2, {"depends_on": ["task-missing"]}, "invalid dependency"),
    (2, {"depends_on": ["task-inventory"]}, "depend on itself"),
    (2, {"depends_on": ["task-quotes"]}, "dependency cycle"),
    (2, {"depends_on": ["initiative-maintenance"]}, "must be a task"),
])
def test_invalid_graph_names_file_and_reason(graph, index, changes, reason):
    replace(graph, index, **changes)
    with pytest.raises(RecordFileError) as exc:
        validate_graph(graph)
    assert ".md:" in str(exc.value)
    assert reason in str(exc.value)


def test_duplicate_ids_report_both_files(graph):
    graph.append(ParsedRecord(Path("duplicate.md"), graph[0].record, ""))
    with pytest.raises(RecordFileError, match="duplicate ID.*venture-ridgeview.md"):
        validate_graph(graph)


def test_parent_must_belong_to_same_venture(graph):
    graph.append(note("venture-acme", "venture", "venture-acme"))
    replace(graph, 2, venture="venture-acme")
    with pytest.raises(RecordFileError, match="different venture"):
        validate_graph(graph)


def test_cross_venture_dependencies_are_valid(graph):
    graph.append(note("venture-acme", "venture", "venture-acme", depends=["task-quotes"]))
    assert len(validate_graph(graph)) == 5
