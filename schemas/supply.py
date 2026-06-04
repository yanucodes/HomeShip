"""Pydantic schema for Supply"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from models.alert_state import AlertState
from models.supply import StockState


class SupplyBase(BaseModel):
    name: str
    stock_state: StockState
    quantity: int | None = None
    date_due: date | None = None


class SupplyWrite(SupplyBase):
    """Base for request schemas: shared fields plus the input validation."""

    @field_validator("date_due")
    @classmethod
    def date_due_not_in_past(cls, value: date | None) -> date | None:
        """Deadline for buying a supply cannot be in the past."""
        if value is not None and value < date.today():
            raise ValueError("date_due must not be in the past")
        return value


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

