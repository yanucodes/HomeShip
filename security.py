"""Authentication and password helpers.

NOTE: the current implementation is a PLACEHOLDER. It does NOT actually
secure passwords.
"""


def hash_password(password: str) -> str:
    """Turn a raw password into the value stored in `User.password_hash`.

    Args:
        password: The plain-text password from the signup request.

    Returns:
        A string to persist as `password_hash`.

    WARNING: this is a stand-in. It performs NO real hashing and provides NO
    security — it only lets the rest of the app be built end-to-end. Swap in
    a real hash before any real password is ever stored.
    """
    return f"placeholder-hash:{password}"
