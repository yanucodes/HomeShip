"""Pydantic schema for ShipMember"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShipMemberBase(BaseModel):
    role: str


class ShipMemberCreate(ShipMemberBase):
    role: str = "Crew Member"


class ShipMemberRead(ShipMemberBase):
    user_id: UUID
    ship_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ShipMemberUpdate(ShipMemberBase):
    role: str | None = None