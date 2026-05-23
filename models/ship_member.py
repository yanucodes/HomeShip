"""ShipMember ORM model.

Maps to the ``ship_members`` table — the association object joining users
to ships. Identified by the composite key (`user_id`, `ship_id`) and
carries the user's `role` on that ship.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.ship import Ship
    from models.user import User


class ShipMember(Base):
    """Association object linking a user to a ship as a crew member.

    Carries the membership-specific data (`role`) that doesn't belong on
    either `User` or `Ship`. Identified by the composite primary key
    `(user_id, ship_id)` — a given user can appear on a given ship at most
    once.

    Attributes:
        user_id: Foreing key to `users.user_id`. Part of the composite
            primary key.
        ship_id: Foreing key to `ships.ship_id`. Part of the composite
            primary key.
        role: The user's role on this ship (e.g. "Captain"). Defaults to
            "Crew Member".
        user: The `User` this membership belongs to. Two-way mirror of
            `User.ship_memberships`.
        ship: The `Ship` this membership belongs to. Two-way mirror of
            `Ship.ship_memberships`.
    """
    __tablename__ = "ship_members"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    ship_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ships.ship_id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        String, nullable=False, default="Crew Member"
    )

    user: Mapped["User"] = relationship(back_populates="ship_memberships")
    ship: Mapped["Ship"] = relationship(back_populates="ship_memberships")