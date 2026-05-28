"""Pydantic schema for User"""

from uuid import UUID
from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints


DisplayName = Annotated[str, StringConstraints(min_length=1, max_length=30)]


class UserBase(BaseModel):
    username: str
    display_name: DisplayName
    email: EmailStr


class UserCreate(UserBase):
    display_name: DisplayName | None = None
    password: str


class UserRead(UserBase):
    user_id: UUID
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(UserBase):
    username: str | None = None
    display_name: DisplayName | None = None
    email: EmailStr | None = None
    password: str | None = None
