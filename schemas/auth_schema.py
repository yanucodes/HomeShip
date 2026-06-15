"""Pydantic schema for authentication."""

import uuid

from pydantic import BaseModel


class Token(BaseModel):
    """JWT access token issued by the login endpoint."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT payload: the authenticated user's id."""
    user_id: uuid.UUID | None = None
