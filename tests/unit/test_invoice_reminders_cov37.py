# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - 发票提醒服务
tests/unit/test_invoice_reminders_cov37.py
"""
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.sales_reminder.invoice_reminders")

from app.services.sales_reminder.invoice_reminders import notify_invoice_issued


def _make_invoice(inv_id=1, code="INV-001", amount=10000):
    invoice = MagicMock()
    invoice.id = inv_id
    invoice.invoice_code = code
    invoice.total_amount = amount
    invoice.issue_date = MagicMock()
    invoice.issue_date.isoformat.return_value = "2025-06-01"
    contract = MagicMock()
    contract.owner_id = 42
    invoice.contract = contract
    return invoice


class TestNotifyInvoiceIssued:
    def test_returns_none_when_invoice_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = notify_invoice_issued(db, 999)
        assert result is None

    def test_returns_none_when_no_contract(self):
        db = MagicMock()
        invoice = MagicMock()
        invoice.contract = None
        db.query.return_value.filter.return_value.first.return_value = invoice
        result = notify_invoice_issued(db, 1)
        assert result is None

    def test_returns_none_when_no_owner(self):
        db = MagicMock()
        invoice = MagicMock()
        invoice.contract = MagicMock()
        invoice.contract.owner_id = None
        db.query.return_value.filter.return_value.first.return_value = invoice
        result = notify_invoice_issued(db, 1)
        assert result is None

    def test_creates_notification_on_valid_invoice(self):
        db = MagicMock()
        invoice = _make_invoice()
        db.query.return_value.filter.return_value.first.return_value = invoice

        fake_notification = MagicMock()
        with patch(
            "app.services.sales_reminder.invoice_reminders.create_notification",
            return_value=fake_notification,
        ) as mock_create:
            result = notify_invoice_issued(db, 1)

        assert result is fake_notification
        mock_create.assert_called_once()

    def test_notification_content_includes_invoice_code(self):
        db = MagicMock()
        invoice = _make_invoice(code="INV-2025-001")
        db.query.return_value.filter.return_value.first.return_value = invoice

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch(
            "app.services.sales_reminder.invoice_reminders.create_notification",
            side_effect=fake_create,
        ):
            notify_invoice_issued(db, 1)

        assert "INV-2025-001" in captured["title"]
        assert captured["notification_type"] == "INVOICE_ISSUED"

    def test_notification_receiver_is_contract_owner(self):
        db = MagicMock()
        invoice = _make_invoice()
        invoice.contract.owner_id = 77
        db.query.return_value.filter.return_value.first.return_value = invoice

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch(
            "app.services.sales_reminder.invoice_reminders.create_notification",
            side_effect=fake_create,
        ):
            notify_invoice_issued(db, 1)

        assert captured["user_id"] == 77

    def test_extra_data_contains_invoice_amount(self):
        db = MagicMock()
        invoice = _make_invoice(amount=50000)
        db.query.return_value.filter.return_value.first.return_value = invoice

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return MagicMock()

        with patch(
            "app.services.sales_reminder.invoice_reminders.create_notification",
            side_effect=fake_create,
        ):
            notify_invoice_issued(db, 1)

        assert captured["extra_data"]["invoice_amount"] == 50000
