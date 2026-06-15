"""Pydantic schema for Task"""

from datetime import date, timedelta
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from models.alert_state import AlertState
from schemas.validators import (
    bounded_str,
    not_in_future,
    not_in_past,
    positive_timedelta,
)


TaskContent = bounded_str(min_length=1, max_length=200)


class TaskBase(BaseModel):
    """Shared task fields. Field definitions only, so output schemas can reuse
    them without inheriting request constraints."""
    frequency: timedelta | None = None
    content: TaskContent
    date_last: date | None = None
    date_due: date | None = None


class TaskCreate(TaskBase):
    """Fields accepted when creating a task, with schedule validation."""

    @field_validator("frequency")
    @classmethod
    def frequency_positive(
        cls, value: timedelta | None
    ) -> timedelta | None:
        """A recurring task's frequency must be a positive interval."""
        return positive_timedelta(value, field_description="frequency")

    @field_validator("date_last")
    @classmethod
    def date_last_not_in_future(cls, value: date | None) -> date | None:
        """A task can't have last been done after today."""
        return not_in_future(value, date_description="date_last")

    @model_validator(mode="after")
    def date_due_not_before_date_last(self) -> Self:
        """A due date can't fall before the date the task was last done."""
        if (self.date_last is not None and self.date_due is not None
                and self.date_due < self.date_last):
            raise ValueError("date_due must not be before date_last")
        return self


class TaskUpdate(BaseModel):
    """Editable plain attributes of a task.

    Covers the free-form fields a user edits directly (currently `content`).
    The scheduling fields (`frequency`, `date_last`, `date_due`) are excluded:
    they carry lifecycle logic and are changed through dedicated operations
    rather than a generic edit.
    """
    content: TaskContent


class TaskPostpone(BaseModel):
    """Body for postponing a task: the new due date (today or later)."""
    date_due: date

    @field_validator("date_due")
    @classmethod
    def date_due_not_in_past(cls, value: date) -> date:
        """A task can't be postponed to a date that has already passed."""
        return not_in_past(value, date_description="date_due")


class FrequencyChange(BaseModel):
    """Body for changing a task's frequency."""
    frequency: timedelta | None

    @field_validator("frequency")
    @classmethod
    def frequency_positive(
        cls, value: timedelta | None
    ) -> timedelta | None:
        """A recurring task's frequency must be a positive interval."""
        return positive_timedelta(value, field_description="frequency")


class TaskRead(TaskBase):
    """Task fields returned to clients, including derived alert state."""
    task_id: UUID
    ship_id: UUID
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)
