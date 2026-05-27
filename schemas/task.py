"""Pydantic schema for Task"""

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.alert_state import AlertState


class TaskBase(BaseModel):
    frequency: timedelta | None = None
    content: str
    date_last: date | None = None
    date_due: date | None = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    task_id: UUID
    ship_id: UUID
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    frequency: timedelta | None = None
    content: str | None = None
    date_last: date | None = None
    date_due: date | None = None
