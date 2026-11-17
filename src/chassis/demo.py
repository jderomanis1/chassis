"""Create an isolated fictional canvas demo; never copy a user's venture data."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from chassis.atomic import write_atomic
from chassis.git import Identity, run_git
from chassis.identity import create_agent_token
from chassis.markdown import serialize_record
from chassis.models import Record
from chassis.templates import GTM_SECTIONS
from chassis.validation import load_vault

VENTURES = (("ridgeview", "Ridgeview HOA"), ("acme", "Acme D2C"),
            ("cedar", "Cedar Rentals"), ("lumen", "Lumen Skincare"),
            ("atlas", "Atlas Trades"), ("northwind", "Northwind Reno"),
            ("juniper", "Juniper Events"))


def demo_records():
    now = datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo("America/Phoenix")).date()
    rows = []

    def add(kind, identifier, title, venture, parent, **fields):
        record = Record.model_validate(dict(id=identifier, type=kind, title=title,
            venture=venture, parent=parent, status="in_progress", owner="Fictional Demo Team",
            next_step="Review the fictional sample plan.", updated_at=now, version=1) | fields)
        body = "Fictional sample work for the canvas demonstration.\n"
        if kind == "initiative":
            body = "\n".join(f"## {section}\nFictional {title.lower()} plan for {section.lower()}.\n"
                             for section in GTM_SECTIONS)
        if record.sensitivity == "restricted":
            body = "Fictional private budget planning note. Authorized sample reviewers only.\n"
        rows.append((record, body))

    for slug, title in VENTURES:
        venture = f"venture-{slug}"
        add("venture", venture, title, venture, None,
            next_milestone="Review the fictional delivery plan", milestone_due_at=today + timedelta(days=21))
        for stage in ("launch", "operations"):
            initiative = f"initiative-{slug}-{stage}"
            add("initiative", initiative, f"{title} {stage} plan", venture, venture,
                next_milestone=f"Complete the fictional {stage} review", milestone_due_at=today + timedelta(days=14))
            previous = None
            for number, status in enumerate(("done", "planned", "in_progress"), 1):
                identifier = f"task-{slug}-{stage}-{number}"
                restricted = slug == "acme" and stage == "operations" and number == 3
                if restricted:
                    identifier = "task-launch-budget"
                blocked = slug == "ridgeview" and stage == "launch" and number == 2
                due_days = 2 if slug == "cedar" else -1 if slug == "northwind" else 10
                dependencies = [previous] if previous else []
                if slug == "atlas" and stage == "launch" and number == 3:
                    dependencies.append("task-ridgeview-operations-3")
                add("task", identifier, "Review the private fictional budget" if restricted else
                    f"{title}: {stage} review {number}", venture, initiative,
                    status="blocked" if blocked else status,
                    owner="Fictional Private Steward" if restricted else "Fictional Demo Team",
                    sensitivity="restricted" if restricted else "normal", depends_on=dependencies,
                    due_at=today + timedelta(days=due_days),
                    blocker_reason="Waiting for fictional supplier approval." if blocked else None)
                previous = identifier
    return rows


def create_demo(destination):
    root = Path(destination)
    if root.exists() or root.is_symlink():
        raise ValueError("Demo destination must not already exist")
    root = root.resolve()
    root.mkdir(parents=True)
    for record, body in demo_records():
        path = root / "records" / f"{record.type}s" / f"{record.id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(path, serialize_record(record, body))
    agents = {}
    for agent, permission, clearance in (("reviewer", "read", "normal"),
            ("canvas-editor", "write", "normal"), ("chief-of-staff", "write", "restricted")):
        agents[agent] = {"clearance": clearance, "ventures": {f"venture-{slug}":
            {kind: permission for kind in ("venture", "initiative", "task")} for slug, _ in VENTURES}}
    write_atomic(root / "agents.yaml", yaml.safe_dump({"version": 1, "unknown_agent": "deny", "agents": agents}).encode())
    write_atomic(root / ".gitignore", b".chassis/\n.env\n.env.*\n")
    load_vault(root)
    run_git(root, "init", "-q", "--initial-branch=main")
    run_git(root, "config", "user.name", "Chassis Demo")
    run_git(root, "config", "user.email", "demo@chassis.local")
    run_git(root, "config", "commit.gpgsign", "false")
    run_git(root, "add", "--", "records", "agents.yaml", ".gitignore")
    run_git(root, "commit", "-qm", "chassis: initialize fictional canvas demo",
            identity=Identity("Chassis Demo", "demo@chassis.local"))
    return {"vault": str(root), "credentials": {agent: create_agent_token(root, agent) for agent in agents}}
