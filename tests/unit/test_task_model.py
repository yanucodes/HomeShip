"""Unit tests for Task model."""
# Test names describe the scenario; per-test docstrings would be redundant.
# pylint: disable=missing-function-docstring
from datetime import date, timedelta

import pytest

from models.alert_state import AlertState
from models.task import Task

TODAY = date(2026, 6, 17)


class TestDeriveDates:
    """Tests for Task.derive_dates: filling in date_last/date_due from the
    fields the client supplied across the lifecycle states."""

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
    """Tests for Task.derive_alert: grading a task's alert state from its due
    date (INACTIVE / GREEN / YELLOW)."""

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


class TestGetChangesOnCompleting:
    """Tests for Task.get_changes_on_completing: the field changes (date_last,
    date_due, alert_state) produced when a task is marked complete."""

    FREQUENCY_FOR_RECURRING = timedelta(days=7)

    def test_new_date_last_is_today_for_recurring(self):
        task = Task(
            frequency=self.FREQUENCY_FOR_RECURRING
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["date_last"] == TODAY

    def test_date_last_records_completion_for_one_off(self):
        # A one-off starts with no date_last, but completing it records the
        # completion date — this powers the "done today" crossing-out in the UI.
        task = Task(
            frequency=None,
            date_last=None
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["date_last"] == TODAY

    def test_date_last_records_completion_for_inactive(self):
        # Even if the task is inactive, if the user completes it,
        # the date should be recorded for display in the UI.
        task = Task(
            frequency=None,
            date_last=None,
            alert_state=AlertState.INACTIVE
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["date_last"] == TODAY

    def test_date_due_set_to_none_for_one_off(self):
        task = Task(
            frequency=None,
            date_due=TODAY
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["date_due"] is None

    def test_due_set_to_today_plus_frequency_for_recurring(self):
        task = Task(
            frequency=self.FREQUENCY_FOR_RECURRING
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["date_due"] == TODAY + self.FREQUENCY_FOR_RECURRING

    def test_alert_set_to_green_for_recurring(self):
        task = Task(
            frequency=self.FREQUENCY_FOR_RECURRING
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["alert_state"] == AlertState.GREEN

    def test_alert_deactivated_for_one_off(self):
        task = Task(
            frequency=None
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["alert_state"] == AlertState.INACTIVE

    def test_inactive_alert_stays_inactive_for_one_off(self):
        task = Task(
            frequency=None,
            alert_state=AlertState.INACTIVE
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["alert_state"] == AlertState.INACTIVE

    @pytest.mark.xfail(
        reason="#1: completing a muted (INACTIVE) recurring task reactivates "
               "it (recomputes alert to GREEN); should stay INACTIVE — an "
               "out-of-band completion records the date without un-muting.",
        strict=True,
    )
    def test_inactive_alert_stays_inactive_for_recurring(self):
        task = Task(
            frequency=self.FREQUENCY_FOR_RECURRING,
            alert_state=AlertState.INACTIVE
        )
        changes = task.get_changes_on_completing(today=TODAY)
        assert changes["alert_state"] == AlertState.INACTIVE


class TestGetChangesOnPostponing:
    """Tests for Task.get_changes_on_postponing: the field changes (date_due,
    alert_state) produced when a task is pushed to a later due date."""

    def test_date_due_is_updated(self):
        task = Task(
            date_due=TODAY,
            alert_state=AlertState.GREEN
        )
        new_date = TODAY + timedelta(days=7)
        changes = task.get_changes_on_postponing(date_due=new_date)
        assert changes["date_due"] == new_date

    def test_alert_state_escalates(self):
        task = Task(
            date_due=TODAY,
            alert_state=AlertState.YELLOW
        )
        new_date = TODAY + timedelta(days=7)
        changes = task.get_changes_on_postponing(date_due=new_date)
        assert changes["alert_state"] == AlertState.RED


class TestGetChangesOnFrequencyChanging:
    """Tests for Task.get_changes_on_frequency_changing: re-deriving the
    schedule (frequency, date_last, date_due, alert_state) from a new
    frequency."""

    def test_new_frequency_is_stored(self):
        old_frequency = timedelta(days=7)
        task = Task(frequency=old_frequency, date_last=TODAY - old_frequency,
                    date_due=TODAY, alert_state=AlertState.GREEN)
        new_frequency = timedelta(days=10)
        changes = task.get_changes_on_frequency_changing(
            new_frequency, today=TODAY)
        assert changes["frequency"] == new_frequency

    def test_alert_state_is_present_in_changes(self):
        # The change dict must carry an alert_state key so the update applies
        # it; the exact value is derive_alert's concern (see TestDeriveAlert).
        old_frequency = timedelta(days=7)
        task = Task(frequency=old_frequency, date_last=TODAY - old_frequency,
                    date_due=TODAY, alert_state=AlertState.GREEN)
        changes = task.get_changes_on_frequency_changing(
            timedelta(days=10), today=TODAY)
        assert "alert_state" in changes

    def test_due_is_existing_date_last_plus_new_frequency(self):
        date_last = TODAY - timedelta(days=2)
        task = Task(date_last=date_last, date_due=TODAY,
                    alert_state=AlertState.GREEN)
        new_frequency = timedelta(days=10)
        changes = task.get_changes_on_frequency_changing(
            new_frequency, today=TODAY)
        # The existing date_last is kept and drives the new due date.
        assert changes["date_last"] == date_last
        assert changes["date_due"] == date_last + new_frequency

    def test_setting_frequency_without_date_last_uses_today(self):
        task = Task(date_last=None, date_due=None,
                    alert_state=AlertState.INACTIVE)
        new_frequency = timedelta(days=7)
        changes = task.get_changes_on_frequency_changing(
            new_frequency, today=TODAY)
        assert changes["date_last"] == TODAY
        assert changes["date_due"] == TODAY + new_frequency

    @pytest.mark.xfail(
        reason="#1 (muted-tasks family): changing a muted (INACTIVE) recurring "
               "task's frequency re-derives the alert to GREEN, reactivating "
               "it; it should stay INACTIVE (only the frequency updates). Same "
               "root cause as the completion bug.",
        strict=True,
    )
    def test_changing_frequency_keeps_muted_task_inactive(self):
        # A muted recurring task keeps its frequency (deactivation mutes the
        # signal, not the cadence); retuning the cadence while muted must not
        # un-mute it.
        task = Task(
            frequency=timedelta(days=7),
            date_last=TODAY - timedelta(days=2),
            date_due=None,
            alert_state=AlertState.INACTIVE,
        )
        changes = task.get_changes_on_frequency_changing(
            timedelta(days=14), today=TODAY)
        assert changes["alert_state"] == AlertState.INACTIVE

    def test_clearing_frequency_keeps_date_due(self):
        frequency = timedelta(days=7)
        date_due = TODAY + frequency
        task = Task(frequency=frequency, date_last=TODAY, date_due=date_due,
                    alert_state=AlertState.GREEN)
        changes = task.get_changes_on_frequency_changing(None, today=TODAY)
        # Clearing frequency stops the recurrence but KEEPS the current due
        # date (becomes a one-off deadline).
        assert changes["frequency"] is None
        assert changes["date_due"] == date_due
        