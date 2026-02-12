# -*- coding: utf-8 -*-
"""发票自动服务 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.invoice_auto_service.main import check_and_create_invoice_request


def _make_service():
    s = MagicMock()
    return s


def _make_order(**kw):
    o = MagicMock()
    o.id = kw.get("id", 1)
    o.overall_result = kw.get("overall_result", "PASSED")
    o.status = kw.get("status", "COMPLETED")
    o.acceptance_type = kw.get("acceptance_type", "FAT")
    o.project_id = kw.get("project_id", 1)
    return o


class TestCheckAndCreateInvoiceRequest:
    def test_order_not_found(self):
        service = _make_service()
        service.db.query.return_value.filter.return_value.first.return_value = None
        result = check_and_create_invoice_request(service, 999)
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_not_passed_skips(self):
        service = _make_service()
        order = _make_order(overall_result="FAILED")
        service.db.query.return_value.filter.return_value.first.return_value = order
        result = check_and_create_invoice_request(service, 1)
        assert result["success"] is True
        assert "无需开票" in result["message"]

    def test_unsupported_type(self):
        service = _make_service()
        order = _make_order(acceptance_type="UNKNOWN")
        service.db.query.return_value.filter.return_value.first.return_value = order
        result = check_and_create_invoice_request(service, 1)
        assert "不支持" in result["message"]

    def test_no_milestones(self):
        service = _make_service()
        order = _make_order()
        service.db.query.return_value.filter.return_value.first.return_value = order
        service.db.query.return_value.filter.return_value.all.return_value = []
        result = check_and_create_invoice_request(service, 1)
        assert "未找到" in result["message"]

    @patch("app.services.invoice_auto_service.main.check_deliverables_complete", return_value=True)
    @patch("app.services.invoice_auto_service.main.check_acceptance_issues_resolved", return_value=True)
    @patch("app.services.invoice_auto_service.main.create_invoice_request", return_value={"success": True})
    @patch("app.services.invoice_auto_service.main.send_invoice_notifications")
    @patch("app.services.invoice_auto_service.main.log_auto_invoice")
    def test_creates_invoice_request(self, mock_log, mock_notify, mock_create, mock_issues, mock_deliv):
        service = _make_service()
        order = _make_order()
        milestone = MagicMock()
        milestone.id = 10
        plan = MagicMock()
        plan.invoice_id = None
        plan.planned_date = None  # no date = not skipped

        service.db.query.return_value.filter.return_value.first.return_value = order
        service.db.query.return_value.filter.return_value.all.side_effect = [
            [milestone],  # milestones
            [plan],       # payment_plans
        ]

        result = check_and_create_invoice_request(service, 1)
        assert result["success"] is True
        assert len(result["invoice_requests"]) == 1
