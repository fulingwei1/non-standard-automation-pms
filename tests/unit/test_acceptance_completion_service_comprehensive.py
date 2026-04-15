# -*- coding: utf-8 -*-
"""Compatibility regressions for acceptance completion service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.acceptance_completion_service import (
    check_auto_stage_transition_after_acceptance,
    handle_acceptance_status_transition,
    handle_progress_integration,
    trigger_bonus_calculation,
    trigger_invoice_on_acceptance,
)


pytestmark = pytest.mark.unit


class TestTriggerInvoiceOnAcceptance:
    def test_triggers_invoice_when_enabled(self):
        db = MagicMock()

        with patch("app.services.acceptance_completion_service.InvoiceAutoService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.check_and_create_invoice_request.return_value = {
                "success": True,
                "invoice_requests": [{"id": 1}],
            }
            mock_service_cls.return_value = mock_service

            with patch.dict("os.environ", {"AUTO_CREATE_INVOICE_ON_ACCEPTANCE": "false"}):
                result = trigger_invoice_on_acceptance(db, order_id=1, auto_trigger=True)

        assert result["success"] is True
        assert len(result["invoice_requests"]) == 1


class TestHandleAcceptanceStatusTransition:
    def test_handles_fat_passed(self):
        db = MagicMock()
        order = MagicMock(acceptance_type="FAT", project_id=1, machine_id=2)

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as mock_service_cls:
            service = MagicMock()
            mock_service_cls.return_value = service

            handle_acceptance_status_transition(db, order, "PASSED")

        service.handle_fat_passed.assert_called_once_with(1, 2)


class TestHandleProgressIntegration:
    def test_handles_failed_acceptance(self):
        db = MagicMock()
        order = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.ProgressIntegrationService"
        ) as mock_service_cls:
            service = MagicMock()
            service.handle_acceptance_failed.return_value = [1, 2]
            mock_service_cls.return_value = service

            result = handle_progress_integration(db, order, "FAILED")

        assert result == {"blocked_milestones": [1, 2]}


class TestCheckAutoStageTransitionAfterAcceptance:
    def test_triggers_fat_auto_transition(self):
        db = MagicMock()
        order = MagicMock(project_id=1, acceptance_type="FAT")
        project = MagicMock(stage="S7")
        db.query.return_value.filter.return_value.first.return_value = project

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as mock_service_cls:
            service = MagicMock()
            service.check_auto_stage_transition.return_value = {"auto_advanced": True}
            mock_service_cls.return_value = service

            result = check_auto_stage_transition_after_acceptance(db, order, "PASSED")

        assert result == {"auto_advanced": True}


class TestTriggerBonusCalculation:
    def test_triggers_bonus_calculation(self):
        db = MagicMock()
        order = MagicMock(project_id=1)
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project

        with patch("app.services.acceptance_completion_service.BonusCalculator") as mock_calc_cls:
            calculator = MagicMock()
            mock_calc_cls.return_value = calculator

            trigger_bonus_calculation(db, order, "PASSED")

        calculator.trigger_acceptance_bonus_calculation.assert_called_once_with(project, order)
