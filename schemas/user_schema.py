"""Pydantic schema for User"""

from uuid import UUID
from typing import Annotated
from pydantic import (BaseModel, ConfigDict, EmailStr, StringConstraints,
                      field_validator)

from schemas.validators import bounded_str, no_at_sign


Username = bounded_str(min_length=3, max_length=30)
DisplayName = bounded_str(min_length=1, max_length=30)
# Passwords keep surrounding whitespace — it is significant, so do not strip.
Password = bounded_str(min_length=8, max_length=128, strip_whitespace=False)
# RFC 5321 caps an email address at 254 characters; EmailStr handles the
# format (and rejects empty), so only the upper bound is added here.
Email = Annotated[EmailStr, StringConstraints(max_length=254)]


class UserBase(BaseModel):
    username: Username
    display_name: DisplayName
    email: Email


class UserWrite(UserBase):
    """Base class for UserCreate and UserUpdate where username should be
    validated."""
    @field_validator("username")
    @classmethod
    def username_has_no_at_sign(cls, value: str | None) -> str | None:
        """Usernames must not contain '@', so login can distinguish a
        username from an email address."""
        return no_at_sign(value, field_description="username")


class UserCreate(UserWrite):
    display_name: DisplayName | None = None
    password: Password


class UserRead(UserBase):
    user_id: UUID
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Public-facing user identity, safe to expose to other crew members.

    Carries only the fields needed to display a person (no email or other
    private profile data).
    """
    user_id: UUID
    display_name: DisplayName
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(UserWrite):
    username: Username | None = None
    display_name: DisplayName | None = None
    email: Email | None = None
    password: Password | None = None
