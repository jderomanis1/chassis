"""stdio update_record uses the same hidden-dependency rules as the library."""
import json

from conftest import git
from mcp_client import StdioClient
from chassis.markdown import read_record
from test_hidden_dependencies import AGENT, HIDDEN, TARGET, VISIBLE, plant
from test_read_error_safety import normal_writer


def test_stdio_update_record_preserves_hidden_dependencies(git_repo):
    path = plant(git_repo, [HIDDEN])
    other = git_repo / "records/tasks/task-resident-faq.md"
    other.write_text(other.read_text().replace("sensitivity: normal", "sensitivity: restricted"))
    token = normal_writer(git_repo)
    original, head = path.read_bytes(), git(git_repo, "rev-parse", "HEAD")
    with StdioClient(git_repo, CHASSIS_AGENT_ID=AGENT, CHASSIS_AGENT_TOKEN=token) as client:
        client.initialize()
        hidden = client.call("update_record", {"id": TARGET, "expected_version": 1, "changes": {
            "depends_on": ["task-resident-faq"]}})
        missing = client.call("update_record", {"id": TARGET, "expected_version": 1, "changes": {
            "depends_on": ["task-missing"]}})
        assert hidden == missing
        assert hidden["error"] == "validation" and hidden["reason"] == "invalid dependency"
        blob = json.dumps([hidden, missing])
        for term in (HIDDEN, "task-resident-faq", "task-missing"):
            assert term not in blob
        assert path.read_bytes() == original and git(git_repo, "rev-parse", "HEAD") == head
        saved = client.call("update_record", {"id": TARGET, "expected_version": 1, "changes": {
            "title": "Fictional stdio title"}})
        assert saved["record"]["depends_on"] == [] and HIDDEN not in json.dumps(saved)
        assert read_record(path).record.depends_on == [HIDDEN]
        linked = client.call("update_record", {"id": TARGET, "expected_version": 2, "changes": {
            "depends_on": [VISIBLE]}})
        assert linked["record"]["depends_on"] == [VISIBLE] and HIDDEN not in json.dumps(linked)
        assert read_record(path).record.depends_on == [VISIBLE, HIDDEN]
        undone = client.call("update_record", {"id": TARGET, "expected_version": 3, "changes": {"depends_on": []}})
        assert undone["record"]["depends_on"] == []
        assert read_record(path).record.depends_on == [HIDDEN]
        read = client.call("read_record", {"id": TARGET})
        assert read["record"]["depends_on"] == [] and HIDDEN not in json.dumps(read)
