"""Unit tests for Task model."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring
from datetime import date, timedelta

import pytest


TODAY = date(2026, 6, 17)


class TestDeriveDates:
    def test_task_is_not_inactive_if_frequency_is_given(self):
        _, date_due = Task.derive_dates(
            frequency=timedelta(days=7),
            date_last=None,
            date_due=None,
            today=TODAY,
        )
        assert date_due is not None

    def test_inactive_both_dates_are_none(self):
        date_last, date_due = Task.derive_dates(
            frequency=None,
            date_last=None,
            date_due=None,
            today=TODAY,
        )
        assert date_last is None
        assert date_due is None

    def test_recurring_sets_date_last_to_today(self):
        date_last, _ = Task.derive_dates(
            frequency=timedelta(days=7),
            date_last=None,
            date_due=None,
            today=TODAY,
        )
        assert date_last == TODAY

    def test_recurring_keeps_date_last_today_despite_date_due(self):
        date_last, _ = Task.derive_dates(
            frequency=timedelta(days=7),
            date_last=None,
            date_due=date(2026, 6, 19),
            today=TODAY,
        )
        assert date_last == TODAY

    def test_recurring_due_is_date_last_plus_frequency(self):
        frequency = timedelta(days=7)
        date_last, date_due = Task.derive_dates(
            frequency=frequency,
            date_last=None,
            date_due=None,
            today=TODAY,
        )
        assert date_due == date_last + frequency

    def test_recurring_due_uses_given_date_last(self):
        frequency = timedelta(days=7)
        given_date_last = TODAY - timedelta(days=3)
        date_last, date_due = Task.derive_dates(
            frequency=frequency,
            date_last=given_date_last,
            date_due=None,
            today=TODAY,
        )
        # The provided date_last is kept (not overridden to today) and drives
        # the due date.
        assert date_last == given_date_last
        assert date_due == given_date_last + frequency

    def test_recurring_due_is_not_clamped_to_today(self):
        frequency = timedelta(days=7)
        given_date_last = TODAY - timedelta(days=30)
        _, date_due = Task.derive_dates(
            frequency=frequency,
            date_last=given_date_last,
            date_due=None,
            today=TODAY,
        )
        # derive_dates does not clamp: an overdue schedule yields a past
        # due date as-is, leaving derive_alert to grade it.
        assert date_due == given_date_last + frequency
        assert date_due < TODAY

    def test_one_off_date_last_removed_if_given(self):
        date_last, _ = Task.derive_dates(
            frequency=None,
            date_last=TODAY - timedelta(days=3),
            date_due=TODAY + timedelta(days=3),
            today=TODAY,
        )
        assert date_last is None

    def test_one_off_no_date_last_is_set(self):
        date_last, _ = Task.derive_dates(
            frequency=None,
            date_last=None,
            date_due=TODAY + timedelta(days=3),
            today=TODAY,
        )
        assert date_last is None


class TestDeriveAlert:
    def test_no_due_date_is_inactive(self):
        assert Task.derive_alert(None, today=TODAY) == AlertState.INACTIVE

    def test_due_in_future_is_green(self):
        date_due = TODAY + timedelta(days=3)
        assert Task.derive_alert(date_due, today=TODAY) == AlertState.GREEN

    def test_due_today_is_green(self):
        # Boundary: a task due today is still on schedule, not overdue.
        assert Task.derive_alert(TODAY, today=TODAY) == AlertState.GREEN

    def test_due_in_past_is_yellow(self):
        date_due = TODAY - timedelta(days=1)
        assert Task.derive_alert(date_due, today=TODAY) == AlertState.YELLOW
