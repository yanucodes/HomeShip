"""Pydantic schema for Supply"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from models.alert_state import AlertState
from models.supply import StockState
from schemas.validators import non_negative, not_in_past


class SupplyBase(BaseModel):
    name: str
    stock_state: StockState
    quantity: int | None = None
    date_due: date | None = None


class SupplyWrite(SupplyBase):
    """Base for request schemas: shared fields plus the input validation."""

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, value: int | None) -> int | None:
        """A supply's quantity on hand cannot be negative."""
        return non_negative(value, field_description="quantity")

    @field_validator("date_due")
    @classmethod
    def date_due_not_in_past(cls, value: date | None) -> date | None:
        """Deadline for buying a supply cannot be in the past."""
        return not_in_past(value, date_description="date_due")


class SupplyCreate(SupplyWrite):
    stock_state: StockState = StockState.OUT_OF_STOCK


class SupplyRead(SupplyBase):
    supply_id: UUID
    ship_id: UUID
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)


class SupplyUpdate(SupplyWrite):
    name: str | None = None
    stock_state: StockState | None = None
