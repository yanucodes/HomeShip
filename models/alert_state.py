"""Shared alert state enum.

The same alert vocabulary is used for both tasks and supplies so that the
ship's overall alert level can be computed uniformly across both domains
(e.g. `max(state for state in all_tasks_and_supplies)`).
"""

from datetime import date
import enum


class AlertState(enum.Enum):
    """Health / urgency level of a task or supply.

    Members:
        INACTIVE: Item is no longer tracked (archived task, one-off supply).
        GREEN: Healthy — task done on time, supply in stock.
        YELLOW: Warning — task postponed once, supply running low.
        RED: Critical — task postponed twice, supply out of stock.
        AUTO_DESTRUCT: Beyond recovery — task cannot be postponed anymore,
            critical-item outage threatening the ship.
    """

    INACTIVE = "inactive"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    AUTO_DESTRUCT = "auto-destruct"

    def escalate(self) -> "AlertState":
        """
        Return the next-higher urgency / severity of the alert.
        The order of escalation is GREEN->YELLOW->RED->AUTO_DESTRUCT.
        Alert state is returned unchanged if it is INACTIVE or AUTO_DESTRUCT.
        """
        if self == AlertState.GREEN:
            return AlertState.YELLOW
        if self == AlertState.YELLOW:
            return AlertState.RED
        if self == AlertState.RED:
            return AlertState.AUTO_DESTRUCT
        return self

    @classmethod
    def on_creation(cls, date_due: date | None) -> "AlertState":
        """
        Derive the initial alert state for a newly created task or supply
        from its due date.

        Args:
            date_due: deadline for the task or getting a supply, or None if
                the item has no deadline.

        Returns:
            `AlertState.INACTIVE` if no deadline was set,
            `AlertState.GREEN` if the deadline is today or later, and
            `AlertState.YELLOW` if it has already passed.
        """
        if date_due is None:
            return AlertState.INACTIVE
        if date_due >= date.today():
            return AlertState.GREEN
        return AlertState.YELLOW
