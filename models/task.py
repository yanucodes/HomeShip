"""Task ORM model.

Maps to the `tasks` table. See `AlertState` in `models.alert_state` for
the meaning of each alert level.
"""

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Interval, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base
from models.mixins import Alertable

if TYPE_CHECKING:
    from models.ship import Ship


class Task(Alertable, Base):
    """Task for the household.

    `date_due` and `alert_state` come from the `Alertable` mixin.

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
            Defaults to `AlertState.INACTIVE`.
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

    ship: Mapped["Ship"] = relationship(back_populates="tasks")

    @staticmethod
    def derive_dates(
        frequency: timedelta | None,
        date_last: date | None,
        date_due: date | None,
        today: date | None = None,
    ) -> tuple[date | None, date | None]:
        """Fill in a task's schedule from the fields the client supplied.

        The three date-related fields are all optional, and their
        combination encodes the task's lifecycle:

        * recurring (`frequency` set): default `date_last` to today or, if
          no `date_last` was given, set `date_due` to `date_last + frequency`.
        * one-off with a deadline (no `frequency`, `date_due` given): clear
          `date_last` — `date_last` is not tracked for a one-off task.
        * inactive (neither given): leave both null.

        Returns:
            The `(date_last, date_due)` pair after derivation.
        """
        today = today or date.today()
        if frequency:
            date_last = date_last or today
            date_due = date_last + frequency
        else:
            date_last = None
        return date_last, date_due

    def get_changes_on_completing(self, today: date | None = None) -> dict:
        """Compute the field changes when completing the task.

        Args:
            today: Reference date for completion; defaults to `date.today()`.
                Injectable to keep the logic deterministic in tests.

        Returns:
            A `{field: value}` dict for `date_last`, `date_due`, and
            `alert_state` reflecting the completion.
        """
        today = today or date.today()
        date_due = today + self.frequency if self.frequency else None
        return {
            "date_last": today,
            "date_due": date_due,
            "alert_state": AlertState.from_due_date(date_due)
        }

    def get_changes_on_postponing(self, date_due: date) -> dict:
        """Compute the field changes when postponing the task.

        Postponing pushes the due date out and raises the alert one level
        (GREEN -> YELLOW -> RED -> AUTO_DESTRUCT) via `AlertState.escalate`,
        so repeated postponements surface increasing urgency.

        Args:
            date_due: New due date for the task, already validated by the
                `TaskPostpone` schema.

        Returns:
            A `{field: value}` dict for `date_due` and `alert_state`.
        """
        return {
            "date_due": date_due,
            "alert_state": self.alert_state.escalate()
        }


    def get_changes_on_frequency_changing(self, frequency: timedelta | None,
                                          today: date | None = None) -> dict:
        """
        Compute the field changes when changing the frequency of the task.

        A new due date is set for recurrent tasks (date_last + frequency).
        Alert is set according to due_date via `AlertState.from_due_date`.

        Args:
            frequency: New frequency for the task.
            today: Reference date for derivation; defaults to `date.today()`.
                Injectable to keep construction deterministic in tests.

        Returns:
            A `{field: value}` dict for `frequency`, `date_last`,
            `date_due`, and `alert_state`.
        """
        date_last, date_due = self.derive_dates(
            frequency, self.date_last, self.date_due, today
        )
        return {
            "frequency": frequency,
            "date_last": date_last,
            "date_due": date_due,
            "alert_state": AlertState.from_due_date(date_due)
        }

    def get_changes_on_deactivation(self) -> dict:
        """
        Return the field changes when task is deactivated.

        Returns:
            A `{field: value}` dict for `frequency`, `date_last`,
            `date_due`, and `alert_state`.
        """
        return {
            "frequency": None,
            "date_last": None,
            "date_due": None,
            "alert_state": AlertState.INACTIVE
        }

    @classmethod
    def scheduled(
        cls,
        *,
        ship_id: uuid.UUID,
        content: str,
        frequency: timedelta | None = None,
        date_last: date | None = None,
        date_due: date | None = None,
        today: date | None = None,
    ) -> "Task":
        """Build a Task with its schedule and alert state derived from the
        given fields.

        Encapsulates "how to construct a valid task" in one place. The dates
        are filled in via `derive_dates` and the alert state via
        `AlertState.from_due_date`.

        Args:
            ship_id: ID of the ship the task belongs to.
            content: Description of the task.
            frequency: Interval for a recurring task, or None.
            date_last: Date the task was last completed, or None.
            date_due: Date the task is due, or None.
            today: Reference date for derivation; defaults to `date.today()`.
                Injectable to keep construction deterministic in tests.

        Returns:
            A new, unsaved `Task` with derived dates and alert state.
        """
        date_last, date_due = cls.derive_dates(
            frequency, date_last, date_due, today
        )
        return cls(
            ship_id=ship_id,
            content=content,
            frequency=frequency,
            date_last=date_last,
            date_due=date_due,
            alert_state=AlertState.from_due_date(date_due),
        )
