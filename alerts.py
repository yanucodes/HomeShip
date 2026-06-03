"""
AlertState derivation logic for tasks and supplies.

Three kinds of caller are expected:
    * Write time - services call these when creating or updating a task/supply
    to stamp its alert_state.
    * Postpone time - services call these when a task is postponed by a user.
    * Scheduled recompute - alerts depend on *today's* date. A periodic job
    re-derives alert_state for active items.
"""
from datetime import date
from models import AlertState


def escalate_alert(current_alert: AlertState) -> AlertState:
    """
    Increase urgency of a task or getting a supply.
    The order of escalation is GREEN->YELLOW->RED->AUTO_DESTRUCT.
    Alert state is not changed if it is set to INACTIVE or AUTO_DESTRUCT.

    Args:
        current_alert: current alert state.

    Returns:
        New escalated (if applicable) alert state.
    """
    if current_alert == AlertState.GREEN:
        return AlertState.YELLOW
    elif current_alert == AlertState.YELLOW:
        return AlertState.RED
    elif current_alert == AlertState.RED:
        return AlertState.AUTO_DESTRUCT
    return current_alert


def derive_alert_state_on_creation(date_due: date) -> AlertState:
    """
    Derive alert state for a newly created task or supply.
    Args:
        date_due: date when the task should be completed.

    Returns:
        Derived alert state.
    """
    if date_due:
        alert_state = AlertState.GREEN
        if date_due >= date.today():
            return escalate_alert(alert_state)
        return alert_state
    return AlertState.INACTIVE