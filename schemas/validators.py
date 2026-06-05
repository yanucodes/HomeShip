"""Reusable field validators for HomeShip schemas."""

from datetime import date


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
