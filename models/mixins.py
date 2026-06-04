"""Reusable declarative mixins shared across ORM models."""

from datetime import date

from sqlalchemy import Date, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from models.alert_state import AlertState


class Alertable:
    """Mixin for ship items that carry a due date and an alert state.

    Both tasks and supplies surface an `AlertState` derived from an optional
    `date_due`, using the one shared alert vocabulary (see `AlertState`). This
    mixin keeps those two columns in a single place so the models don't drift
    apart.

    The column defaults to `AlertState.INACTIVE`; in practice the real value is
    computed at creation by each model's factory (`Task.scheduled`,
    `Supply.set_alert_on_creation`).

    Attributes:
        date_due: Deadline associated with the item (optional). Its exact
            meaning is model-specific — see each model's own docstring.
        alert_state: Urgency level for the item. Non-null; defaults to
            `AlertState.INACTIVE`.
    """

    date_due: Mapped[date | None] = mapped_column(Date)
    alert_state: Mapped[AlertState] = mapped_column(
        SqlEnum(
            AlertState,
            name="alert_state",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=AlertState.INACTIVE,
    )
