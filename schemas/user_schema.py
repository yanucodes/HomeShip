"""Pydantic schema for User"""

from uuid import UUID
from typing import Annotated
from pydantic import (BaseModel, ConfigDict, EmailStr, StringConstraints,
                      field_validator)

from schemas.validators import no_at_sign


DisplayName = Annotated[str, StringConstraints(min_length=1, max_length=30)]


class UserBase(BaseModel):
    username: str
    display_name: DisplayName
    email: EmailStr


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
    password: str


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
    username: str | None = None
    display_name: DisplayName | None = None
    email: EmailStr | None = None
    password: str | None = None
