"""User endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_user_service
from schemas import UserCreate, UserRead
from services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate,
                service: UserService = Depends(get_user_service)):
    """Register a new user.

    Args:
        user_data: Validated signup fields from the request body.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The created user serialized as `UserRead` — `password_hash` is
        dropped by the response model and never leaves this boundary.
    """
    return service.create_user(user_data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID,
             service: UserService = Depends(get_user_service)):
    """
    Fetch user data.

    Args:
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The user serialized as `UserRead`.
    """
    user = service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID,
                service: UserService = Depends(get_user_service)):
    """
    Delete user with a given ID.

    Args:
        service: User service, injected by FastAPI via `get_user_service`.
    """
    user = service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404)
    service.delete_user(user)
