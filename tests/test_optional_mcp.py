import os
import subprocess
import sys
import tomllib

from conftest import ROOT


def test_mcp_is_an_optional_extra():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["optional-dependencies"]["mcp"] == ["mcp>=2.3,<3"]
    assert all(not item.startswith("mcp") for item in project["dependencies"])


def test_core_imports_and_entry_point_explains_missing_mcp():
    code = """
import importlib.abc, sys
class WithoutExtras(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'mcp', 'anyio', 'starlette', 'uvicorn'}:
            raise ModuleNotFoundError(name=fullname)
sys.meta_path.insert(0, WithoutExtras())
import chassis.cli, chassis.index, chassis.store, chassis.tool_handlers, chassis.mcp_server
raise SystemExit(chassis.mcp_server.main([]))
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == 'MCP support is not installed. Run: uv sync --extra mcp (or pip install "chassis[mcp]").\n'
