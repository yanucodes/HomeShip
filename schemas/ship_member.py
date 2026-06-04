"""Pydantic schema for ShipMember"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ShipMemberBase(BaseModel):
    role: str


class ShipMemberCreate(ShipMemberBase):
    role: str = ("Crew Member")


class ShipMemberAdd(ShipMemberCreate):
    """Add an existing user to a ship's crew, identified by email."""
    email: EmailStr


class ShipMemberRead(ShipMemberBase):
    user_id: UUID
    ship_id: UUID
    model_config = ConfigDict(from_attributes=True)


class ShipMemberUpdate(ShipMemberBase):
    role: str | None = None
