"""Undo targets from canvas-editor commits. History is never rewritten."""
import re

from chassis.git import GitError, run_git
from chassis.markdown import RecordFileError, parse_record, read_record

FIELDS = ("title", "status", "next_step", "blocker_reason", "due_at", "depends_on")


def _snapshot(record, visible):
    data = record.model_dump(mode="json")
    values = {}
    for key in FIELDS:
        value = data.get(key)
        if key == "depends_on":
            value = [item for item in value or [] if item in visible]
        values[key] = value
    return values


def _show(root, rev, relative):
    try:
        text = run_git(root, "show", f"{rev}:{relative}")
    except GitError:
        return None
    try:
        return parse_record(text, root / relative).record
    except RecordFileError:
        return None


def _last_email(root, relative):
    try:
        return run_git(root, "log", "-1", "--format=%ae", "--", relative)
    except GitError:
        return ""


def undo_entries(root, email, visible, limit=10):
    """Last canvas edits by ``email``, oldest first, as new forward patches.

    A later commit that applies the previous inverse is that undo, so it is
    removed from the stack. The version is the current one when the visible
    fields still match, including after an editor undo. A different author
    leaves the old version in place so the patch conflicts.
    """
    if not email:
        return []
    try:
        log = run_git(root, "log", "-n", "40", "--format=%H", f"--author={re.escape(email)}", "--", "records")
    except GitError:
        return []
    stack = []
    for sha in reversed([line for line in log.splitlines() if line]):
        try:
            paths = [line for line in run_git(
                root, "diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines() if line]
            parent = run_git(root, "rev-parse", f"{sha}^")
        except GitError:
            continue
        if len(paths) != 1 or not paths[0].startswith("records/") or not paths[0].endswith(".md"):
            continue
        relative = paths[0]
        before, after = _show(root, parent, relative), _show(root, sha, relative)
        if before is None or after is None:
            continue
        # A commit the viewer cannot see must not change the stack, its count, or its etag.
        if after.id not in visible or before.id not in visible:
            continue
        prior, current = _snapshot(before, visible), _snapshot(after, visible)
        forward = {key: current[key] for key in FIELDS if prior[key] != current[key]}
        if not forward:
            continue
        inverse = {key: prior[key] for key in forward}
        if stack and stack[-1]["id"] == after.id and stack[-1]["changes"] == forward:
            stack.pop()
            continue
        stack.append({"id": after.id, "path": relative, "changes": inverse,
                      "after": current, "after_version": after.version})
    entries = stack[-limit:]
    while entries:
        top = entries[-1]
        path = root / top["path"]
        try:
            record = read_record(path).record if path.is_file() else None
        except RecordFileError:
            record = None
        if record is not None and _snapshot(record, visible) == top["after"] and (
                record.version == top["after_version"]
                or _last_email(root, top["path"]).casefold() == email.casefold()):
            for item in entries:
                if item["id"] == top["id"]:
                    item["version"] = record.version
            break
        entries = [item for item in entries if item["id"] != top["id"]]
    return [{"id": item["id"], "changes": item["changes"], "version": item.get("version", item["after_version"])}
            for item in entries if "version" in item or item.get("after_version")]
