# -*- coding: utf-8 -*-
"""
Unit tests for app/services/invoice_auto_service/main.py (cov52)
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.invoice_auto_service.main import check_and_create_invoice_request
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_order(overall_result="PASSED", status="COMPLETED", acceptance_type="FAT",
                project_id=10, order_id=1, order_no="ORD-001"):
    order = MagicMock()
    order.id = order_id
    order.order_no = order_no
    order.overall_result = overall_result
    order.status = status
    order.acceptance_type = acceptance_type
    order.project_id = project_id
    return order


# ──────────────────────── check_and_create_invoice_request ────────────────────────

def test_order_not_found():
    """验收单不存在时返回 success=False"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    result = check_and_create_invoice_request(service, acceptance_order_id=999)

    assert result["success"] is False
    assert "不存在" in result["message"]
    assert result["invoice_requests"] == []


def test_order_not_passed():
    """验收未通过时，返回 success=True 但不创建发票"""
    service = _make_service()
    order = _make_order(overall_result="FAILED", status="COMPLETED")
    service.db.query.return_value.filter.return_value.first.return_value = order

    result = check_and_create_invoice_request(service, acceptance_order_id=1)

    assert result["success"] is True
    assert result["invoice_requests"] == []


def test_order_not_completed():
    """验收单状态非 COMPLETED 时跳过"""
    service = _make_service()
    order = _make_order(overall_result="PASSED", status="PENDING")
    service.db.query.return_value.filter.return_value.first.return_value = order

    result = check_and_create_invoice_request(service, acceptance_order_id=1)

    assert result["success"] is True
    assert result["invoice_requests"] == []


def test_unsupported_acceptance_type():
    """不支持的验收类型返回 success=True 且无发票创建"""
    service = _make_service()
    order = _make_order(acceptance_type="PARTIAL")
    service.db.query.return_value.filter.return_value.first.return_value = order

    result = check_and_create_invoice_request(service, acceptance_order_id=1)

    assert result["success"] is True
    assert "不支持" in result["message"]
    assert result["invoice_requests"] == []


def test_no_milestones_found():
    """找不到关联里程碑时返回空列表"""
    service = _make_service()
    order = _make_order(acceptance_type="SAT")
    service.db.query.return_value.filter.return_value.first.return_value = order
    service.db.query.return_value.filter.return_value.all.return_value = []

    result = check_and_create_invoice_request(service, acceptance_order_id=1)

    assert result["success"] is True
    assert result["invoice_requests"] == []


@patch("app.services.invoice_auto_service.main.check_deliverables_complete", return_value=True)
@patch("app.services.invoice_auto_service.main.check_acceptance_issues_resolved", return_value=True)
@patch("app.services.invoice_auto_service.main.create_invoice_request")
@patch("app.services.invoice_auto_service.main.send_invoice_notifications")
@patch("app.services.invoice_auto_service.main.log_auto_invoice")
def test_success_create_invoice_request(
    mock_log, mock_notify, mock_create, mock_issues, mock_deliverables
):
    """正常流程：创建发票申请并调用通知/日志"""
    import datetime

    service = _make_service()
    order = _make_order(acceptance_type="FAT")
    milestone = MagicMock(id=1, milestone_name="FAT")
    plan = MagicMock(id=1, invoice_id=None, planned_date=None, status="PENDING",
                     payment_type="ACCEPTANCE")

    # db.query().filter().first() → order
    # db.query().filter().all() → [milestone]
    # db.query().filter().all() → [plan]
    service.db.query.return_value.filter.return_value.first.return_value = order
    service.db.query.return_value.filter.return_value.all.side_effect = [
        [milestone],  # milestones
        [plan],       # payment_plans
    ]

    mock_create.return_value = {"success": True, "request_no": "IR2412-001", "amount": 1130.0}

    result = check_and_create_invoice_request(service, acceptance_order_id=1, auto_create=False)

    assert result["success"] is True
    assert len(result["invoice_requests"]) == 1
    mock_notify.assert_called_once()
    mock_log.assert_called_once()
    service.db.commit.assert_called_once()
