"""Shared alert state enum.

The same alert vocabulary is used for both tasks and supplies so that the
ship's overall alert level can be computed uniformly across both domains
(e.g. `max(state for state in all_tasks_and_supplies)`).
"""

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
