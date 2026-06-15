"""Pydantic schema for ShipMember"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from schemas.user_schema import UserPublic
from schemas.validators import bounded_str


Role = bounded_str(min_length=1, max_length=30)


class ShipMemberBase(BaseModel):
    """Crew-membership fields shared by the read and write schemas."""
    role: Role


class ShipMemberCreate(ShipMemberBase):
    """Membership fields for a ship's own crew; role defaults to Crew Member."""
    role: Role = "Crew Member"


class ShipMemberAdd(ShipMemberCreate):
    """Add an existing user to a ship's crew, identified by email."""
    email: EmailStr


class ShipMemberRead(ShipMemberBase):
    """Crew-member fields returned to clients, with public user identity."""
    ship_id: UUID
    user: UserPublic
    model_config = ConfigDict(from_attributes=True)


class ShipMemberUpdate(ShipMemberBase):
    """Fields accepted when updating a crew member; all optional."""
    role: Role | None = None
