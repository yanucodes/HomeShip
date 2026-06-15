"""Service-layer tests for UserService."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring,redefined-outer-name
from sqlalchemy.orm import Session

from repositories import (
    ShipMemberRepository,
    ShipRepository,
    UserRepository,
)
from schemas import UserCreate
from services import UserService


def build_user_service(session: Session) -> UserService:
    return UserService(
        ship_repository=ShipRepository(session),
        ship_member_repository=ShipMemberRepository(session),
        user_repository=UserRepository(session),
    )


def test_create_user_stores_hash_not_raw_password(session, test_user_data):
    service = build_user_service(session)
    data = test_user_data["all_fields_correct"]

    user = service.create_user(UserCreate(**data))

    assert user.user_id is not None
    # The raw password must never be persisted.
    assert user.password_hash != data["password"]


def test_create_user_defaults_display_name_to_username(
        session, test_user_data):
    service = build_user_service(session)
    data = test_user_data["all_fields_correct"]

    user = service.create_user(UserCreate(**data))

    assert user.display_name == data["username"].capitalize()
