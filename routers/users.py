"""User endpoints."""
from fastapi import APIRouter, Depends, status

from dependencies import (get_current_user, get_current_ship_membership_or_404,
                          get_current_users_ship_or_404, get_user_service)
from models import Ship, ShipMember, User
from schemas import (ShipCreate, ShipMemberCreate, ShipRead, ShipUpdate,
                     UserCreate, UserRead, UserUpdate)
from services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             operation_id="createUser")
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


@router.get("/me", response_model=UserRead, operation_id="getCurrentUser")
def get_me(user: User = Depends(get_current_user)):
    """
    Fetch user data.

    Args:
        user: User resolved via `get_current_user`.

    Returns:
        The user serialized as `UserRead`.
    """
    return user


@router.patch("/me", response_model=UserRead, operation_id="updateCurrentUser")
def update_user(user_data: UserUpdate,
                user: User = Depends(get_current_user),
                service: UserService = Depends(get_user_service)):
    """
    Update user data.

    Args:
        user_data: Validated partial user fields from the request body.
        user: User resolved via `get_current_user`.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The updated user serialized as `UserRead`.
    """
    return service.update_user(user, user_data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT,
               operation_id="deleteCurrentUser")
def delete_user(user: User = Depends(get_current_user),
                service: UserService = Depends(get_user_service)):
    """
    Delete current user.

    Args:
        user: User resolved via `get_current_user`.
        service: User service, injected by FastAPI via `get_user_service`.
    """
    service.delete_user(user)


@router.post("/me/ships", response_model=ShipRead,
             status_code=status.HTTP_201_CREATED, operation_id="createShip")
def create_ship_for_user(ship_data: ShipCreate,
                         ship_member_data: ShipMemberCreate,
                         user: User = Depends(get_current_user),
                         service: UserService = Depends(get_user_service)):
    """
    Create a new ship for the user, with the user as its first crew member.

    Args:
        ship_data: Validated ship fields from the request body.
        ship_member_data: Validated crew-membership fields (e.g. role) from
            the request body.
        user: User resolved via `get_current_user`; becomes the ship's first
            member.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The created ship serialized as `ShipRead`.
    """
    return service.create_ship_for_user(user, ship_data, ship_member_data)


@router.get("/me/ships", response_model=list[ShipRead],
            operation_id="listShips")
def get_ships(user: User = Depends(get_current_user),
              service: UserService = Depends(get_user_service)):
    """
    List all ships the user is a crew member of.

    Args:
        user: User resolved via `get_current_user`.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        The user's ships, each serialized as `ShipRead`. An empty list if
        the user isn't a member of any ship.
    """
    return service.get_ships(user)


@router.patch("/me/ships/{ship_id}", response_model=ShipRead,
              operation_id="updateShip")
def update_ship(ship_data: ShipUpdate,
                ship: Ship = Depends(get_current_users_ship_or_404),
                service: UserService = Depends(get_user_service)):
    """
    Update user's ship.

    Args:
        ship_data: Validated ship fields from the request body.
        ship: Ship to update.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        Updated Ship serialized as `ShipRead`.
    """
    return service.update_ship(ship, ship_data)


@router.delete("/me/ships/{ship_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               operation_id="leaveShip")
def leave_ship(
        membership: ShipMember = Depends(get_current_ship_membership_or_404),
        service: UserService = Depends(get_user_service)):
    """
    Remove the user's membership of the ship (they leave the crew).

    If the user is the ship's only member, the ship itself is deleted
    (taking its tasks and supplies with it via cascade).

    Args:
        membership: The current user's membership on the path's ship,
            resolved via `get_current_ship_membership_or_404` (404 if the
            user is not a member).
        service: User service, injected by FastAPI via `get_user_service`.
    """
    service.delete_ship_membership(membership)
