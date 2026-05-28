"""Pydantic schema for Supply"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.alert_state import AlertState
from models.supply import StockState


class SupplyBase(BaseModel):
    name: str
    stock_state: StockState
    quantity: int | None = None
    date_due: date | None = None


class SupplyCreate(SupplyBase):
    stock_state: StockState = StockState.OUT_OF_STOCK


class SupplyRead(SupplyBase):
    supply_id: UUID
    ship_id: UUID
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)


class SupplyUpdate(SupplyBase):
    name: str | None = None
    stock_state: StockState | None = None

