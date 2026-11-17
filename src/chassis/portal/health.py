"""Pure health rules over a viewer's authorized records, with an injected date."""
from datetime import date, datetime

from chassis.portal.config import PHOENIX, TASK_DUE_SOON_DAYS, MILESTONE_SOON_DAYS, STALE_DAYS


def as_date(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def result(color, *reasons):
    return {"color": color, "reasons": list(dict.fromkeys(reasons))}


def task_health(record, today):
    due, activity = record.get("due_at"), record.get("last_activity_at")
    if record["status"] == "done":
        return result("green", "done")
    if record["status"] == "blocked":
        return result("red", "blocked")
    if due and as_date(due) < today:
        return result("red", "overdue")
    if due and (as_date(due) - today).days <= TASK_DUE_SOON_DAYS:
        return result("yellow", "due_soon")
    if activity:
        activity = datetime.fromisoformat(activity) if isinstance(activity, str) else activity
        if (today - activity.astimezone(PHOENIX).date()).days > STALE_DAYS:
            return result("yellow", "stale")
    if not due and not activity:
        return result("unknown", "no_signal")
    return result("green", "on_track")


def health(record, children, today, *, records=None):
    """Children may carry computed health; dependency lookup contains visible rows only."""
    if record["type"] == "task":
        value = task_health(record, today)
        visible = records or {}
        if any(dep in visible and visible[dep]["status"] != "done" for dep in record.get("depends_on", [])):
            value["reasons"].append("waiting_on")
        return value

    milestone = record.get("milestone_due_at")
    days = (as_date(milestone) - today).days if milestone else None
    if days is not None and days < 0 and record["status"] != "done":
        return result("red", "milestone_overdue")
    active = [child for child in children if child["status"] != "done"]
    values = [child.get("health") or health(child, [], today, records=records) for child in active]
    known = [value for value in values if value["color"] != "unknown"]
    rank = {"green": 0, "yellow": 1, "red": 2}
    if known:
        color = max((value["color"] for value in known), key=rank.get)
        value = result(color, *(reason for v in known if v["color"] == color for reason in v["reasons"]))
    elif active:
        value = result("unknown", "no_signal")
    elif children:
        value = result("green", "done")
    elif milestone:
        value = result("green", "done" if record["status"] == "done" else "on_track")
    else:
        value = result("unknown", "no_signal")
    if days is not None and 0 <= days <= MILESTONE_SOON_DAYS:
        reasons = value["reasons"] if value["color"] in {"yellow", "red"} else []
        value = result("red" if value["color"] == "red" else "yellow", "milestone_soon", *reasons)
    return value


def health_map(records, today):
    """Roll up the authorized hierarchy; hidden records cannot enter this function."""
    by_id, computed = {record["id"]: record for record in records}, {}
    child_types = {"venture": "initiative", "initiative": "task"}

    def calculate(record):
        if record["id"] not in computed:
            children = [child | {"health": calculate(child)} for child in records
                        if child["parent"] == record["id"] and child["type"] == child_types.get(record["type"])]
            computed[record["id"]] = health(record, children, today, records=by_id)
        return computed[record["id"]]

    for record in records:
        calculate(record)
    return computed
