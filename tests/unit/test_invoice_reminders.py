# -*- coding: utf-8 -*-
"""发票提醒单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.sales_reminder.invoice_reminders import notify_invoice_issued


class TestNotifyInvoiceIssued:
    def setup_method(self):
        self.db = MagicMock()

    def test_invoice_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = notify_invoice_issued(self.db, 999)
        assert result is None

    def test_no_contract(self):
        invoice = MagicMock()
        invoice.contract = None
        self.db.query.return_value.filter.return_value.first.return_value = invoice
        result = notify_invoice_issued(self.db, 1)
        assert result is None

    def test_no_owner(self):
        invoice = MagicMock()
        invoice.contract.owner_id = None
        self.db.query.return_value.filter.return_value.first.return_value = invoice
        result = notify_invoice_issued(self.db, 1)
        assert result is None

    @patch("app.services.sales_reminder.invoice_reminders.create_notification")
    def test_success(self, mock_create):
        invoice = MagicMock()
        invoice.contract.owner_id = 10
        invoice.invoice_code = "INV001"
        invoice.total_amount = 5000
        invoice.issue_date = MagicMock()
        invoice.issue_date.isoformat.return_value = "2024-01-01"
        invoice.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = invoice
        mock_create.return_value = MagicMock()
        result = notify_invoice_issued(self.db, 1)
        mock_create.assert_called_once()
