"""Pydantic schema for Ship"""

from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from models.alert_state import AlertState
from schemas.ship_member_schema import ShipMemberRead
from schemas.supply_schema import SupplyRead
from schemas.task_schema import TaskRead
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


class ShipDashboard(ShipRead):
    """Everything a client needs to render the ship's console in one request.

    Extends `ShipRead` with the ship's derived journey/alert data and its
    nested crew, task and supply collections. The aliased fields are read off
    the `Ship` ORM object's properties and relationships; they serialize under
    the plain field names.
    """
    condition: AlertState = Field(validation_alias="current_condition")
    current_speed: float | None
    alert_counts: dict[AlertState, int] = Field(
        validation_alias="current_alerts")
    members: list[ShipMemberRead] = Field(validation_alias="ship_memberships")
    tasks: list[TaskRead]
    supplies: list[SupplyRead]


class ShipUpdate(BaseModel):
    """
    Editable plain attributes of a ship.

    Covers the free-form fields a user edits directly (currently `shipname`).
    The `start_date` is set on creation of the ship and is not editable.
    """
    shipname: ShipName | None = None
