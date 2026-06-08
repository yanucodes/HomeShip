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


class ShipUpdate(BaseModel):
    """
    Editable plain attributes of a ship.

    Covers the free-form fields a user edits directly (currently `shipname`).
    The `start_date` is set on creation of the ship and is not editable.
    """
    shipname: str | None = None
