# -*- coding: utf-8 -*-
"""第二十一批：异常工时提醒单元测试"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date, datetime, timedelta

pytest.importorskip("app.services.timesheet_reminder.anomaly_reminders")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_timesheet(user_id=1, work_date=None, ts_id=10):
    t = MagicMock()
    t.id = ts_id
    t.user_id = user_id
    t.work_date = work_date or date.today()
    return t


def _make_anomaly(timesheet_id=10, anomaly_type="超时工时", description="工时超过12小时"):
    return {
        "timesheet_id": timesheet_id,
        "anomaly_type": anomaly_type,
        "description": description,
    }


class TestNotifyTimesheetAnomaly:
    def test_no_anomalies_returns_zero(self, mock_db):
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        mock_quality_svc = MagicMock()
        mock_quality_svc.detect_anomalies.return_value = []
        with patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService",
                   return_value=mock_quality_svc):
            result = notify_timesheet_anomaly(mock_db, days=1)
        assert result == 0

    def test_sends_notification_for_anomaly(self, mock_db):
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        anomaly = _make_anomaly(timesheet_id=10)
        mock_quality_svc = MagicMock()
        mock_quality_svc.detect_anomalies.return_value = [anomaly]

        # Use side_effect: first call returns timesheet, second call (notification check) returns None
        ts = MagicMock()
        ts.id = 10
        ts.user_id = 1
        ts.work_date = date.today()
        mock_db.query.return_value.filter.return_value.first.side_effect = [ts, None]

        with patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService",
                   return_value=mock_quality_svc), \
             patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification") as mock_notify:
            result = notify_timesheet_anomaly(mock_db, days=1)
        mock_notify.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_skips_duplicate_user_notification(self, mock_db):
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        anomalies = [_make_anomaly(timesheet_id=10), _make_anomaly(timesheet_id=10)]
        mock_quality_svc = MagicMock()
        mock_quality_svc.detect_anomalies.return_value = anomalies

        ts = MagicMock()
        ts.id = 10
        ts.user_id = 5
        ts.work_date = date.today()
        # Both timesheets return same ts, notification check returns None each time
        mock_db.query.return_value.filter.return_value.first.side_effect = [ts, None, ts, None]

        with patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService",
                   return_value=mock_quality_svc), \
             patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification") as mock_notify:
            result = notify_timesheet_anomaly(mock_db, days=1)
        # Only 1 notification should be sent (second anomaly is same user)
        assert mock_notify.call_count == 1

    def test_skips_if_timesheet_not_found(self, mock_db):
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        anomaly = _make_anomaly(timesheet_id=999)
        mock_quality_svc = MagicMock()
        mock_quality_svc.detect_anomalies.return_value = [anomaly]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService",
                   return_value=mock_quality_svc), \
             patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification") as mock_notify:
            result = notify_timesheet_anomaly(mock_db, days=1)
        assert result == 0
        mock_notify.assert_not_called()

    def test_skips_if_already_notified_today(self, mock_db):
        from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
        ts = _make_timesheet(user_id=2)
        anomaly = _make_anomaly(timesheet_id=ts.id)
        mock_quality_svc = MagicMock()
        mock_quality_svc.detect_anomalies.return_value = [anomaly]

        # First call returns timesheet, second (notification check) returns existing notification
        existing_notif = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [ts, existing_notif]

        with patch("app.services.timesheet_reminder.anomaly_reminders.TimesheetQualityService",
                   return_value=mock_quality_svc), \
             patch("app.services.timesheet_reminder.anomaly_reminders.create_timesheet_notification") as mock_notify:
            result = notify_timesheet_anomaly(mock_db, days=1)
        mock_notify.assert_not_called()
        assert result == 0
