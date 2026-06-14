"""Reusable field validators for HomeShip schemas."""

from datetime import date, timedelta
from typing import Annotated

from pydantic import StringConstraints


def bounded_str(*, max_length: int, min_length: int = 1,
                strip_whitespace: bool = True,
                pattern: str | None = None) -> type[str]:
    """Build a length-bounded string type for use as a schema field.

    Returns an `Annotated[str, ...]` type carrying Pydantic constraints, so
    fields can share one definition instead of repeating `StringConstraints`.
    By default leading/trailing whitespace is stripped before the length is
    checked, which also rejects whitespace-only input against a `min_length`
    of 1.

    Args:
        max_length: Maximum number of characters allowed (after stripping).
        min_length: Minimum number of characters required (after stripping).
            Defaults to 1, which forbids the empty string.
        strip_whitespace: Whether to strip surrounding whitespace before
            validating. Pass False for fields where surrounding whitespace is
            significant (e.g. passwords).
        pattern: Optional regular expression the whole value must match, used
            to restrict the allowed character set (e.g. a username charset).

    Returns:
        An annotated `str` type applying the given constraints.
    """
    return Annotated[str, StringConstraints(
        strip_whitespace=strip_whitespace,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
    )]


def not_in_future(
    value: date | None, *, date_description: str = "date"
) -> date | None:
    """Reject a date (if provided) later than today.

    Args:
        value: The date to check, or None. Accepts None for optional date
            fields.
        date_description: Name of the field, used to make the error message.

    Returns:
        The unchanged value if valid. None if the date was not provided.

    Raises:
        ValueError: If the date is in the future.
    """
    if value is not None and value > date.today():
        raise ValueError(f"{date_description} must not be in the future")
    return value


def not_in_past(
    value: date | None, *, date_description: str = "date"
) -> date | None:
    """Reject a date (if provided) earlier than today.

    Args:
        value: The date to check, or None. Accepts None for optional date
            fields.
        date_description: Name of the field, used to make the error message.

    Returns:
        The unchanged value if valid. None if the date was not provided.

    Raises:
        ValueError: If the date is in the past.
    """
    if value is not None and value < date.today():
        raise ValueError(f"{date_description} must not be in the past")
    return value


def positive_timedelta(
    value: timedelta | None, *, field_description: str = "duration"
) -> timedelta | None:
    """Reject a duration (if provided) that is not strictly positive.

    Args:
        value: The duration to check, or None. Accepts None for optional
            duration fields.
        field_description: Name of the field, used to make the error message.

    Returns:
        The unchanged value if valid. None if the duration was not provided.

    Raises:
        ValueError: If the duration is zero or negative.
    """
    if value is not None and value <= timedelta(0):
        raise ValueError(f"{field_description} must be positive")
    return value


def non_negative(
    value: int | None, *, field_description: str = "value"
) -> int | None:
    """Reject an integer (if provided) below zero.

    Args:
        value: The integer to check, or None. Accepts None for optional
            fields.
        field_description: Name of the field, used to make the error message.

    Returns:
        The unchanged value if valid. None if the value was not provided.

    Raises:
        ValueError: If the integer is negative.
    """
    if value is not None and value < 0:
        raise ValueError(f"{field_description} must not be negative")
    return value
