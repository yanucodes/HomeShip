"""Pydantic schema for Supply"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.alert_state import AlertState

class SupplyBase(BaseModel):
    name: str
    quantity: int | None = None


class SupplyCreate(SupplyBase):
    in_stock: bool = True


class SupplyRead(SupplyBase):
    supply_id: UUID
    ship_id: UUID
    in_stock: bool
    alert_state: AlertState
    model_config = ConfigDict(from_attributes=True)


class SupplyUpdate(BaseModel):
    name: str | None = None
    in_stock: bool | None = None
    quantity: int | None = None
