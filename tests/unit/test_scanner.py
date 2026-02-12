# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch


class TestScanAndNotifyAll:
    @patch("app.services.sales_reminder.scanner.notify_approval_pending", return_value=1)
    @patch("app.services.sales_reminder.scanner.notify_contract_expiring", return_value=2)
    @patch("app.services.sales_reminder.scanner.notify_quote_expiring", return_value={"expiring": 1, "expired": 0})
    @patch("app.services.sales_reminder.scanner.notify_gate_timeout", return_value=3)
    @patch("app.services.sales_reminder.scanner.notify_payment_overdue", return_value=0)
    @patch("app.services.sales_reminder.scanner.notify_payment_plan_upcoming", return_value=1)
    @patch("app.services.sales_reminder.scanner.notify_milestone_overdue", return_value=0)
    @patch("app.services.sales_reminder.scanner.notify_milestone_upcoming", return_value=2)
    @patch("app.services.sales_reminder.scanner.settings")
    def test_scan_and_notify_all(self, mock_settings, *mocks):
        mock_settings.SALES_GATE_TIMEOUT_DAYS = 7
        mock_settings.SALES_APPROVAL_TIMEOUT_HOURS = 48
        from app.services.sales_reminder.scanner import scan_and_notify_all
        db = MagicMock()
        result = scan_and_notify_all(db)
        assert isinstance(result, dict)
        assert result["contract_expiring"] == 2
        assert result["gate_timeout"] == 3
        db.commit.assert_called_once()


class TestScanSalesReminders:
    @patch("app.services.sales_reminder.scanner.notify_approval_pending", return_value=0)
    @patch("app.services.sales_reminder.scanner.notify_contract_expiring", return_value=0)
    @patch("app.services.sales_reminder.scanner.notify_quote_expiring", return_value={"expiring": 0, "expired": 0})
    @patch("app.services.sales_reminder.scanner.notify_gate_timeout", return_value=0)
    @patch("app.services.sales_reminder.scanner.settings")
    def test_scan_sales_reminders(self, mock_settings, *mocks):
        mock_settings.SALES_GATE_TIMEOUT_DAYS = 7
        mock_settings.SALES_APPROVAL_TIMEOUT_HOURS = 48
        from app.services.sales_reminder.scanner import scan_sales_reminders
        db = MagicMock()
        result = scan_sales_reminders(db)
        assert isinstance(result, dict)
        db.commit.assert_called_once()
