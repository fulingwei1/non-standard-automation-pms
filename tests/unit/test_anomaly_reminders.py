# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime


class TestNotifyTimesheetAnomaly:
    @patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService")
    @patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification")
    def test_no_anomalies(self, mock_notify, mock_quality_cls):
        mock_quality_cls.return_value.detect_anomalies.return_value = []
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        db = MagicMock()
        result = notify_timesheet_anomaly(db)
        assert result == 0

    @patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService")
    @patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification")
    def test_with_anomaly(self, mock_notify, mock_quality_cls):
        mock_quality_cls.return_value.detect_anomalies.return_value = [
            {"timesheet_id": 1, "anomaly_type": "OVERTIME", "description": "超时"}
        ]
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        db = MagicMock()
        ts = MagicMock()
        ts.user_id = 1
        ts.id = 1
        ts.work_date = date(2024, 1, 15)
        db.query.return_value.filter.return_value.first.side_effect = [ts, None]
        result = notify_timesheet_anomaly(db)
        assert result == 1
        mock_notify.assert_called_once()
