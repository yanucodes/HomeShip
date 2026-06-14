"""Pydantic schema for User"""

from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from schemas.validators import bounded_str


# Letters, digits, and the separators _ . - only. Forbids whitespace and '@',
# keeping usernames tidy and distinct from emails (login routes an identifier
# with '@' to email lookup, otherwise to username lookup).
Username = bounded_str(
    min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
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


class UserCreate(UserBase):
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


class UserUpdate(UserBase):
    username: Username | None = None
    display_name: DisplayName | None = None
    email: Email | None = None
    password: Password | None = None
