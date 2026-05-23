"""User ORM model.

Maps to the `users` table. A user is identified by a UUID primary key and
authenticates with a username/email plus a bcrypt password hash. The plain
password is never stored — only `password_hash`.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.ship_members import ShipMember


class User(Base):
    """Application user.

    Attributes:
        id: Server-side UUID primary key. Generated in Python via `uuid.uuid4`
            on insert if the caller does not provide one.
        username: Unique, non-null display handle used for login.
        email: Unique, non-null email address used for login and contact.
        password_hash: bcrypt hash of the user's password. The raw password
            must never be persisted; hash it at the auth layer before assigning.
    """

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    ship_memberships: Mapped[list["ShipMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )