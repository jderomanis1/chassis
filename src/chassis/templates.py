"""Constrained Markdown templates. Expansion never edits policy or writes files."""

import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path

from chassis.errors import WriteError

GTM_SECTIONS = ("Positioning", "Audience", "Channels", "Offer", "Launch checklist", "Success metrics")
AGENT_SECTIONS = ("Playbooks", "Channels", "Data scope")
READ_ONLY_PERMISSIONS = ("Read-only by default. This document grants no access.\n"
                         "Only a human can change access grants in agents.yaml.")
TEMPLATE_SECTIONS = {"initiative": GTM_SECTIONS, "agent": AGENT_SECTIONS}
TOKEN = re.compile(r"\{\{([^{}\n]+)\}\}")
HEADING = re.compile(r"^## ([^\r\n]+)\r?$", re.MULTILINE)
PLACEHOLDER = re.compile(
    r"\{\{|\}\}|\$\{|\b(?:TODO|TBD|TBC|FIXME|XXX|PLACEHOLDER)\b|"
    r"[\[<]\s*(?:insert|replace|fill)\b[^\]>]*[\]>]", re.IGNORECASE)


def _filled(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WriteError(f"{label}: missing or empty template content")
    visible = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    visible = re.sub(r"(?m)^\s*(?:[-*+]|\d+[.)])(?:[ \t]+|$)(?:\[[ xX]\][ \t]*)?", "", visible)
    if not re.search(r"\w", visible):
        raise WriteError(f"{label}: empty template content")
    if PLACEHOLDER.search(unicodedata.normalize("NFKC", value)):
        raise WriteError(f"{label}: leftover placeholder text")
    return value.strip()


def template_sections(template: str) -> tuple[str, ...]:
    if not isinstance(template, str) or template not in TEMPLATE_SECTIONS:
        raise WriteError(f"unknown template: {template!r}")
    return TEMPLATE_SECTIONS[template]


def expand_template(root: Path, template: str, fields: Mapping) -> dict:
    """Return create fields; the caller must authorize before opening a template."""
    names = template_sections(template)
    if not isinstance(fields, Mapping):
        raise WriteError("fields must be an object")
    fields = dict(fields)
    reserved = {"type", "venture", "parent", "body"}.intersection(fields)
    if reserved:
        raise WriteError(f"template controls fields: {', '.join(sorted(reserved))}")
    sections = fields.pop("sections", {})
    if not isinstance(sections, Mapping):
        raise WriteError("sections must be an object keyed by exact section names")
    values = {name: _filled(sections.get(name), name) for name in names}
    if set(sections) != set(names):
        raise WriteError("unknown template section names")
    values["title"] = _filled(fields.get("title"), "title")
    for key, value in fields.items():
        if isinstance(value, str):
            _filled(value, key)
    path = root / "templates" / f"{template}.md"
    if path.parent.is_symlink() or path.is_symlink():
        raise WriteError(f"{path}: template paths cannot be symlinks")
    source = path.read_text(encoding="utf-8")
    if TOKEN.findall(source) != ["title", *names]:
        raise WriteError(f"{path}: invalid template placeholders")
    headings = (*names, "Permissions") if template == "agent" else names
    parts = HEADING.split(source)
    if tuple(parts[1::2]) != headings:
        raise WriteError(f"{path}: invalid template section names or order")
    for name, content in zip(parts[1::2], parts[2::2]):
        if name in names and TOKEN.findall(content) != [name]:
            raise WriteError(f"{path}: {name} has invalid section placeholders")
    body = TOKEN.sub(lambda match: values[match[1]], source)
    parts = HEADING.split(body)
    if tuple(parts[1::2]) != headings:
        raise WriteError(f"{path}: invalid template section names or order")
    for name, content in zip(parts[1::2], parts[2::2]):
        _filled(content, name)
    if template == "agent" and body.split("\n## Permissions\n")[-1].strip() != READ_ONLY_PERMISSIONS:
        raise WriteError(f"{path}: agent template permissions must remain read-only")
    _filled(body, "rendered template")
    return {"status": "planned", **fields, "body": body}
