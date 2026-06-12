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
        start_date: Date the ship's journey began. Used to compute distance
            traveled (one light year per alert-free day).
        distance: Light years travelled so far. Recomputed and overwritten by
            the daily cron job (one light year per alert-free day), stored
            rounded to one decimal place. Non-null; defaults to 0.0 for a
            ship that has just set off.
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
    shipname: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    ship_memberships: Mapped[list["ShipMember"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )
    supplies: Mapped[list["Supply"]] = relationship(
        back_populates="ship", cascade="all, delete-orphan"
    )
