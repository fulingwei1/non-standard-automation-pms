# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/invoice_auto_service/main.py
"""
import pytest

pytest.importorskip("app.services.invoice_auto_service.main")

from unittest.mock import MagicMock, patch

from app.services.invoice_auto_service.main import check_and_create_invoice_request


def make_service():
    svc = MagicMock()
    svc.db = MagicMock()
    return svc


# ── 1. 验收单不存在 ───────────────────────────────────────────────────────────
def test_order_not_found():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    result = check_and_create_invoice_request(svc, acceptance_order_id=999)
    assert result["success"] is False
    assert "不存在" in result["message"]


# ── 2. 验收未通过 ─────────────────────────────────────────────────────────────
def test_order_not_passed():
    svc = make_service()
    order = MagicMock()
    order.overall_result = "FAILED"
    order.status = "COMPLETED"
    svc.db.query.return_value.filter.return_value.first.return_value = order

    result = check_and_create_invoice_request(svc, acceptance_order_id=1)
    assert result["success"] is True
    assert "无需开票" in result["message"]
    assert result["invoice_requests"] == []


# ── 3. 不支持的验收类型 ───────────────────────────────────────────────────────
def test_unsupported_acceptance_type():
    svc = make_service()
    order = MagicMock()
    order.overall_result = "PASSED"
    order.status = "COMPLETED"
    order.acceptance_type = "UNKNOWN"
    svc.db.query.return_value.filter.return_value.first.return_value = order

    result = check_and_create_invoice_request(svc, acceptance_order_id=2)
    assert result["success"] is True
    assert "不支持" in result["message"]


# ── 4. 里程碑不存在 ───────────────────────────────────────────────────────────
def test_no_milestones():
    svc = make_service()
    order = MagicMock()
    order.overall_result = "PASSED"
    order.status = "COMPLETED"
    order.acceptance_type = "FAT"
    order.project_id = 1

    q_order = MagicMock()
    q_order.filter.return_value.first.return_value = order

    q_milestone = MagicMock()
    q_milestone.filter.return_value.all.return_value = []

    svc.db.query.side_effect = [q_order, q_milestone]

    result = check_and_create_invoice_request(svc, acceptance_order_id=3)
    assert result["success"] is True
    assert "未找到" in result["message"]


# ── 5. 创建发票申请（auto_create=False）────────────────────────────────────────
def test_create_invoice_request_flow():
    svc = make_service()
    order = MagicMock()
    order.overall_result = "PASSED"
    order.status = "COMPLETED"
    order.acceptance_type = "SAT"
    order.project_id = 2
    order.id = 10

    milestone = MagicMock()
    milestone.id = 100

    plan = MagicMock()
    plan.invoice_id = None
    plan.planned_date = None

    with patch("app.services.invoice_auto_service.main.check_deliverables_complete", return_value=True), \
         patch("app.services.invoice_auto_service.main.check_acceptance_issues_resolved", return_value=True), \
         patch("app.services.invoice_auto_service.main.create_invoice_request",
               return_value={"success": True, "request_no": "IR2602-001", "amount": 1000.0}) as mock_create, \
         patch("app.services.invoice_auto_service.main.send_invoice_notifications"), \
         patch("app.services.invoice_auto_service.main.log_auto_invoice"):

        q_order = MagicMock()
        q_order.filter.return_value.first.return_value = order

        q_milestone = MagicMock()
        q_milestone.filter.return_value.all.return_value = [milestone]

        q_plan = MagicMock()
        q_plan.filter.return_value.all.return_value = [plan]

        svc.db.query.side_effect = [q_order, q_milestone, q_plan]
        result = check_and_create_invoice_request(svc, acceptance_order_id=10, auto_create=False)

    assert result["success"] is True
    assert len(result["invoice_requests"]) == 1


# ── 6. 自动创建发票（auto_create=True） ───────────────────────────────────────
def test_create_invoice_directly_flow():
    svc = make_service()
    order = MagicMock()
    order.overall_result = "PASSED"
    order.status = "COMPLETED"
    order.acceptance_type = "FINAL"
    order.project_id = 3
    order.id = 20

    milestone = MagicMock()
    milestone.id = 200

    plan = MagicMock()
    plan.invoice_id = None
    plan.planned_date = None

    with patch("app.services.invoice_auto_service.main.check_deliverables_complete", return_value=True), \
         patch("app.services.invoice_auto_service.main.check_acceptance_issues_resolved", return_value=True), \
         patch("app.services.invoice_auto_service.main.create_invoice_directly",
               return_value={"success": True, "invoice_code": "INV2602-001", "amount": 2000.0}), \
         patch("app.services.invoice_auto_service.main.send_invoice_notifications"), \
         patch("app.services.invoice_auto_service.main.log_auto_invoice"):

        q_order = MagicMock()
        q_order.filter.return_value.first.return_value = order

        q_milestone = MagicMock()
        q_milestone.filter.return_value.all.return_value = [milestone]

        q_plan = MagicMock()
        q_plan.filter.return_value.all.return_value = [plan]

        svc.db.query.side_effect = [q_order, q_milestone, q_plan]
        result = check_and_create_invoice_request(svc, acceptance_order_id=20, auto_create=True)

    assert result["success"] is True
    assert len(result["invoice_requests"]) == 1
