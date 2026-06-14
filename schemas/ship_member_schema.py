"""Pydantic schema for ShipMember"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from schemas.user_schema import UserPublic
from schemas.validators import bounded_str


Role = bounded_str(min_length=1, max_length=30)


class ShipMemberBase(BaseModel):
    role: Role


class ShipMemberCreate(ShipMemberBase):
    role: Role = "Crew Member"


class ShipMemberAdd(ShipMemberCreate):
    """Add an existing user to a ship's crew, identified by email."""
    email: EmailStr


class ShipMemberRead(ShipMemberBase):
    ship_id: UUID
    user: UserPublic
    model_config = ConfigDict(from_attributes=True)


class ShipMemberUpdate(ShipMemberBase):
    role: Role | None = None
