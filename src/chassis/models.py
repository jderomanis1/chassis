"""Record schema shared by every transport and renderer."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (AwareDatetime, BaseModel, ConfigDict, Field,
                      StringConstraints, field_validator)

RecordId = Annotated[str, StringConstraints(strict=True, max_length=80,
                       pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]
Nonempty = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                                          min_length=1)]
RecordType = Literal["venture", "initiative", "task"]


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
