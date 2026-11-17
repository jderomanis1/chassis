import importlib.util
import json
import secrets

import pytest

from conftest import ROOT, EphemeralToken
from test_security_cli import assert_no_leaks, restricted_terms


def probe_module():
    spec = importlib.util.spec_from_file_location("leak_probe", ROOT / "evidence/step6_leak_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_leak_probe_detects_a_partial_body_sentence(git_repo):
    terms = restricted_terms(git_repo)
    fragment = "Keep this record out of every rendered graph"
    assert fragment in terms[-1] and terms[-1] not in fragment
    with pytest.raises(AssertionError):
        assert_no_leaks([json.dumps({"snippet": fragment})], terms)


def test_evidence_redacts_session_csrf_before_writing_captures():
    csrf = EphemeralToken(secrets.token_urlsafe(32))
    output = json.dumps({"csrf": csrf, "viewer": "reviewer", "writes_enabled": False})
    safe = probe_module().redact_session(output)
    assert csrf not in safe
    assert json.loads(safe) == {"csrf": "<redacted>", "viewer": "reviewer", "writes_enabled": False}


def test_evidence_preserves_other_outputs_for_leak_checks():
    module = probe_module()
    for output in ['{"error":{"code":"not_found"}}', "Fictional stderr output"]:
        assert module.redact_session(output) == output
