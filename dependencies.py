"""FastAPI dependency wiring: session -> repositories -> services.

Each request gets one session. These providers assemble the repositories on top
of that session and hand a ready-to-use service to the endpoint, so routes
never touch the ORM or construct repositories themselves.
"""
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_session
from models import Ship, Supply, Task
from repositories import (
    ShipMemberRepository,
    ShipRepository,
    SupplyRepository,
    TaskRepository,
    UserRepository,
)
from services import ShipService, UserService


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


def get_ship_or_404(
    ship_id: uuid.UUID,
    service: ShipService = Depends(get_ship_service),
    ) -> Ship:
    """Resolve a path's `ship_id` to a Ship, or raise 404.

    Lets ship-scoped routes receive an already-validated `Ship` instead of
    repeating the lookup-or-404 dance. `get_ship_service` is shared with the
    endpoint within a request (FastAPI caches dependencies), so this adds no
    extra session or query wiring.
    """
    ship = service.get_ship_by_id(ship_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Ship not found")
    return ship


def get_task_or_404(task_id: uuid.UUID,
    ship: Ship = Depends(get_ship_or_404),
    service: ShipService = Depends(get_ship_service)) -> Task:
    """Resolve a path's `task_id` to a Task on the path's ship, or raise 404.

    Depends on `get_ship_or_404`, so the ship is validated first: a missing
    ship raises "Ship not found". The task must belong to that ship,
    so a `task_id` from another ship resolves to a
    "Task not found" rather than leaking across ships.
    """
    task = service.get_task(ship, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def get_supply_or_404(supply_id: uuid.UUID,
    ship: Ship = Depends(get_ship_or_404),
    service: ShipService = Depends(get_ship_service)) -> Supply:
    """Resolve a path's `supply_id` to a Supply on the path's ship, or 404.

    Depends on `get_ship_or_404`, so the ship is validated first: a missing
    ship raises "Ship not found". The supply must belong to that ship,
    so a `supply_id` from another ship resolves to a "Supply not found"
    rather than leaking across ships.
    """
    supply = service.get_supply(ship, supply_id)
    if supply is None:
        raise HTTPException(status_code=404, detail="Supply not found")
    return supply
