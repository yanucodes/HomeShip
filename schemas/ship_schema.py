"""Pydantic schema for Ship"""

from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict

from schemas.validators import bounded_str, valid_timezone


ShipName = bounded_str(min_length=1, max_length=50)
# An IANA timezone name (e.g. "Europe/Berlin"), validated against zoneinfo.
Timezone = Annotated[str, AfterValidator(valid_timezone)]


class ShipBase(BaseModel):
    """Editable ship fields shared by the read and write schemas."""
    shipname: ShipName
    timezone: Timezone = "UTC"


class ShipCreate(ShipBase):
    """Fields accepted when creating a ship."""


class ShipRead(ShipBase):
    """Ship fields returned to clients, including derived journey data."""
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
