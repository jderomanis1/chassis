"""One-off evidence collector: real test outputs, checked with literal ripgrep."""
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

rows = []


def redact_session(output):
    """CSRF stays in memory even when evidence captures a session response."""
    try:
        data = json.loads(output)
    except (ValueError, TypeError):
        return output
    if isinstance(data, dict) and "csrf" in data:
        return json.dumps(data | {"csrf": "<redacted>"})
    return output


def pytest_configure(config):
    sys.path.insert(0, str(config.rootpath / "tests"))
    import test_security_cli
    original = test_security_cli.assert_no_leaks
    directory = Path(os.environ["CHASSIS_LEAK_PROBE_DIR"])
    directory.mkdir(parents=True, exist_ok=True)

    def capture(outputs, terms):
        original(outputs, terms)
        module = inspect.currentframe().f_back.f_globals["__name__"]
        category = "mcp" if "mcp" in module else ("cli" if module == "test_security_cli" else "portal")
        output = "\n".join(redact_session(output) for output in outputs)
        path = directory / f"{len(rows):02d}-{category}.log"
        path.write_text(output)
        patterns = test_security_cli.leak_patterns(terms)
        args = ["rg", "--fixed-strings", "--multiline", "--files-with-matches"]
        for pattern in patterns:
            args += ["--regexp", pattern]
        checked = subprocess.run([*args, "--", str(path)], capture_output=True, text=True)
        assert checked.returncode == 1 and checked.stdout == "", "Literal leak grep found a match or failed"
        rows.append({"surface": category, "output_count": len(outputs), "bytes": len(output.encode()),
                     "patterns": len(patterns), "matching_files": 0, "rg_exit": checked.returncode})

    test_security_cli.assert_no_leaks = capture


def pytest_sessionfinish(session, exitstatus):
    directory = Path(os.environ["CHASSIS_LEAK_PROBE_DIR"])
    report = {"pytest_exit": int(exitstatus), "grep": "rg --fixed-strings --multiline --files-with-matches",
              "coverage": "restricted id, title, owner, complete body and partial body sentence; raw and JSON-escaped forms",
              "captures": rows, "matching_files": sum(row["matching_files"] for row in rows)}
    (directory / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
