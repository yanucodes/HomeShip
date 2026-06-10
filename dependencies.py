"""FastAPI dependency wiring: session -> repositories -> services.

Each request gets one session. These providers assemble the repositories on top
of that session and hand a ready-to-use service to the endpoint, so routes
never touch the ORM or construct repositories themselves.
"""
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from database import get_session
from models import Ship, ShipMember, Supply, Task, User
from repositories import (
    ShipMemberRepository,
    ShipRepository,
    SupplyRepository,
    TaskRepository,
    UserRepository,
)
from security import decode_access_token
from services import ShipService, UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Assemble a UserService on top of the request-scoped session.

    Args:
        session: Request-scoped session, injected via `get_session`.

    Returns:
        A UserService wired with the repositories it needs.
    """
    return UserService(
        ship_repository=ShipRepository(session),
        ship_member_repository=ShipMemberRepository(session),
        user_repository=UserRepository(session),
    )


def get_current_user(token: str = Depends(oauth2_scheme),
                     service: UserService = Depends(get_user_service)) -> User:
    """Resolve the request's bearer token to the authenticated User.

    Args:
        token: The JWT access token from the `Authorization: Bearer` header,
            extracted by `oauth2_scheme`.
        service: UserService, injected via `get_user_service`.

    Returns:
        The User identified by the token's `sub` claim.

    Raises:
        HTTPException: 401 if the token is missing, invalid, expired, not an
            access token, or its user no longer exists.
    """
    credentials_error = HTTPException(
        status_code=401,
        detail="Could not validate  credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        user_id = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error
    user = service.get_user_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


def get_ship_service(session: Session = Depends(get_session)) -> ShipService:
    """Assemble a ShipService on top of the request-scoped session.

    Args:
        session: Request-scoped session, injected via `get_session`.

    Returns:
        A ShipService wired with the repositories it needs.
    """
    return ShipService(
        ship_repository=ShipRepository(session),
        ship_member_repository=ShipMemberRepository(session),
        task_repository=TaskRepository(session),
        supply_repository=SupplyRepository(session),
        user_repository=UserRepository(session),
    )


def get_user_or_404(user_id: uuid.UUID,
                    service: UserService = Depends(get_user_service)) -> User:
    """Resolve a path's `user_id` to a User, or raise 404.

    Args:
        user_id: User identifier taken from the request path.
        service: UserService, injected via `get_user_service`.

    Returns:
        The User matching `user_id`.

    Raises:
        HTTPException: 404 if no user matches `user_id`.
    """
    user = service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_ship_or_404(ship_id: uuid.UUID,
                    service: ShipService = Depends(get_ship_service)) -> Ship:
    """Resolve a path's `ship_id` to a Ship, or raise 404.

    Args:
        ship_id: Ship identifier taken from the request path.
        service: ShipService, injected via `get_ship_service`.

    Returns:
        The Ship matching `ship_id`.

    Raises:
        HTTPException: 404 if no ship matches `ship_id`.
    """
    ship = service.get_ship_by_id(ship_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Ship not found")
    return ship


def get_ship_membership_or_404(
        user: User = Depends(get_user_or_404),
        ship: Ship = Depends(get_ship_or_404),
        service: UserService = Depends(get_user_service),
) -> ShipMember:
    """Resolve the path's (user_id, ship_id) to a ShipMember, or raise 404.

    Args:
        user: User resolved from the path, injected via `get_user_or_404`.
        ship: Ship resolved from the path, injected via `get_ship_or_404`.
        service: UserService, injected via `get_user_service`.

    Returns:
        The ShipMember linking `user` to `ship`.

    Raises:
        HTTPException: 404 if `user` is not a member of `ship`.
    """
    membership = service.get_ship_membership(user, ship)
    if membership is None:
        raise HTTPException(status_code=404,
                            detail="User is not a member of this ship.")
    return membership


def get_current_users_ship_or_404(
        user: User = Depends(get_current_user),
        ship: Ship = Depends(get_ship_or_404),
        service: UserService = Depends(get_user_service),
) -> Ship:
    """Resolve the path's ship and confirm the authenticated user is a member
    of it.

    Args:
        user: The authenticated user, via `get_current_user`.
        ship: Ship resolved from the path, injected via `get_ship_or_404`.
        service: UserService, injected via `get_user_service`.

    Returns:
        Ship if it exists and user is a member.

    Raises:
        HTTPException: 404 if the current `user` is not a member of `ship`.
    """
    membership = service.get_ship_membership(user, ship)
    if membership is None:
        raise HTTPException(status_code=404,
                            detail="You are not a member of this ship.")
    return ship


def get_task_or_404(task_id: uuid.UUID,
                    ship: Ship = Depends(get_ship_or_404),
                    service: ShipService = Depends(get_ship_service)) -> Task:
    """Resolve a path's `task_id` to a Task on the path's ship, or raise 404.

    Depends on `get_ship_or_404`, so the ship is validated first: a missing
    ship raises "Ship not found". The task must belong to that ship,
    so a `task_id` from another ship resolves to a
    "Task not found" rather than leaking across ships.

    Args:
        task_id: Task identifier taken from the request path.
        ship: Ship resolved from the path, injected via `get_ship_or_404`.
        service: ShipService, injected via `get_ship_service`.

    Returns:
        The Task matching `task_id` on `ship`.

    Raises:
        HTTPException: 404 if no task matches `task_id` on `ship`.
    """
    task = service.get_task(ship, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def get_supply_or_404(supply_id: uuid.UUID,
                      ship: Ship = Depends(get_ship_or_404),
                      service: ShipService = Depends(get_ship_service)) -> (
        Supply):
    """Resolve a path's `supply_id` to a Supply on the path's ship, or 404.

    Depends on `get_ship_or_404`, so the ship is validated first: a missing
    ship raises "Ship not found". The supply must belong to that ship,
    so a `supply_id` from another ship resolves to a "Supply not found"
    rather than leaking across ships.

    Args:
        supply_id: Supply identifier taken from the request path.
        ship: Ship resolved from the path, injected via `get_ship_or_404`.
        service: ShipService, injected via `get_ship_service`.

    Returns:
        The Supply matching `supply_id` on `ship`.

    Raises:
        HTTPException: 404 if no supply matches `supply_id` on `ship`.
    """
    supply = service.get_supply(ship, supply_id)
    if supply is None:
        raise HTTPException(status_code=404, detail="Supply not found")
    return supply
