import json

import pytest

from chassis.index import IndexFileError
from chassis.tool_handlers import TOOL_INPUTS, ToolHandlers

ARGUMENTS = {
    "list_records": {}, "read_record": {"id": "venture-acme"}, "search": {"query": "fictional"},
    "create_record": {"type": "task", "fields": {}},
    "create_from_template": {"template": "initiative", "venture": "venture-acme", "fields": {}},
    "update_record": {"id": "task-launch-offer", "expected_version": 1, "changes": {}},
}
INTERNAL = {"error": "internal_error", "reason": "Operation failed; inspect server stderr before retrying."}


@pytest.mark.parametrize("name", list(TOOL_INPUTS))
def test_every_tool_contains_absolute_index_paths(git_repo, monkeypatch, name):
    path = git_repo / ".chassis/index.sqlite"

    def fail(*args):
        raise IndexFileError(f"{path}: index paths cannot be symlinks")

    monkeypatch.setattr(ToolHandlers, "_call", fail)
    result = ToolHandlers(git_repo, "chief-of-staff").call(name, ARGUMENTS[name])
    assert result == INTERNAL
    assert str(git_repo) not in json.dumps(result)
    assert "/index.sqlite" not in json.dumps(result)
