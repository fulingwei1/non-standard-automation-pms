# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta


class TestNotifySyncFailure:
    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_no_approved_timesheets(self, mock_notify):
        from app.services.timesheet_reminder.sync_reminders import notify_sync_failure
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = notify_sync_failure(db)
        assert result == 0
        mock_notify.assert_not_called()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_with_sync_failure(self, mock_notify):
        from app.services.timesheet_reminder.sync_reminders import notify_sync_failure
        db = MagicMock()
        ts = MagicMock()
        ts.user_id = 1
        ts.id = 10
        ts.approve_time = datetime.now() - timedelta(hours=2)
        ts.work_date = date(2024, 1, 15)
        db.query.return_value.filter.return_value.all.return_value = [ts]
        db.query.return_value.filter.return_value.first.return_value = None
        result = notify_sync_failure(db)
        assert result == 1
        mock_notify.assert_called_once()

    @patch("app.services.timesheet_reminder.sync_reminders.create_timesheet_notification")
    def test_already_notified(self, mock_notify):
        from app.services.timesheet_reminder.sync_reminders import notify_sync_failure
        db = MagicMock()
        ts = MagicMock()
        ts.user_id = 1
        ts.id = 10
        ts.approve_time = datetime.now() - timedelta(hours=2)
        ts.work_date = date(2024, 1, 15)
        db.query.return_value.filter.return_value.all.return_value = [ts]
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        result = notify_sync_failure(db)
        assert result == 0
