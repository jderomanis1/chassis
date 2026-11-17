from datetime import date

import pytest

from chassis.portal.health import health, health_map
from chassis.portal.config import TASK_DUE_SOON_DAYS, MILESTONE_SOON_DAYS, STALE_DAYS

TODAY = date(2026, 11, 16)


def task(**changes):
    return {"id": "task-sample", "type": "task", "status": "planned", "parent": "initiative-sample",
            "due_at": None, "last_activity_at": None, "depends_on": [], **changes}


def parent(kind="initiative", **changes):
    return {"id": f"{kind}-sample", "type": kind, "status": "planned", "parent": None,
            "milestone_due_at": None, "depends_on": [], **changes}


@pytest.mark.parametrize("changes,color,reasons", [
    ({"status": "done", "due_at": "2020-01-01"}, "green", ["done"]),
    ({"status": "blocked", "due_at": "2020-01-01"}, "red", ["blocked"]),
    ({"due_at": "2026-11-15"}, "red", ["overdue"]),
    ({"due_at": "2026-11-16"}, "yellow", ["due_soon"]),
    ({"due_at": "2026-11-19"}, "yellow", ["due_soon"]),
    ({"due_at": "2026-11-20"}, "green", ["on_track"]),
    ({"due_at": "2026-12-01", "last_activity_at": "2026-11-01T12:00:00Z"}, "yellow", ["stale"]),
    ({"due_at": "2026-11-17", "last_activity_at": "2026-11-01T12:00:00Z"}, "yellow", ["due_soon"]),
    ({"last_activity_at": "2026-11-02T07:00:00Z"}, "green", ["on_track"]),
    ({"last_activity_at": "2026-11-02T06:59:59Z"}, "yellow", ["stale"]),
    ({}, "unknown", ["no_signal"]),
    ({"last_activity_at": "2026-11-16T12:00:00Z"}, "green", ["on_track"]),
])
def test_task_rules_first_match_and_phoenix_boundaries(changes, color, reasons):
    assert health(task(**changes), [], TODAY) == {"color": color, "reasons": reasons}


@pytest.mark.parametrize("kind", ["initiative", "venture"])
@pytest.mark.parametrize("changes,children,color,reasons", [
    ({"milestone_due_at": "2026-11-15"}, [], "red", ["milestone_overdue"]),
    ({"milestone_due_at": "2026-11-16"}, [], "yellow", ["milestone_soon"]),
    ({"milestone_due_at": "2026-11-23"}, [], "yellow", ["milestone_soon"]),
    ({"milestone_due_at": "2026-11-24"}, [], "green", ["on_track"]),
    ({"status": "done", "milestone_due_at": "2026-11-15"}, [], "green", ["done"]),
    ({}, [], "unknown", ["no_signal"]),
    ({"status": "done"}, [], "unknown", ["no_signal"]),
    ({"next_milestone": "Fictional label without a date"}, [], "unknown", ["no_signal"]),
    ({}, [task()], "unknown", ["no_signal"]),
    ({}, [task(status="done")], "green", ["done"]),
    ({}, [task(status="done"), task()], "unknown", ["no_signal"]),
    ({}, [task(), task(due_at="2026-12-01")], "green", ["on_track"]),
    ({}, [task(due_at="2026-11-18"), task(status="blocked")], "red", ["blocked"]),
    ({"milestone_due_at": "2026-11-23"}, [task()], "yellow", ["milestone_soon"]),
    ({"milestone_due_at": "2026-11-23"}, [task(status="blocked")], "red", ["milestone_soon", "blocked"]),
    ({"milestone_due_at": "2026-11-15"}, [task(status="blocked")], "red", ["milestone_overdue"]),
])
def test_parent_rules_and_rollup_edges(kind, changes, children, color, reasons):
    children = [child | {"health": health(child, [], TODAY)} for child in children]
    assert health(parent(kind, **changes), children, TODAY) == {"color": color, "reasons": reasons}


@pytest.mark.parametrize("status,expected", [("planned", ["on_track", "waiting_on"]),
                                             ("blocked", ["on_track", "waiting_on"]),
                                             ("done", ["on_track"])])
def test_waiting_on_does_not_change_color(status, expected):
    record = task(due_at="2026-12-01", depends_on=["task-other"])
    assert health(record, [], TODAY, records={"task-other": task(status=status)}) == {
        "color": "green", "reasons": expected}


def test_health_map_rolls_up_only_supplied_visible_work_and_does_not_mutate_input():
    records = [parent("venture"), parent(parent="venture-sample"),
               task(due_at="2026-12-01", depends_on=["task-hidden"])]
    result = health_map(records, TODAY)
    assert result == {r["id"]: {"color": "green", "reasons": ["on_track"]} for r in records}
    assert all("health" not in r for r in records)
    records.append(task(id="task-hidden", status="blocked"))
    result = health_map(records, TODAY)
    assert result["task-sample"] == {"color": "green", "reasons": ["on_track", "waiting_on"]}
    assert result["initiative-sample"] == result["venture-sample"] == {"color": "red", "reasons": ["blocked"]}


def test_thresholds_are_configuration_constants():
    assert (TASK_DUE_SOON_DAYS, MILESTONE_SOON_DAYS, STALE_DAYS) == (3, 7, 14)
