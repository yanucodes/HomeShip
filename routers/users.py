"""User endpoints."""
from fastapi import APIRouter, Depends, status

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
