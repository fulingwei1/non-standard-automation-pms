# -*- coding: utf-8 -*-
"""工时提醒扫描器单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.timesheet_reminder.scanner import scan_and_notify_all


class TestScanAndNotifyAll:
    @patch("app.services.timesheet_reminder.scanner.notify_sync_failure", return_value=0)
    @patch("app.services.timesheet_reminder.scanner.notify_approval_timeout", return_value=1)
    @patch("app.services.timesheet_reminder.scanner.notify_timesheet_anomaly", return_value=2)
    @patch("app.services.timesheet_reminder.scanner.notify_weekly_timesheet_missing", return_value=3)
    @patch("app.services.timesheet_reminder.scanner.notify_timesheet_missing", return_value=5)
    def test_scan_all(self, mock_daily, mock_weekly, mock_anomaly, mock_approval, mock_sync):
        db = MagicMock()
        result = scan_and_notify_all(db)
        assert result['daily_missing'] == 5
        assert result['weekly_missing'] == 3
        assert result['anomaly'] == 2
        assert result['approval_timeout'] == 1
        assert result['sync_failure'] == 0
        db.commit.assert_called_once()

    @patch("app.services.timesheet_reminder.scanner.notify_timesheet_missing", side_effect=Exception("fail"))
    def test_scan_error_rollback(self, mock_daily):
        db = MagicMock()
        result = scan_and_notify_all(db)
        db.rollback.assert_called_once()
