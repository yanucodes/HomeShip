"""Authentication and password helpers."""

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Turn a raw password into the value stored in `User.password_hash`.

    Args:
        password: The plain-text password from the signup request.

    Returns:
        A bcrypt hash string to persist as `password_hash`.
    """
    return _pwd_context.hash(password)
