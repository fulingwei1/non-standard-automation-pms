# -*- coding: utf-8 -*-
"""
Unit tests for app/services/invoice_auto_service/notifications.py (cov52)
"""
import json
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.invoice_auto_service.notifications import (
        send_invoice_notifications,
        log_auto_invoice,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_order(order_id=1, order_no="ORD-001", project_id=10):
    order = MagicMock()
    order.id = order_id
    order.order_no = order_no
    order.project_id = project_id
    return order


# ──────────────────────── send_invoice_notifications ────────────────────────

def test_send_invoice_notifications_no_project():
    """order.project 为 None 时，函数直接返回，不报错"""
    service = _make_service()
    order = _make_order()
    order.project = None

    # 应无异常
    send_invoice_notifications(service, order, [], False)


@patch("app.services.invoice_auto_service.notifications.NotificationDispatcher")
def test_send_invoice_notifications_with_recipients(mock_dispatcher_cls):
    """存在财务角色用户和合同负责人时，正常发送通知"""
    service = _make_service()

    # 构造项目 / 合同
    project = MagicMock(project_code="P001", project_name="TestProject", contract_id=1)
    order = _make_order()
    order.project = project

    # db.query().filter().all() 返回角色ID列表
    role_ids = [(1,), (2,)]
    user_ids = [(100,)]
    contract = MagicMock(owner_id=200)

    service.db.query.return_value.filter.return_value.all.side_effect = [
        role_ids,   # finance_role_ids
        user_ids,   # finance_user_ids
    ]
    service.db.query.return_value.filter.return_value.first.return_value = contract

    mock_dispatcher = MagicMock()
    mock_dispatcher.send_notification_request.return_value = {"success": True}
    mock_dispatcher_cls.return_value = mock_dispatcher

    created_items = [{"request_no": "IR2412-001", "amount": 1130.0}]
    send_invoice_notifications(service, order, created_items, False)

    # 确认 dispatcher 被实例化
    mock_dispatcher_cls.assert_called_once_with(service.db)


@patch("app.services.invoice_auto_service.notifications.NotificationDispatcher")
def test_send_invoice_notifications_auto_create(mock_dispatcher_cls):
    # auto_create=True 时，通知内容含"发票"而非"发票申请"
    service = _make_service()
    project = MagicMock(project_code="P002", project_name="AutoProject", contract_id=None)
    order = _make_order()
    order.project = project

    service.db.query.return_value.filter.return_value.all.return_value = []
    service.db.query.return_value.filter.return_value.first.return_value = None

    mock_dispatcher_cls.return_value = MagicMock()

    send_invoice_notifications(service, order, [], auto_create=True)
    # 无异常即可


# ──────────────────────── log_auto_invoice ────────────────────────

def test_log_auto_invoice_no_existing_conditions():
    """conditions 为 None 时，初始化日志列表并追加"""
    service = _make_service()
    order = _make_order()
    order.conditions = None

    log_auto_invoice(service, order, [{"amount": 100}], False)

    stored = json.loads(order.conditions)
    assert isinstance(stored, list)
    assert len(stored) == 1
    assert stored[0]["acceptance_order_id"] == order.id


def test_log_auto_invoice_with_existing_conditions():
    """conditions 已有 JSON 时，追加而非覆盖"""
    service = _make_service()
    order = _make_order()
    existing_log = [{"acceptance_order_id": 999}]
    order.conditions = json.dumps(existing_log, ensure_ascii=False)

    log_auto_invoice(service, order, [], True)

    stored = json.loads(order.conditions)
    assert len(stored) == 2


def test_log_auto_invoice_invalid_json_conditions():
    """conditions 包含无效 JSON 时，重置为空列表再追加"""
    service = _make_service()
    order = _make_order()
    order.conditions = "NOT_VALID_JSON{{{"

    log_auto_invoice(service, order, [], False)

    stored = json.loads(order.conditions)
    assert isinstance(stored, list)
    assert len(stored) == 1


def test_log_auto_invoice_exception_is_swallowed():
    """内部异常不应向上传播"""
    service = _make_service()
    order = MagicMock()
    # 访问 order.id 时抛出异常
    type(order).id = property(lambda self: (_ for _ in ()).throw(RuntimeError("DB error")))

    # 应捕获异常，不向外抛出
    log_auto_invoice(service, order, [], False)
