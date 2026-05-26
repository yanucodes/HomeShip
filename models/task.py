"""Task ORM model.

Maps to the `tasks` table. See `AlertState` in `models.alert_state` for
the meaning of each alert level.
"""

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Interval, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base

if TYPE_CHECKING:
    from models.ship import Ship


class Task(Base):
    """Task for the household.

    Attributes:
        task_id: UUID primary key. Generated in Python via `uuid.uuid4`
            on insert if the caller does not provide one.
        ship_id: Foreign key to `ships.ship_id`.
        frequency: Time interval at which the task should be completed.
            Null for non-repeating tasks.
        content: Description of the task (e.g. "Laundry").
        date_last: Last date when the task was completed. Null if it has
            never been completed.
        date_due: Date when the task should be completed (`date_last +
            frequency` if `alert_state` is green, later if postponed).
            Null for non-repeating tasks that have been archived.
        alert_state: Shows if the task was completed on time or postponed.
            Defaults to `AlertState.GREEN`.
        ship: The `Ship` this task belongs to. Two-way mirror of
            `Ship.tasks`.
    """

    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ships.ship_id"), nullable=False
    )
    frequency: Mapped[timedelta | None] = mapped_column(Interval)
    content: Mapped[str] = mapped_column(String, nullable=False)
    date_last: Mapped[date | None] = mapped_column(Date)
    date_due: Mapped[date | None] = mapped_column(Date)
    alert_state: Mapped[AlertState] = mapped_column(
        SqlEnum(
            AlertState,
            name="alert_state",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=AlertState.GREEN,
    )

    ship: Mapped["Ship"] = relationship(back_populates="tasks")
