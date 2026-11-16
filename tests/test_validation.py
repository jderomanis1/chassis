import subprocess
import sys
from pathlib import Path

import pytest

from chassis.markdown import RecordFileError
from chassis.validation import load_vault

TEXT = """---
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
# Fictional data
"""


@pytest.fixture
def vault(tmp_path):
    path = tmp_path / "records/ventures/venture-ridgeview.md"
    path.parent.mkdir(parents=True)
    path.write_text(TEXT, encoding="utf-8")
    (tmp_path / "README.md").write_text("Not a record", encoding="utf-8")
    return tmp_path


def test_loads_working_tree_and_ignores_nonrecord_markdown(vault):
    path = vault / "records/ventures/venture-ridgeview.md"
    path.write_text(TEXT.replace("status: planned", "status: done"), encoding="utf-8")
    assert load_vault(vault)["venture-ridgeview"].record.status == "done"


def test_empty_vault_is_not_a_success(tmp_path):
    with pytest.raises(RecordFileError, match="No record files"):
        load_vault(tmp_path)


def test_wrong_record_folder_is_rejected(vault):
    path = vault / "records/ventures/venture-ridgeview.md"
    path.rename(path.parent.parent / path.name)
    with pytest.raises(RecordFileError, match="records/ventures"):
        load_vault(vault)


def test_symlink_cannot_escape_vault(vault, tmp_path):
    outside = tmp_path / "outside.md"
    outside.write_text(TEXT, encoding="utf-8")
    (vault / "records/ventures/escape.md").symlink_to(outside)
    with pytest.raises(RecordFileError, match="symlink"):
        load_vault(vault)


def test_cli_success(vault):
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "validate", str(vault)],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert "VALID: 1 records" in result.stdout


def test_cli_failure_is_actionable(tmp_path):
    result = subprocess.run([sys.executable, "-m", "chassis.cli", "validate", str(tmp_path)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "No record files" in result.stderr
    assert "Traceback" not in result.stderr
