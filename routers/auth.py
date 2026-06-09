"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import get_user_service
from schemas import Token
from security import create_access_token
from services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model = Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(),
          service: UserService = Depends(get_user_service)):
    """Log in with email and password and issue a JWT access token.

    Args:
        form_data: OAuth2 password-flow form. Per the OAuth2 spec the login
            field is named `username`, but this app authenticates by email,
            so `form_data.username` carries the user's email address.
        service: User service, injected by FastAPI via `get_user_service`.

    Returns:
        A `Token` with the signed access token and `token_type` "bearer".

    Raises:
        HTTPException: 401 if no user matches the email or the password is
            wrong.
    """
    user = service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(401, "Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(str(user.user_id)))