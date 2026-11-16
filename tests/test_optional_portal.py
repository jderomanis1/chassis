import subprocess
import sys
import tomllib

from conftest import ROOT


def test_portal_extra_has_only_the_two_approved_runtime_dependencies():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["optional-dependencies"]["portal"] == ["starlette>=1.10,<2", "uvicorn>=0.54,<1"]
    assert all(not item.startswith(("starlette", "uvicorn")) for item in project["dependencies"])


def test_core_cli_explains_missing_portal_extra():
    code = """
import importlib.abc, sys
class WithoutPortal(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'starlette', 'uvicorn'}:
            raise ModuleNotFoundError(name=fullname)
sys.meta_path.insert(0, WithoutPortal())
from chassis.cli import main
raise SystemExit(main(['portal']))
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr == 'INVALID: Portal support is not installed. Run: uv sync --extra portal (or pip install "chassis[portal]").\n'
