# -*- coding: utf-8 -*-
"""验收完成服务测试"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.acceptance_completion_service import (
    validate_required_check_items,
    update_acceptance_order_status,
    trigger_invoice_on_acceptance,
    handle_acceptance_status_transition,
    handle_progress_integration,
    check_auto_stage_transition_after_acceptance,
    trigger_warranty_period,
    trigger_bonus_calculation,
)


@pytest.fixture
def db():
    return MagicMock()


class TestValidateRequiredCheckItems:
    def test_all_completed(self, db):
        db.query.return_value.filter.return_value.count.return_value = 0
        validate_required_check_items(db, 1)  # should not raise

    def test_pending_items(self, db):
        from fastapi import HTTPException
        db.query.return_value.filter.return_value.count.return_value = 3
        with pytest.raises(HTTPException):
            validate_required_check_items(db, 1)


class TestUpdateAcceptanceOrderStatus:
    def test_update(self, db):
        order = MagicMock()
        update_acceptance_order_status(db, order, "PASSED", "OK", None)
        assert order.status == "COMPLETED"
        assert order.overall_result == "PASSED"
        db.add.assert_called()
        db.flush.assert_called()


class TestTriggerInvoice:
    def test_not_enabled(self, db):
        result = trigger_invoice_on_acceptance(db, 1, auto_trigger=False)
        assert result["success"] is False

    @patch('app.services.acceptance_completion_service.InvoiceAutoService')
    @patch.dict('os.environ', {'AUTO_CREATE_INVOICE_ON_ACCEPTANCE': 'false'})
    def test_auto_trigger(self, mock_svc, db):
        mock_instance = MagicMock()
        mock_svc.return_value = mock_instance
        mock_instance.check_and_create_invoice_request.return_value = {"success": True, "invoice_requests": []}
        result = trigger_invoice_on_acceptance(db, 1, auto_trigger=True)
        assert result["success"] is True

    def test_exception_handling(self, db):
        with patch('app.services.invoice_auto_service.InvoiceAutoService', side_effect=Exception("err")):
            result = trigger_invoice_on_acceptance(db, 1, auto_trigger=True)
            assert result["success"] is False


class TestHandleAcceptanceStatusTransition:
    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_fat_passed(self, mock_svc, db):
        order = MagicMock(acceptance_type="FAT", project_id=1, machine_id=1)
        handle_acceptance_status_transition(db, order, "PASSED")
        mock_svc.return_value.handle_fat_passed.assert_called()

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_fat_failed(self, mock_svc, db):
        order = MagicMock(acceptance_type="FAT", project_id=1, machine_id=1, id=1)
        db.query.return_value.filter.return_value.all.return_value = []
        handle_acceptance_status_transition(db, order, "FAILED")

    def test_exception_safe(self, db):
        with patch('app.services.status_transition_service.StatusTransitionService', side_effect=Exception):
            order = MagicMock(acceptance_type="FAT", project_id=1)
            handle_acceptance_status_transition(db, order, "PASSED")  # should not raise


class TestHandleProgressIntegration:
    @patch('app.services.progress_integration_service.ProgressIntegrationService')
    def test_failed(self, mock_svc, db):
        order = MagicMock()
        mock_svc.return_value.handle_acceptance_failed.return_value = []
        result = handle_progress_integration(db, order, "FAILED")
        assert "blocked_milestones" in result

    @patch('app.services.progress_integration_service.ProgressIntegrationService')
    def test_passed(self, mock_svc, db):
        order = MagicMock()
        mock_svc.return_value.handle_acceptance_passed.return_value = []
        result = handle_progress_integration(db, order, "PASSED")
        assert "unblocked_milestones" in result


class TestCheckAutoStageTransition:
    def test_not_passed(self, db):
        order = MagicMock(project_id=1)
        result = check_auto_stage_transition_after_acceptance(db, order, "FAILED")
        assert result == {}

    def test_no_project_id(self, db):
        order = MagicMock(project_id=None)
        result = check_auto_stage_transition_after_acceptance(db, order, "PASSED")
        assert result == {}


class TestTriggerWarrantyPeriod:
    def test_not_final(self, db):
        order = MagicMock(acceptance_type="FAT")
        trigger_warranty_period(db, order, "PASSED")  # should be no-op

    def test_not_passed(self, db):
        order = MagicMock(acceptance_type="FINAL")
        trigger_warranty_period(db, order, "FAILED")  # should be no-op

    def test_final_passed(self, db):
        order = MagicMock(acceptance_type="FINAL", project_id=1)
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []
        trigger_warranty_period(db, order, "PASSED")
        assert project.stage == "S9"


class TestTriggerBonusCalculation:
    def test_not_passed(self, db):
        order = MagicMock()
        trigger_bonus_calculation(db, order, "FAILED")  # should be no-op

    @patch('app.services.bonus.BonusCalculator')
    def test_passed(self, mock_calc, db):
        order = MagicMock(project_id=1)
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        trigger_bonus_calculation(db, order, "PASSED")
