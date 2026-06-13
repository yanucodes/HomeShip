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

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.alert_state import AlertState
from models.base import Base
from models.mixins import Alertable

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


class Supply(Alertable, Base):
    """Supply item tracked by a ship's crew.

    `date_due` and `alert_state` come from the `Alertable` mixin.

    Attributes:
        supply_id: UUID primary key. Generated in Python via `uuid.uuid4`
            on insert if the caller does not provide one.
        ship_id: Foreign key to `ships.ship_id`.
        name: Non-null display name of the supply (e.g. "Shampoo").
        stock_state: Whether the item is currently available in the
            household in sufficient amount. Defaults to
            `StockState.OUT_OF_STOCK`
        quantity: How many units are on hand (optional).
        date_due: Deadline for buying the item (optional).
        alert_state: Urgency level for this supply, derived at creation by
            `set_alert_on_creation`. The column defaults to
            `AlertState.INACTIVE`.
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
        default=StockState.OUT_OF_STOCK
    )
    quantity: Mapped[int | None] = mapped_column(Integer)

    ship: Mapped["Ship"] = relationship(back_populates="supplies")

    @staticmethod
    def derive_alert(stock_state: StockState, date_due: date | None = None,
                     today: date | None = None) -> AlertState:
        """
        Derive alert state from `date_due` proximity, or `stock_state` when
        there is no deadline.

        The presence of a `date_due` selects the mode:

        * No deadline: the alert reflects the stock level alone — `green` if
          in stock, `yellow` if running low, `red` if out of stock.
        * Deadline set: the alert reflects how close the deadline is,
          regardless of stock level — `green` while it is two or more days
          away, `yellow` the day before, `red` on the day itself, and
          `auto-destruct` once it has passed.

        Args:
            stock_state: Whether the item is currently available in the
                household in sufficient amount. Used only when `date_due` is
                None.
            date_due: Deadline for buying the item, or None.
            today: Current date. Defaults to `date.today()`.

        Returns:
            Derived `AlertState` for the item.
        """
        if today is None:
            today = date.today()

        if date_due is None:
            if stock_state == StockState.IN_STOCK:
                return AlertState.GREEN
            if stock_state == StockState.RUNNING_LOW:
                return AlertState.YELLOW
            return AlertState.RED

        if today > date_due:
            return AlertState.AUTO_DESTRUCT
        if today == date_due:
            return AlertState.RED
        if date_due == today + timedelta(days=1):
            return AlertState.YELLOW
        return AlertState.GREEN

    @classmethod
    def set_alert_on_creation(cls, *, ship_id: uuid.UUID, name: str,
                              stock_state: StockState | None = None,
                              quantity: int | None = None,
                              date_due: date | None = None,
                              today: date | None = None) -> "Supply":
        """
        Build a Supply with its alert state derived from the given fields.

        Encapsulates "how to construct a valid supply" in one place. The alert
        state is derived from `stock_state` and `date_due` via `derive_alert`.

        Args:
            ship_id: ID of the ship the supply belongs to.
            name: Display name of the supply (e.g. "Shampoo").
            stock_state: Current stock level. Defaults to
                `StockState.OUT_OF_STOCK` — supplies are usually added the
                moment the crew runs out.
            quantity: Units on hand, or None.
            date_due: Deadline for buying the item, or None.
            today: Reference date for derivation; defaults to `date.today()`.
                Injectable to keep construction deterministic in tests.

        Returns:
            A new, unsaved `Supply` with derived alert state.
        """
        stock_state = stock_state or StockState.OUT_OF_STOCK
        return cls(
            ship_id=ship_id,
            name=name,
            stock_state=stock_state,
            quantity=quantity,
            date_due=date_due,
            alert_state=cls.derive_alert(stock_state, date_due, today),
        )

    def get_changes_on_stock_state_change(
        self, stock_state: StockState, today: date | None = None
    ) -> dict:
        """Compute the field changes when the supply's stock state changes.

        Re-derives the alert from the new stock state and the supply's
        existing deadline via `derive_alert`, so the signal stays consistent
        with the stock level. `quantity` is left untouched — it is an
        independent dimension that does not feed the alert.

        Args:
            stock_state: New stock state for the supply.
            today: Reference date for derivation; defaults to `date.today()`.
                Injectable to keep the logic deterministic in tests.

        Returns:
            A `{field: value}` dict for `stock_state` and `alert_state`.
        """
        return {
            "stock_state": stock_state,
            "alert_state": self.derive_alert(stock_state, self.date_due, today)
        }

    def get_changes_on_reschedule(
        self, date_due: date, today: date | None = None
    ) -> dict:
        """Compute the field changes when the supply's deadline is rescheduled.

        Re-derives the alert from the supply's current stock state and the new
        deadline via `derive_alert`, so moving the buy-by date adjusts the
        urgency.

        Args:
            date_due: New buy-by deadline for the supply, already validated by
                the `SupplyReschedule` schema.
            today: Reference date for derivation; defaults to `date.today()`.
                Injectable to keep the logic deterministic in tests.

        Returns:
            A `{field: value}` dict for `date_due` and `alert_state`.
        """
        return {
            "date_due": date_due,
            "alert_state": self.derive_alert(self.stock_state, date_due, today)
        }

    def get_changes_on_deactivation(self) -> dict:
        """Return the field changes when the supply is deactivated.

        Deactivating stops tracking the supply: its buy-by deadline and
        quantity are cleared and its alert drops to INACTIVE. The stock state
        is kept (it is non-nullable and no longer feeds the alert once the
        supply is untracked).

        Returns:
            A `{field: value}` dict for `date_due`, `quantity`, and
            `alert_state`.
        """
        return {
            "date_due": None,
            "quantity": None,
            "alert_state": AlertState.INACTIVE
        }

    def get_daily_changes(self, today: date | None = None) -> dict:
        """Compute the field changes for one day's deadline decay.

        The cron only concerns deadline-driven supplies: a stock-only supply's
        alert is already kept current synchronously by
        `get_changes_on_stock_state_change`, so there is nothing to recompute
        when `date_due` is None. For a supply with a deadline, re-deriving via
        `derive_alert` lets it tick closer over time (GREEN -> YELLOW -> RED ->
        AUTO_DESTRUCT). Inactive supplies are skipped outright as an invariant
        guard, so a stray `date_due` can never resurrect a deactivated supply.

        Args:
            today: Reference date; defaults to `date.today()`. Injectable to
                keep the logic deterministic in tests.

        Returns:
            A `{field: value}` dict for `alert_state`, or an empty dict when
            the supply is inactive, has no deadline, or its alert is unchanged.
        """
        if self.date_due is None or self.alert_state == AlertState.INACTIVE:
            return {}
        new_alert = self.derive_alert(self.stock_state, self.date_due, today)
        return {
            "alert_state":
        } if new_alert != self.alert_state else {}
