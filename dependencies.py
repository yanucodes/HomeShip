"""FastAPI dependency wiring: session -> repositories -> services.

Each request gets one session. These providers assemble the repositories on top
of that session and hand a ready-to-use service to the endpoint, so routes
never touch the ORM or construct repositories themselves.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_session
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
    )
