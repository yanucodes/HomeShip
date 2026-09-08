"""Unit tests for Supply model."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring
from datetime import date, timedelta

import pytest

from models.alert_state import AlertState
from models.supply import Supply, StockState

TODAY = date(2026, 6, 17)
# Deliberately not the config defaults (1 / 7): derive_alert must grade on the
# windows it is handed, so tuning settings can never move these tests.
RED_WITHIN = timedelta(days=2)
YELLOW_WITHIN = timedelta(days=5)
DAY = timedelta(days=1)

# Every deadline position that matters, as an offset from TODAY, paired with
# the alert a supply the crew still has to buy must show there. Both sides of
# every boundary are listed as well as the interiors, so an inclusive
# comparison silently turned exclusive fails a case. Offsets are expressed in
# terms of the windows, so retuning RED_WITHIN/YELLOW_WITHIN keeps the table
# valid. Rows are (offset, expected alert, test-case id).
_LADDER = [
    (-YELLOW_WITHIN, AlertState.AUTO_DESTRUCT, "long-past"),
    (-DAY, AlertState.AUTO_DESTRUCT, "yesterday"),
    (timedelta(0), AlertState.RED, "due-today"),
    (RED_WITHIN - DAY, AlertState.RED, "inside-red-window"),
    (RED_WITHIN, AlertState.RED, "red-edge"),
    (RED_WITHIN + DAY, AlertState.YELLOW, "just-past-red-edge"),
    (YELLOW_WITHIN - DAY, AlertState.YELLOW, "inside-yellow-window"),
    (YELLOW_WITHIN, AlertState.YELLOW, "yellow-edge"),
    (YELLOW_WITHIN + DAY, AlertState.GREEN, "just-past-yellow-edge"),
    (YELLOW_WITHIN * 6, AlertState.GREEN, "far-future"),
]
DEADLINE_LADDER = [
    pytest.param(offset, expected, id=case_id)
    for offset, expected, case_id in _LADDER
]
# The same positions without the expectations, for the in-stock test: it has
# one answer for all of them, so it must not take an `expected` it ignores.
DEADLINE_POSITIONS = [
    pytest.param(offset, id=case_id) for offset, _, case_id in _LADDER
]

# With no deadline, the alert is a pure function of the stock level.
STOCK_ONLY_RULE = [
    pytest.param(StockState.IN_STOCK, AlertState.GREEN, id="in_stock"),
    pytest.param(StockState.RUNNING_LOW, AlertState.YELLOW, id="running_low"),
    pytest.param(StockState.OUT_OF_STOCK, AlertState.RED, id="out_of_stock"),
]

# Contexts that must make no difference whatsoever to that rule: any date in
# any direction, and any window configuration including degenerate ones. The
# `today-defaulted` case omits `today` entirely and so runs against the real
# clock — safe precisely because the property under test is that the date is
# irrelevant, and it is the only thing exercising derive_alert's
# `today is None` default.
NO_DEADLINE_CONTEXTS = [
    pytest.param(TODAY, RED_WITHIN, YELLOW_WITHIN, id="baseline"),
    pytest.param(date(2024, 2, 29), RED_WITHIN, YELLOW_WITHIN, id="leap-day"),
    pytest.param(date(2026, 1, 1), RED_WITHIN, YELLOW_WITHIN, id="new-year"),
    pytest.param(date(2026, 12, 31), RED_WITHIN, YELLOW_WITHIN, id="year-end"),
    pytest.param(date(1970, 1, 1), RED_WITHIN, YELLOW_WITHIN, id="far-past"),
    pytest.param(date(2999, 12, 31), RED_WITHIN, YELLOW_WITHIN,
                 id="far-future"),
    pytest.param(TODAY, timedelta(days=1), timedelta(days=7),
                 id="config-defaults"),
    pytest.param(TODAY, timedelta(0), timedelta(0), id="zero-windows"),
    pytest.param(TODAY, YELLOW_WITHIN * 20, YELLOW_WITHIN * 20,
                 id="huge-equal-windows"),
    pytest.param(None, RED_WITHIN, YELLOW_WITHIN, id="today-defaulted"),
]


class TestDeriveAlert:
    """Tests for Supply.derive_alert: filling in alert_state from the fields
    the client supplied.
    """

    @pytest.mark.parametrize("today,red_within,yellow_within",
                             NO_DEADLINE_CONTEXTS)
    @pytest.mark.parametrize("stock_state,expected", STOCK_ONLY_RULE)
    def test_no_deadline_alert_is_governed_only_by_stock_state(
            self, stock_state, expected, today, red_within, yellow_within):
        # A supply with nothing to buy *by* has no clock running against it,
        # so neither the current date nor the deadline windows may move the
        # alert — only what is on the shelf. Asserted across every date and
        # window combination rather than at one arbitrary today, so the
        # independence is demonstrated instead of assumed.
        alert = Supply.derive_alert(stock_state,
                                    date_due=None,
                                    red_within=red_within,
                                    yellow_within=yellow_within,
                                    today=today)
        assert alert == expected

    @pytest.mark.parametrize("offset,expected", DEADLINE_LADDER)
    def test_out_of_stock_alert_follows_the_deadline(self, offset, expected):
        # Note due-today is RED, not GREEN: it is not yet missed
        # (auto-destruct needs today > date_due) but an item needed today and
        # not on the shelf is maximally urgent. This differs from Task, where
        # due-today is still GREEN — a task can be done later today, a
        # purchase cannot be assumed.
        alert = Supply.derive_alert(StockState.OUT_OF_STOCK,
                                    date_due=TODAY + offset,
                                    red_within=RED_WITHIN,
                                    yellow_within=YELLOW_WITHIN,
                                    today=TODAY)
        assert alert == expected

    @pytest.mark.parametrize("offset,expected", DEADLINE_LADDER)
    def test_running_low_alert_follows_the_deadline(self, offset, expected):
        # The same expectations as OUT_OF_STOCK at every single position:
        # once a deadline is set, having some but not enough earns no credit,
        # because a purchase is still pending either way. Note this makes
        # RUNNING_LOW *less* alarming than it is with no deadline at all (a
        # far-off deadline grades GREEN where a deadline-free supply would be
        # YELLOW) — the deadline, not the shelf, is the story.
        alert = Supply.derive_alert(StockState.RUNNING_LOW,
                                    date_due=TODAY + offset,
                                    red_within=RED_WITHIN,
                                    yellow_within=YELLOW_WITHIN,
                                    today=TODAY)
        assert alert == expected

    @pytest.mark.parametrize("offset", DEADLINE_POSITIONS)
    def test_in_stock_is_green_whatever_the_deadline(self, offset):
        # Having the item outranks every position on the ladder, including a
        # deadline already missed: the crew bought it, so a stale date_due
        # must never auto-destruct the ship. Deliberately the same positions
        # as the two tests above, so the contrast is exhaustive rather than
        # sampled.
        alert = Supply.derive_alert(StockState.IN_STOCK,
                                    date_due=TODAY + offset,
                                    red_within=RED_WITHIN,
                                    yellow_within=YELLOW_WITHIN,
                                    today=TODAY)
        assert alert == AlertState.GREEN
