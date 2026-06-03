"""Pydantic schema for Task"""

from datetime import date, timedelta
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from models.alert_state import AlertState


class TaskBase(BaseModel):
    """Shared task fields. Field definitions only, so output schemas can reuse
    them without inheriting request constraints."""
    frequency: timedelta | None = None
    content: str
    date_last: date | None = None
    date_due: date | None = None


class TaskWrite(TaskBase):
    """Base for request schemas: shared fields plus the input validation
    common to creating and updating a task."""

    @field_validator("date_last")
    @classmethod
    def date_last_not_in_future(cls, value: date | None) -> date | None:
        """A task can't have last been done after today."""
        if value is not None and value > date.today():
            raise ValueError("date_last must not be in the future")
        return value

    @model_validator(mode="after")
    def date_due_not_before_date_last(self) -> Self:
        """A due date can't fall before the date the task was last done."""
        if (self.date_last is not None and self.date_due is not None
                and self.date_due < self.date_last):
            raise ValueError("date_due must not be before date_last")
        return self


class TaskCreate(TaskWrite):
    pass


class TaskUpdate(TaskWrite):
    content: str | None = None


class TaskRead(TaskBase):
    task_id: UUID
    ship_id: UUID
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)
