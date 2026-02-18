# -*- coding: utf-8 -*-
"""第二十一批：验收完成服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date

pytest.importorskip("app.services.acceptance_completion_service")


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_order(acceptance_type="FAT", project_id=1, machine_id=2, order_id=10):
    order = MagicMock()
    order.id = order_id
    order.acceptance_type = acceptance_type
    order.project_id = project_id
    order.machine_id = machine_id
    order.status = "IN_PROGRESS"
    return order


class TestValidateRequiredCheckItems:
    def test_no_pending_items_passes(self, mock_db):
        from app.services.acceptance_completion_service import validate_required_check_items
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        # should not raise
        validate_required_check_items(mock_db, order_id=1)

    def test_pending_items_raises(self, mock_db):
        from app.services.acceptance_completion_service import validate_required_check_items
        from fastapi import HTTPException
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        with pytest.raises(HTTPException) as exc_info:
            validate_required_check_items(mock_db, order_id=1)
        assert exc_info.value.status_code == 400
        assert "3" in exc_info.value.detail


class TestUpdateAcceptanceOrderStatus:
    def test_updates_order_fields(self, mock_db):
        from app.services.acceptance_completion_service import update_acceptance_order_status
        order = _make_order()
        update_acceptance_order_status(mock_db, order, "PASSED", "全部通过", None)
        assert order.status == "COMPLETED"
        assert order.overall_result == "PASSED"
        assert order.conclusion == "全部通过"
        mock_db.add.assert_called_once_with(order)
        mock_db.flush.assert_called_once()


class TestTriggerInvoiceOnAcceptance:
    def test_auto_trigger_disabled(self, mock_db):
        from app.services.acceptance_completion_service import trigger_invoice_on_acceptance
        result = trigger_invoice_on_acceptance(mock_db, order_id=1, auto_trigger=False)
        assert result["success"] is False

    def test_auto_trigger_calls_service(self, mock_db):
        from app.services.acceptance_completion_service import trigger_invoice_on_acceptance
        mock_service = MagicMock()
        mock_service.check_and_create_invoice_request.return_value = {
            "success": True, "invoice_requests": [{"id": 1}]
        }
        with patch("app.services.invoice_auto_service.InvoiceAutoService", return_value=mock_service):
            result = trigger_invoice_on_acceptance(mock_db, order_id=5, auto_trigger=True)
        assert result["success"] is True

    def test_auto_trigger_exception_returns_error(self, mock_db):
        from app.services.acceptance_completion_service import trigger_invoice_on_acceptance
        with patch("app.services.invoice_auto_service.InvoiceAutoService", side_effect=Exception("boom")):
            result = trigger_invoice_on_acceptance(mock_db, order_id=5, auto_trigger=True)
        assert result["success"] is False
        assert "error" in result


class TestHandleAcceptanceStatusTransition:
    def test_fat_passed_calls_handler(self, mock_db):
        from app.services.acceptance_completion_service import handle_acceptance_status_transition
        order = _make_order(acceptance_type="FAT")
        mock_svc = MagicMock()
        with patch("app.services.status_transition_service.StatusTransitionService", return_value=mock_svc):
            handle_acceptance_status_transition(mock_db, order, "PASSED")
        mock_svc.handle_fat_passed.assert_called_once_with(order.project_id, order.machine_id)

    def test_sat_failed_calls_handler(self, mock_db):
        from app.services.acceptance_completion_service import handle_acceptance_status_transition
        order = _make_order(acceptance_type="SAT")
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_svc = MagicMock()
        with patch("app.services.status_transition_service.StatusTransitionService", return_value=mock_svc):
            handle_acceptance_status_transition(mock_db, order, "FAILED")
        mock_svc.handle_sat_failed.assert_called_once()

    def test_exception_does_not_propagate(self, mock_db):
        from app.services.acceptance_completion_service import handle_acceptance_status_transition
        order = _make_order(acceptance_type="FAT")
        with patch("app.services.status_transition_service.StatusTransitionService", side_effect=Exception("fail")):
            # Should not raise
            handle_acceptance_status_transition(mock_db, order, "PASSED")


class TestTriggerWarrantyPeriod:
    def test_only_final_passed(self, mock_db):
        from app.services.acceptance_completion_service import trigger_warranty_period
        order = _make_order(acceptance_type="FAT")
        trigger_warranty_period(mock_db, order, "PASSED")
        # Not a FINAL acceptance, so db.query should not be called for project stage
        project = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = project
        order2 = _make_order(acceptance_type="FINAL")
        trigger_warranty_period(mock_db, order2, "FAILED")
        # FAILED result, should also skip

    def test_final_passed_updates_project(self, mock_db):
        from app.services.acceptance_completion_service import trigger_warranty_period
        order = _make_order(acceptance_type="FINAL")
        project = MagicMock()
        project.project_code = "P001"
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        trigger_warranty_period(mock_db, order, "PASSED")
        assert project.stage == "S9"
