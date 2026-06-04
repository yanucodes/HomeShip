"""User endpoints."""
from fastapi import APIRouter, Depends, status

from dependencies import get_user_or_404, get_user_service
from models import User
from schemas import (ShipCreate, ShipMemberCreate, ShipRead, UserCreate,
                     UserRead, UserUpdate)
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
def get_user(user: User = Depends(get_user_or_404)):
    """
    Fetch user data.

    Args:
        user: User resolved from the path's `user_id` (404 if not found).

    Returns:
        The user serialized as `UserRead`.
    """
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_data: UserUpdate,
                user: User = Depends(get_user_or_404),
                service: UserService = Depends(get_user_service)):
    """
    Update user data.

    Args:
        user_data: Validated partial user fields from the request body.
        user: User resolved from the path's `user_id` (404 if not found).
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The updated user serialized as `UserRead`.
    """
    return service.update_user(user, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: User = Depends(get_user_or_404),
                service: UserService = Depends(get_user_service)):
    """
    Delete user with a given ID.

    Args:
        user: User resolved from the path's `user_id` (404 if not found).
        service: User service, injected by FastAPI via `get_user_service`.
    """
    service.delete_user(user)


@router.post("/{user_id}/ships", response_model=ShipRead,
             status_code=status.HTTP_201_CREATED)
def create_ship_for_user(ship_data: ShipCreate,
                         ship_member_data: ShipMemberCreate,
                         user: User = Depends(get_user_or_404),
                         service: UserService = Depends(get_user_service)):
    """
    Create a new ship for the user, with the user as its first crew member.

    Args:
        ship_data: Validated ship fields from the request body.
        ship_member_data: Validated crew-membership fields (e.g. role) from
            the request body.
        user: User resolved from the path's `user_id` (404 if not found);
            becomes the ship's first member.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The created ship serialized as `ShipRead`.
    """
    return service.create_ship_for_user(user, ship_data, ship_member_data)
