"""Exercise Joe's commands using the real CLI and an isolated demo Git vault."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deploy"))
from meeting import chief_write, history
from start import initialize, open_vault


class MeetingTests(unittest.TestCase):
    def test_existing_files_survive_an_invalid_vault_or_failed_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "current"
            vault.mkdir()
            note = vault / "keep.txt"
            note.write_text("existing file")
            with self.assertRaises(RuntimeError):
                open_vault(root)
            self.assertEqual(note.read_text(), "existing file")
            note.unlink()
            vault.rmdir()
            open_vault(root)
            initial_history = history(vault)
            with contextlib.redirect_stdout(io.StringIO()):
                chief_write(vault)
            edited_history = history(vault)
            self.assertNotEqual(initial_history, edited_history)
            marker = vault / ".chassis/reset-on-next-start"
            marker.touch()
            with patch("start.initialize", side_effect=RuntimeError("seed failed")):
                with self.assertRaisesRegex(RuntimeError, "seed failed"):
                    open_vault(root)
            self.assertEqual(history(vault), edited_history)
            self.assertTrue(marker.exists())
            vault.rename(root / ".reset-previous")  # Interrupted before publishing the new seed.
            open_vault(root)
            self.assertFalse(marker.exists())
            self.assertNotIn("chief-of-staff@", history(vault))
            with contextlib.redirect_stdout(io.StringIO()):
                chief_write(vault)
            after_reset = history(vault)
            open_vault(root)
            self.assertEqual(history(vault), after_reset)

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
