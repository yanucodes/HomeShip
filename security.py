"""Authentication and password helpers."""
from datetime import datetime, timedelta, timezone
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from config import settings

_password_hasher = PasswordHasher()

# Precomputed hash of a throwaway value. `verify_dummy` verifies against it so
# an unknown-account login costs the same as a real one (see that function).
_DUMMY_HASH = _password_hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    """Turn a raw password into the value stored in `User.password_hash`.

    Args:
        password: The plain-text password from the signup request.

    Returns:
        An Argon2 hash string to persist as `password_hash`.
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plain-text password against a stored hash.

    Args:
        password: The plain-text password from the login request.
        password_hash: The value previously stored in `User.password_hash`.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy() -> None:
    """Run a throwaway verification against a dummy hash to equalize timing.

    Call this when no user matched the login identifier, so an unknown
    account takes the same time as a real account with a wrong password.
    Without it, the faster "no such user" path lets an attacker enumerate
    which emails or usernames exist by measuring response time.
    """
    try:
        _password_hasher.verify(_DUMMY_HASH, "")
    except VerificationError:
        pass


def create_access_token(subject: str) -> str:
    """
    Build a signed JWT access token for a subject.

    Args:
        subject: Identifies who the token is for — the user's `user_id`
            as a string (the JWT `sub` claim must be a string).

    Returns:
        A signed, URL-safe JWT string carrying `sub`, `type="access"`,
        and a UTC `exp` expiry claim.
    """
    expire_time = (datetime.now(timezone.utc) +
                   timedelta(minutes=settings.access_token_expire_minutes))
    jwt_data = {"sub": subject, "type": "access", "exp": expire_time}
    return jwt.encode(jwt_data, settings.jwt_secret_key,
                      algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    """Verify a JWT access token and return the user ID it identifies.

    Args:
        token: The encoded JWT taken from the request's `Authorization` header.

    Returns:
        The `user_id` carried in the token's `sub` claim.

    Raises:
        jwt.PyJWTError: If the signature is invalid, the token has expired,
            or it is not an access token.
    """
    jwt_data = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    if jwt_data.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return uuid.UUID(jwt_data["sub"])
