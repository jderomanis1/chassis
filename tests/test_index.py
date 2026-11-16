import json
import os

import pytest

from chassis.index import RecordIndex
from chassis.markdown import RecordFileError

def query_bytes(index):
    results = [index.list_records(), index.get_record("task-launch-budget"),
               index.get_record("missing-id"), index.search("maintenance"),
               index.search("zz-no-match-zz"), index.search("internal launch test budget")]
    results.extend(index.list_records(filters) for filters, _ in FILTER_CASES)
    return json.dumps(results, ensure_ascii=False, sort_keys=True).encode("utf-8")


def test_delete_rebuild_produces_byte_identical_results(vault):
    sources = {path: path.read_bytes() for path in vault.rglob("*.md")}
    index = RecordIndex(vault)
    assert index.rebuild() == 13
    assert index.path == vault / ".chassis/index.sqlite"
    before = query_bytes(index)
    index.path.unlink()
    assert index.rebuild() == 13
    assert query_bytes(index) == before
    assert {path: path.read_bytes() for path in sources} == sources


def test_get_and_list_preserve_content_and_include_restricted_records(vault):
    index = RecordIndex(vault)
    index.rebuild()
    results = index.list_records()
    assert len(results) == 13
    assert [item["id"] for item in results] == sorted(item["id"] for item in results)
    restricted = index.get_record("task-launch-budget")
    assert restricted in results
    assert restricted["sensitivity"] == "restricted"
    assert "Fictional sample" in restricted["body"]
    assert all("sensitivity" in item for item in results)
    assert index.get_record("missing-id") is None


FILTER_CASES = [
    ({"type": "venture"}, ["venture-acme", "venture-ridgeview"]),
    ({"venture": "venture-acme"}, ["initiative-d2c-launch", "task-audience-interviews",
                                  "task-launch-budget", "task-launch-offer", "venture-acme"]),
    ({"status": "blocked"}, ["task-maintenance-plan"]),
    ({"parent": "initiative-resident-updates"}, ["task-resident-bulletin", "task-resident-faq"]),
    ({"assigned_agent": "reviewer"}, []),
    ({"sensitivity": "restricted"}, ["task-launch-budget"]),
    ({"parent": None}, ["venture-acme", "venture-ridgeview"]),
    ({"type": "task", "venture": "venture-acme", "status": "planned",
      "parent": "initiative-d2c-launch", "assigned_agent": "chief-of-staff",
      "sensitivity": "restricted"}, ["task-launch-budget"]),
    ({"venture": "venture-ridgeview", "sensitivity": "restricted"}, []),
]


@pytest.mark.parametrize(("filters", "expected"), FILTER_CASES)
def test_exact_filters_and_combinations(vault, filters, expected):
    index = RecordIndex(vault)
    index.rebuild()
    assert [item["id"] for item in index.list_records(filters)] == expected


def test_assignment_filters_distinguish_unassigned_and_known_agents(vault):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("assigned_agent: chief-of-staff",
                                            "assigned_agent: null"), encoding="utf-8")
    index = RecordIndex(vault)
    index.rebuild()
    assert [item["id"] for item in index.list_records({"assigned_agent": None})] == ["task-launch-budget"]
    assert len(index.list_records({"assigned_agent": "chief-of-staff"})) == 12


@pytest.mark.parametrize(("query", "expected"), [
    ("  INTERNAL LAUNCH TEST BUDGET  ", ["task-launch-budget"]),
    ("three most repeated", ["task-audience-interviews"]),
    ("No vendor is contacted", ["task-maintenance-quotes"]),
    ("zz-no-match-zz", []), ("", []), ("   ", []),
    ("%", []), ("_", []), ("' OR 1=1 --", []),
])
def test_search_is_literal_case_insensitive_substring(vault, query, expected):
    index = RecordIndex(vault)
    index.rebuild()
    results = index.search(query)
    assert [item["id"] for item in results] == expected
    assert all("sensitivity" in item for item in results)


def test_search_matches_unicode_and_has_deterministic_order(vault):
    for name in ("task-launch-offer", "task-launch-budget"):
        path = vault / "records/tasks" / f"{name}.md"
        path.write_text(path.read_text() + "\nFictional Straße exercise.\n", encoding="utf-8")
    index = RecordIndex(vault)
    index.rebuild()
    assert [item["id"] for item in index.search("STRASSE")] == ["task-launch-budget", "task-launch-offer"]


def test_search_finds_terms_present_only_in_title(vault):
    path = vault / "records/tasks/task-launch-budget.md"
    path.write_text(path.read_text().replace("title: Set the internal launch test budget",
                                            "title: Fictional sapphire marker"), encoding="utf-8")
    index = RecordIndex(vault)
    index.rebuild()
    assert [item["id"] for item in index.search("sapphire marker")] == ["task-launch-budget"]


@pytest.mark.parametrize("filters", [{"typo": "task"}, {"type": None}, {"status": 1}])
def test_invalid_filter_fields_and_values_are_actionable(vault, filters):
    index = RecordIndex(vault)
    index.rebuild()
    with pytest.raises(ValueError, match=next(iter(filters))):
        index.list_records(filters)


@pytest.mark.parametrize("operation", ["list", "get", "search"])
@pytest.mark.parametrize("preserve_mtime", [False, True])
def test_every_read_refreshes_edits_even_with_preserved_mtime(vault, monkeypatch,
                                                            operation, preserve_mtime):
    index = RecordIndex(vault)
    index.rebuild()
    monkeypatch.setattr(index, "rebuild", lambda: pytest.fail("Expected record refresh, not rebuild"))
    path = vault / "records/tasks/task-launch-budget.md"
    previous = path.stat()
    text = path.read_text().replace("status: planned", "status: blocked")
    path.write_text(text.replace("visibility rule", "freshness proof"), encoding="utf-8")
    assert path.stat().st_size == previous.st_size
    mtime = previous.st_mtime_ns if preserve_mtime else previous.st_mtime_ns + 10_000_000
    os.utime(path, ns=(previous.st_atime_ns, mtime))
    if operation == "list":
        result = index.list_records({"status": "blocked", "sensitivity": "restricted"})[0]
    elif operation == "get":
        result = index.get_record("task-launch-budget")
    else:
        result = index.search("freshness proof")[0]
    assert result["id"] == "task-launch-budget" and result["status"] == "blocked"
    assert "freshness proof" in result["body"]


def test_source_addition_and_removal_are_seen_without_rebuild(vault):
    index = RecordIndex(vault)
    index.rebuild()
    original = vault / "records/tasks/task-launch-budget.md"
    added = original.with_name("task-extra-budget.md")
    added.write_text(original.read_text().replace("task-launch-budget", "task-extra-budget"),
                     encoding="utf-8")
    assert len(index.list_records()) == 14
    assert index.get_record("task-extra-budget") is not None
    added.unlink()
    assert index.get_record("task-extra-budget") is None
    assert len(index.search("launch test budget")) == 1


@pytest.mark.parametrize("method,args", [("rebuild", ()), ("list_records", ()),
                                        ("get_record", ("venture-acme",)), ("search", ("",))])
def test_invalid_source_fails_loudly_before_any_answer(vault, method, args):
    index = RecordIndex(vault)
    index.rebuild()
    (vault / "records/tasks/broken.md").write_text("# Missing frontmatter\n", encoding="utf-8")
    with pytest.raises(RecordFileError, match="broken.md:.*opening YAML frontmatter fence"):
        getattr(index, method)(*args)


def test_removal_that_breaks_relationships_is_rejected(vault):
    index = RecordIndex(vault)
    index.rebuild()
    (vault / "records/tasks/task-maintenance-inventory.md").unlink()
    with pytest.raises(RecordFileError, match="task-maintenance-quotes.md: dependency.*does not exist"):
        index.list_records()
