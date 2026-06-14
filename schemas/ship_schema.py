"""Pydantic schema for Ship"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.validators import bounded_str


ShipName = bounded_str(min_length=1, max_length=50)


class ShipBase(BaseModel):
    shipname: ShipName


class ShipCreate(ShipBase):
    pass


class ShipRead(ShipBase):
    ship_id: UUID
    start_date: date
    distance: float
    model_config = ConfigDict(from_attributes=True)


class ShipUpdate(BaseModel):
    """
    Editable plain attributes of a ship.

    Covers the free-form fields a user edits directly (currently `shipname`).
    The `start_date` is set on creation of the ship and is not editable.
    """
    shipname: ShipName | None = None
