"""Supply ORM model.

A supply is any item users regularly buy for their household (e.g.
groceries, stationery, toiletries).

Maps to the `supplies` table. See `AlertState` in `models.alert_state`
for the meaning of each alert level.
"""

from datetime import date, timedelta
import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base

if TYPE_CHECKING:
    from models.ship import Ship


class StockState(enum.Enum):
    """Whether a supply is sufficient, running low, or out.

    Members:
        IN_STOCK: Sufficient amount of supplies.
        RUNNING_LOW: Insufficient amount of supplies.
        OUT_OF_STOCK: No supplies left.
    """
    IN_STOCK = "in_stock"
    RUNNING_LOW = "running_low"
    OUT_OF_STOCK = "out_of_stock"


class Supply(Base):
    """Supply item tracked by a ship's crew.

    Attributes:
        supply_id: UUID primary key. Generated in Python via `uuid.uuid4`
            on insert if the caller does not provide one.
        ship_id: Foreign key to `ships.ship_id`.
        name: Non-null display name of the supply (e.g. "Shampoo").
        stock_state: Whether the item is currently available in the
            household in sufficient amount.
        quantity: How many units are on hand (optional).
        date_due: Deadline for buying the item (optional).
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
    stock_state: Mapped[StockState] = mapped_column(
        SqlEnum(StockState, name="stock_state",
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                ),
        nullable=False,
        default=StockState.IN_STOCK
    )
    quantity: Mapped[int | None] = mapped_column(Integer)
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

    ship: Mapped["Ship"] = relationship(back_populates="supplies")

    @staticmethod
    def derive_alert(stock_state: StockState, date_due: date | None = None,
                     today: date | None = None) -> AlertState:
        """
        Derive alert state based on `stock_state` and `date_due`.

        Alert is `green` if the item is in stock, `yellow` if the item is
        running low, or out of stock with a `date_due` more than a day away.
        It is `red` if the item is out of stock and no `date_due` or the
        deadline is close — `date_due` is today or tomorrow — so the crew is
        warned before it's too late to act. It is `auto-destruct` if the item
        is out of stock and `date_due` has already passed.

        Args:
            stock_state: Whether the item is currently available in the
                household in sufficient amount.
            date_due: Deadline for buying the item.
            today: Current date. Defaults to `date.today()`.

        Returns:
            Derived `AlertState` for the item.
        """
        if today is None:
            today = date.today()

        if stock_state == StockState.IN_STOCK:
            return AlertState.GREEN
        elif stock_state == StockState.RUNNING_LOW:
            return AlertState.YELLOW
        else:
            if date_due is not None and date_due < today:
                return AlertState.AUTO_DESTRUCT
            elif date_due is None or date_due <= today + timedelta(days=1):
                return AlertState.RED
            else:
                return AlertState.YELLOW