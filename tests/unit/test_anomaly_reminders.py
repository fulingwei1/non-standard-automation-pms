# -*- coding: utf-8 -*-
from datetime import date
from unittest.mock import MagicMock, patch


class TestNotifyTimesheetAnomaly:
    @patch("app.services.timesheet.reminder.anomaly_reminders.TimesheetQualityService")
    @patch("app.services.timesheet.reminder.anomaly_reminders.create_timesheet_notification")
    def test_no_anomalies(self, mock_notify, mock_quality_cls):
        mock_quality_cls.return_value.detect_anomalies.return_value = []
        from app.services.timesheet.reminder.anomaly_reminders import notify_timesheet_anomaly

        db = MagicMock()
        result = notify_timesheet_anomaly(db)
        assert result == 0

    @patch("app.services.timesheet.reminder.anomaly_reminders.TimesheetQualityService")
    @patch("app.services.timesheet.reminder.anomaly_reminders.create_timesheet_notification")
    def test_with_anomaly(self, mock_notify, mock_quality_cls):
        mock_quality_cls.return_value.detect_anomalies.return_value = [
            {"timesheet_id": 1, "anomaly_type": "OVERTIME", "description": "超时"}
        ]
        from app.services.timesheet.reminder.anomaly_reminders import notify_timesheet_anomaly

        db = MagicMock()
        ts = MagicMock()
        ts.user_id = 1
        ts.id = 1
        ts.work_date = date(2024, 1, 15)
        q1 = MagicMock(); q1.filter.return_value.first.return_value = ts
        q2 = MagicMock(); q2.filter.return_value.first.return_value = None
        db.query.side_effect = [q1, q2]
        result = notify_timesheet_anomaly(db)
        assert result == 1
        mock_notify.assert_called_once()
