"""Exercise Joe's commands using the real CLI and an isolated demo Git vault."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deploy"))
from meeting import chief_write, history
from start import initialize


class MeetingTests(unittest.TestCase):
    def test_cli_updates_once_and_history_names_the_record_and_author(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            env = initialize(vault)
            self.assertEqual(env["CHASSIS_PORTAL_EDITOR_AGENT"], "canvas-editor")
            self.assertNotEqual(env["CHASSIS_PORTAL_EDITOR_TOKEN"], env["CHASSIS_AGENT_TOKEN"])
            self.assertNotIn("DEMO_PASSWORD", env)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                chief_write(vault)
                chief_write(vault)
            log = history(vault)
            self.assertIn("chief-of-staff <chief-of-staff@chassis.local>", log)
            self.assertIn("records/tasks/task-cedar-launch-2.md", log)
            self.assertNotIn(env["CHASSIS_AGENT_TOKEN"], out.getvalue() + log)
            count = subprocess.check_output(["git", "-C", vault, "rev-list", "--count", "HEAD"])
            self.assertEqual(count.strip(), b"2")
