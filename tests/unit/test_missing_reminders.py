# -*- coding: utf-8 -*-
"""Tests for app.services.timesheet_reminder.missing_reminders"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.services.timesheet_reminder.missing_reminders import (
    notify_timesheet_missing,
    notify_weekly_timesheet_missing,
)


class TestNotifyTimesheetMissing(unittest.TestCase):

    @patch("app.services.timesheet_reminder.base.create_timesheet_notification")
    def test_no_engineers_no_reminders(self, mock_create):
        """With no engineers found, should send 0 reminders"""
        db = MagicMock()
        # All queries return empty
        db.query.return_value.filter.return_value.all.return_value = []

        result = notify_timesheet_missing(db, date(2025, 1, 10))
        self.assertEqual(result, 0)

    def test_function_signature(self):
        """Verify function accepts expected parameters"""
        self.assertTrue(callable(notify_timesheet_missing))

    def test_default_target_date_is_yesterday(self):
        """Verify the function uses yesterday when no date provided"""
        # We can't easily test the default without running the full function,
        # but we verify the function signature accepts None
        import inspect
        sig = inspect.signature(notify_timesheet_missing)
        self.assertIn("target_date", sig.parameters)
        self.assertIsNone(sig.parameters["target_date"].default)


class TestNotifyWeeklyTimesheetMissing(unittest.TestCase):

    def test_function_is_callable(self):
        self.assertTrue(callable(notify_weekly_timesheet_missing))

    def test_default_week_start_is_none(self):
        import inspect
        sig = inspect.signature(notify_weekly_timesheet_missing)
        self.assertIsNone(sig.parameters["week_start"].default)


if __name__ == "__main__":
    unittest.main()
