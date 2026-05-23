"""Supply ORM model.

A supply is any item users regularly buy for their household (e.g.
groceries, stationery, toiletries).

Maps to the `supplies` table. See `AlertState` in `models.alert_state`
for the meaning of each alert level.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base

if TYPE_CHECKING:
    from models.ship import Ship


class Supply(Base):
    """Supply item tracked by a ship's crew.

    Attributes:
        supply_id: UUID primary key. Generated in Python via `uuid.uuid4`
            on insert if the caller does not provide one.
        ship_id: Foreign key to `ships.ship_id`.
        name: Non-null display name of the supply (e.g. "Shampoo").
        in_stock: Whether the item is currently available in the household.
        quantity: How many units are on hand. Null when not tracked
            numerically (some items are tracked only by `in_stock`).
        alert_state: Urgency level for this supply. Defaults to
            `AlertState.GREEN`.
        ship: The `Ship` this supply belongs to. Two-way mirror of
            `Ship.supplies`.
    """

    __tablename__ = "supplies"

    supply_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ships.ship_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer)
    alert_state: Mapped[AlertState] = mapped_column(
        SqlEnum(
            AlertState,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=AlertState.GREEN,
    )

    ship: Mapped["Ship"] = relationship(back_populates="supplies")
