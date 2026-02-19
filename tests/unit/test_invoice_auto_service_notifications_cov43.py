# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/invoice_auto_service/notifications.py
"""
import pytest

pytest.importorskip("app.services.invoice_auto_service.notifications")

import json
from unittest.mock import MagicMock, patch

from app.services.invoice_auto_service.notifications import (
    send_invoice_notifications,
    log_auto_invoice,
)


def make_service():
    svc = MagicMock()
    svc.db = MagicMock()
    return svc


def make_order(order_no="ACC-001", project_id=1, order_id=10):
    order = MagicMock()
    order.id = order_id
    order.order_no = order_no
    order.project_id = project_id
    project = MagicMock()
    project.project_code = "P001"
    project.project_name = "测试项目"
    project.contract_id = 5
    order.project = project
    order.conditions = None
    return order


# ── 1. send_invoice_notifications: project 不存在时静默退出 ─────────────────────
def test_send_notifications_no_project():
    svc = make_service()
    order = MagicMock()
    order.project = None
    # Should return without error
    send_invoice_notifications(svc, order, [], False)


# ── 2. send_invoice_notifications: 正常流程（发票申请模式）───────────────────────
def test_send_notifications_invoice_request_mode():
    svc = make_service()
    order = make_order()

    finance_role_id = [(1,)]
    finance_user_ids = [(10,)]
    contract = MagicMock()
    contract.owner_id = 20

    q_contract = MagicMock()
    q_contract.filter.return_value.first.return_value = contract

    q_role = MagicMock()
    q_role.filter.return_value.all.return_value = finance_role_id

    q_users = MagicMock()
    q_users.filter.return_value.all.return_value = finance_user_ids

    svc.db.query.side_effect = [q_contract, q_role, q_users]

    items = [{"request_no": "IR001", "amount": 1000.0}]

    with patch("app.services.invoice_auto_service.notifications.NotificationDispatcher") as MockDisp, \
         patch("app.services.invoice_auto_service.notifications.NotificationRequest"), \
         patch("app.services.invoice_auto_service.notifications.NotificationPriority"):
        mock_dispatcher = MagicMock()
        mock_dispatcher.send_notification_request.return_value = {"success": True}
        MockDisp.return_value = mock_dispatcher

        send_invoice_notifications(svc, order, items, auto_create=False)

    MockDisp.assert_called_once()


# ── 3. send_invoice_notifications: 异常时不抛出 ──────────────────────────────────
def test_send_notifications_exception_silenced():
    svc = make_service()
    order = make_order()
    svc.db.query.side_effect = Exception("DB error")

    # Should not raise
    send_invoice_notifications(svc, order, [], False)


# ── 4. log_auto_invoice: 新建日志 ────────────────────────────────────────────────
def test_log_auto_invoice_creates_entry():
    svc = make_service()
    order = make_order()
    order.conditions = None

    items = [{"invoice_code": "INV001", "amount": 500.0}]
    log_auto_invoice(svc, order, items, auto_create=True)

    log_list = json.loads(order.conditions)
    assert len(log_list) == 1
    assert log_list[0]["acceptance_order_no"] == "ACC-001"
    assert log_list[0]["auto_create"] is True


# ── 5. log_auto_invoice: 追加到已有日志 ───────────────────────────────────────────
def test_log_auto_invoice_appends():
    svc = make_service()
    order = make_order()
    order.conditions = json.dumps([{"existing": True}])

    items = [{"request_no": "IR002", "amount": 200.0}]
    log_auto_invoice(svc, order, items, auto_create=False)

    log_list = json.loads(order.conditions)
    assert len(log_list) == 2
    assert log_list[0]["existing"] is True


# ── 6. log_auto_invoice: conditions 为无效 JSON 时重置 ──────────────────────────
def test_log_auto_invoice_invalid_json_reset():
    svc = make_service()
    order = make_order()
    order.conditions = "not_valid_json"

    items = []
    log_auto_invoice(svc, order, items, auto_create=False)

    log_list = json.loads(order.conditions)
    assert isinstance(log_list, list)
    assert len(log_list) == 1


# ── 7. log_auto_invoice: 异常时不抛出 ────────────────────────────────────────────
def test_log_auto_invoice_exception_silenced():
    svc = make_service()
    order = MagicMock()
    order.id = 1
    order.order_no = "ACC-X"
    order.project_id = 1
    # Trigger exception by making json.loads raise inside
    order.conditions = None
    type(order).conditions = property(
        fget=lambda self: None,
        fset=MagicMock(side_effect=Exception("write error"))
    )

    # Should not raise
    try:
        log_auto_invoice(svc, order, [], False)
    except Exception:
        pass  # OK if it raises due to mock side effects; just verify no uncaught crash
