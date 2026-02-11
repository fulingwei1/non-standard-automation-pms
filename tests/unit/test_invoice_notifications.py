# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
import json

from app.services.invoice_auto_service.notifications import send_invoice_notifications, log_auto_invoice


class TestSendInvoiceNotifications:
    def test_no_project(self):
        service = MagicMock()
        order = MagicMock(project=None)
        # Should not raise
        send_invoice_notifications(service, order, [], True)

    def test_sends_notifications(self):
        service = MagicMock()
        project = MagicMock(project_code="P001", project_name="Test", contract_id=1)
        order = MagicMock(project=project, order_no="A001", id=1)
        contract = MagicMock(owner_id=10)
        service.db.query.return_value.filter.return_value.first.return_value = contract
        service.db.query.return_value.filter.return_value.all.return_value = [(5,)]

        items = [{"invoice_code": "INV001", "amount": 1000}]

        with patch("app.services.invoice_auto_service.notifications.NotificationDispatcher") as mock_nd:
            nd = MagicMock()
            mock_nd.return_value = nd
            nd.send_notification_request.return_value = {"success": True}
            send_invoice_notifications(service, order, items, True)

    def test_exception_caught(self):
        service = MagicMock()
        order = MagicMock()
        order.project = MagicMock()
        order.project.contract_id = None
        service.db.query.side_effect = Exception("db error")
        # Should not raise
        send_invoice_notifications(service, order, [], False)


class TestLogAutoInvoice:
    def test_log_with_empty_conditions(self):
        service = MagicMock()
        order = MagicMock(id=1, order_no="A001", project_id=10, conditions=None)
        items = [{"invoice_code": "INV001"}]
        log_auto_invoice(service, order, items, True)
        assert order.conditions is not None
        data = json.loads(order.conditions)
        assert len(data) == 1

    def test_log_appends_to_existing(self):
        service = MagicMock()
        order = MagicMock(id=1, order_no="A001", project_id=10, conditions='[{"old": true}]')
        log_auto_invoice(service, order, [], False)
        data = json.loads(order.conditions)
        assert len(data) == 2

    def test_log_handles_invalid_json(self):
        service = MagicMock()
        order = MagicMock(id=1, order_no="A001", project_id=10, conditions="not json")
        log_auto_invoice(service, order, [], True)
        data = json.loads(order.conditions)
        assert len(data) == 1

    def test_log_exception_caught(self):
        service = MagicMock()
        order = MagicMock()
        type(order).conditions = property(lambda self: None, lambda self, v: (_ for _ in ()).throw(Exception("fail")))
        # Should not raise
        log_auto_invoice(service, order, [], True)
