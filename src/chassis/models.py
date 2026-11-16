"""Record schema shared by every transport and renderer."""

import re
from datetime import date, datetime
from typing import Annotated, Literal, get_args

from pydantic import (AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field,
                      StringConstraints, field_validator)

RecordId = Annotated[str, StringConstraints(strict=True, max_length=80,
                       pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]
Nonempty = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                                          min_length=1)]
RecordType = Literal["venture", "initiative", "task", "agent"]
RECORD_TYPES = get_args(RecordType)


def iso_date(value):
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return date.fromisoformat(value)
    raise ValueError("must be an ISO date (YYYY-MM-DD)")


IsoDate = Annotated[date, BeforeValidator(iso_date)]
OptionalText = Annotated[str, StringConstraints(strict=True, strip_whitespace=True)] | None


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: RecordId
    type: RecordType
    title: Nonempty
    status: Literal["planned", "in_progress", "blocked", "done"]
    owner: Nonempty
    venture: RecordId
    parent: RecordId | None
    next_step: Nonempty
    updated_at: AwareDatetime
    version: Annotated[int, Field(strict=True, ge=1)]
    sensitivity: Literal["normal", "restricted"] = "normal"
    assigned_agent: RecordId | None = None
    depends_on: list[RecordId] = Field(default_factory=list, strict=True)
    next_milestone: Nonempty | None = None
    milestone_due_at: IsoDate | None = None
    due_at: IsoDate | None = None
    blocker_reason: OptionalText = Field(default=None, validate_default=True)

    @field_validator("next_milestone", "milestone_due_at", "due_at")
    @classmethod
    def portal_field_scope(cls, value, info):
        kinds = {"task"} if info.field_name == "due_at" else {"venture", "initiative"}
        if value is not None and info.data.get("type") not in kinds:
            raise ValueError(f"{info.field_name} is only valid for {', '.join(sorted(kinds))}")
        return value

    @field_validator("blocker_reason")
    @classmethod
    def blocker_matches_status(cls, value, info):
        if info.data.get("type") == "task" and info.data.get("status") == "blocked":
            if not value:
                raise ValueError("blocker_reason is required when a task is blocked")
        elif value:
            raise ValueError("blocker_reason must be empty unless a task is blocked")
        return value

    @field_validator("updated_at", mode="before")
    @classmethod
    def require_datetime_or_string(cls, value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("updated_at must be a timezone-aware ISO datetime") from exc
        if not isinstance(value, (str, datetime)):
            raise ValueError("updated_at must be a timezone-aware ISO datetime")
        return value

    @field_validator("depends_on")
    @classmethod
    def unique_dependencies(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("depends_on contains duplicate IDs")
        return value
