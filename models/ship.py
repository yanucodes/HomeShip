"""Ship ORM model.

Maps to the `ships` table. A ship represents a household — the shared
"spaceship" that crew members (users) maintain together.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base

if TYPE_CHECKING:
    from models.ship_member import ShipMember
    from models.supply import Supply
    from models.task import Task


class Ship(Base):
    """A household, modeled as a spaceship shared by its crew.

    Attributes:
        ship_id: Server-side UUID primary key. Generated in Python via
            `uuid.uuid4` on insert if the caller does not provide one.
        shipname: Non-null display name of the ship.
        start_date: Date the current journey began. Set server-side to today
            when the ship is created, and reset to today each time the ship
            auto-destructs, so it always marks the start of the ongoing,
            uninterrupted journey.
        distance: Light years travelled so far. Recomputed and overwritten by
            the daily cron job (one light year per alert-free day), stored
            rounded to one decimal place. Non-null; defaults to 0.0 for a
            ship that has just set off.
        timezone: IANA timezone name of the household (e.g. "Europe/Berlin"),
            used by the daily cron to roll the ship's day over at the crew's
            local rollover hour. Non-null; defaults to "UTC".
        last_advanced_on: Ship-local date on which the daily cron last advanced
            this ship, or None if it has never been advanced. The hourly cron
            uses it to advance each ship exactly once per local day (and to
            catch up a ship whose rollover-hour run was missed).
        ship_memberships: Crew membership rows for this ship. Two-way mirror
            of `ShipMember.ship`.
        tasks: Tasks belonging to this ship. Two-way mirror of `Task.ship`.
        supplies: Supplies tracked by this ship. Two-way mirror of
            `Supply.ship`.
    """

    __tablename__ = "ships"

    ship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    shipname: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="UTC")
    last_advanced_on: Mapped[date | None] = mapped_column(Date)

    ship_memberships: Mapped[list["ShipMember"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )
    supplies: Mapped[list["Supply"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )

    @property
    def current_alerts(self) -> dict[AlertState, int]:
        """Count the ship's tasks and supplies at each alert level.

        Returns:
            A mapping of every `AlertState` to the number of tasks and
            supplies currently in that state. Levels with no items map to 0.
        """
        counts = {state: 0 for state in AlertState}
        for item in (*self.tasks, *self.supplies):
            counts[item.alert_state] += 1
        return counts

    @property
    def current_speed(self) -> float | None:
        """Current travel speed in light years per day, from the alert mix.

        The ship cruises at the fraction of its tracked items that are on
        track — `green / (green + yellow)`. A single red alert halts progress,
        and an auto-destruct wipes it out entirely.

        Returns:
            `None` if any item is at AUTO_DESTRUCT (progress destroyed), `0.0`
            if any item is at RED (progress frozen), otherwise the green
            fraction of active (green + yellow) items, or `1.0` when there are
            no active items to weigh the ship down.
        """
        alerts = self.current_alerts
        if alerts[AlertState.AUTO_DESTRUCT]:
            return None
        if alerts[AlertState.RED]:
            return 0.0
        active = alerts[AlertState.GREEN] + alerts[AlertState.YELLOW]
        if not active:
            return 1.0
        return alerts[AlertState.GREEN] / active

    def get_daily_changes(self, today: date | None = None) -> dict:
        """Compute the ship's changes for one day of the journey.

        Advances `distance` by the day's `current_speed`. When any item has hit
        AUTO_DESTRUCT (speed `None`) the journey is wiped: `distance` resets to
        zero and `start_date` resets to today, so the ship begins a fresh
        journey from the day of the disaster.

        Args:
            today: Reference date for an auto-destruct reset; defaults to
                `date.today()`. Injectable to keep the logic deterministic in
                tests.

        Returns:
            A change dict for `BaseRepository.update`. On an auto-destruct
            reset, `distance` (0.0) and `start_date` (today); otherwise just
            the new `distance` (current distance plus the day's speed).
        """
        speed = self.current_speed
        if speed is None:
            return {"distance": 0.0, "start_date": today or date.today()}
        return {"distance": self.distance + speed}