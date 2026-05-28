"""Pydantic schema for Ship"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShipBase(BaseModel):
    shipname: str
    start_date: date


class ShipCreate(ShipBase):
    pass


class ShipRead(ShipBase):
    ship_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ShipUpdate(ShipBase):
    shipname: str | None = None
    start_date: date | None = None
