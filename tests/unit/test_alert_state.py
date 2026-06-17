"""Unit tests for AlertState.escalate."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring
from models.alert_state import AlertState


def test_green_escalates_to_yellow():
    assert AlertState.GREEN.escalate() == AlertState.YELLOW


def test_yellow_escalates_to_red():
    assert AlertState.YELLOW.escalate() == AlertState.RED


def test_red_escalates_to_auto_destruct():
    assert AlertState.RED.escalate() == AlertState.AUTO_DESTRUCT


def test_auto_destruct_stays_auto_destruct():
    # AUTO_DESTRUCT is terminal: escalating further leaves it unchanged.
    assert AlertState.AUTO_DESTRUCT.escalate() == AlertState.AUTO_DESTRUCT


def test_inactive_stays_inactive():
    # INACTIVE is outside the escalation ladder and never escalates.
    assert AlertState.INACTIVE.escalate() == AlertState.INACTIVE
