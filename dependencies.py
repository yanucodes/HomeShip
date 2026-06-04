"""FastAPI dependency wiring: session -> repositories -> services.

Each request gets one session. These providers assemble the repositories on top
of that session and hand a ready-to-use service to the endpoint, so routes
never touch the ORM or construct repositories themselves.
"""
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_session
from models import Ship
from repositories import (
    ShipMemberRepository,
    ShipRepository,
    SupplyRepository,
    TaskRepository,
    UserRepository,
)
from services import ShipService, UserService


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(
        ship_repository=ShipRepository(session),
        ship_member_repository=ShipMemberRepository(session),
        user_repository=UserRepository(session),
    )


def get_ship_service(session: Session = Depends(get_session)) -> ShipService:
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
