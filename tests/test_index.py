import json
import shutil
from pathlib import Path

import pytest

from chassis.index import RecordIndex

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def vault(tmp_path):
    shutil.copytree(ROOT / "records", tmp_path / "records")
    shutil.copyfile(ROOT / "agents.yaml", tmp_path / "agents.yaml")
    return tmp_path


def query_bytes(index):
    results = [index.list_records(), index.get_record("task-launch-budget"),
               index.get_record("missing-id")]
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
