# -*- coding: utf-8 -*-
"""
acceptance_completion_service 单元测试

测试验收完成服务的各个方法
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.acceptance_completion_service import (
    check_auto_stage_transition_after_acceptance,
    handle_acceptance_status_transition,
    handle_progress_integration,
    trigger_bonus_calculation,
    trigger_invoice_on_acceptance,
    trigger_warranty_period,
    update_acceptance_order_status,
    validate_required_check_items,
)


@pytest.mark.unit
class TestValidateRequiredCheckItems:
    """测试 validate_required_check_items 函数"""

    def test_all_items_completed(self):
        """测试所有必检项已完成"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Should not raise exception
        validate_required_check_items(mock_db, 1)

    def test_pending_items_exist(self):
        """测试还有未完成的必检项"""
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        with pytest.raises(HTTPException) as exc_info:
            validate_required_check_items(mock_db, 1)

        assert exc_info.value.status_code == 400
        assert "3 个必检项" in exc_info.value.detail


@pytest.mark.unit
class TestUpdateAcceptanceOrderStatus:
    """测试 update_acceptance_order_status 函数"""

    def test_update_status_passed(self):
        """测试更新状态为通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()

        update_acceptance_order_status(
            mock_db,
            mock_order,
            overall_result="PASSED",
            conclusion="验收通过",
            conditions="无条件"
        )

        assert mock_order.status == "COMPLETED"
        assert mock_order.overall_result == "PASSED"
        assert mock_order.conclusion == "验收通过"
        assert mock_order.conditions == "无条件"
        assert mock_order.actual_end_date is not None
        mock_db.add.assert_called_once_with(mock_order)
        mock_db.flush.assert_called_once()

    def test_update_status_failed(self):
        """测试更新状态为不通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()

        update_acceptance_order_status(
            mock_db,
            mock_order,
            overall_result="FAILED",
            conclusion="验收未通过",
            conditions=None
        )

        assert mock_order.status == "COMPLETED"
        assert mock_order.overall_result == "FAILED"


@pytest.mark.unit
class TestTriggerInvoiceOnAcceptance:
    """测试 trigger_invoice_on_acceptance 函数"""

    def test_auto_trigger_disabled(self):
        """测试自动开票未启用"""
        mock_db = MagicMock()

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=False)

        assert result["success"] is False
        assert "未启用" in result["message"]

    @patch('app.services.invoice_auto_service.InvoiceAutoService')
    @patch.dict('os.environ', {'AUTO_CREATE_INVOICE_ON_ACCEPTANCE': 'false'})
    def test_auto_trigger_success(self, mock_service_class):
        """测试自动开票成功"""
        mock_db = MagicMock()

        mock_service = MagicMock()
        mock_service.check_and_create_invoice_request.return_value = {
            "success": True,
            "invoice_requests": [{"id": 1}]
        }
        mock_service_class.return_value = mock_service

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=True)

        assert result["success"] is True
        assert len(result["invoice_requests"]) == 1

    @patch('app.services.invoice_auto_service.InvoiceAutoService')
    def test_auto_trigger_exception(self, mock_service_class):
        """测试自动开票异常"""
        mock_db = MagicMock()
        mock_service_class.side_effect = Exception("Service error")

        result = trigger_invoice_on_acceptance(mock_db, 1, auto_trigger=True)

        assert result["success"] is False
        assert "error" in result


@pytest.mark.unit
class TestHandleAcceptanceStatusTransition:
    """测试 handle_acceptance_status_transition 函数"""

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_fat_passed(self, mock_service_class):
        """测试FAT验收通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

        mock_service.handle_fat_passed.assert_called_once_with(1, 1)

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_fat_failed(self, mock_service_class):
        """测试FAT验收不通过"""
        mock_db = MagicMock()

        mock_issue = MagicMock()
        mock_issue.issue_description = "问题描述"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_issue]

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        handle_acceptance_status_transition(mock_db, mock_order, "FAILED")

        mock_service.handle_fat_failed.assert_called_once()

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_sat_passed(self, mock_service_class):
        """测试SAT验收通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "SAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

        mock_service.handle_sat_passed.assert_called_once_with(1, 1)

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_final_passed(self, mock_service_class):
        """测试终验收通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"
        mock_order.project_id = 1

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

        mock_service.handle_final_acceptance_passed.assert_called_once_with(1)

    def test_exception_handling(self):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "UNKNOWN"

        # Should not raise exception
        handle_acceptance_status_transition(mock_db, mock_order, "PASSED")


@pytest.mark.unit
class TestHandleProgressIntegration:
    """测试 handle_progress_integration 函数"""

    @patch('app.services.progress_integration_service.ProgressIntegrationService')
    def test_acceptance_failed(self, mock_service_class):
        """测试验收失败处理"""
        mock_db = MagicMock()
        mock_order = MagicMock()

        mock_service = MagicMock()
        mock_service.handle_acceptance_failed.return_value = ["milestone1", "milestone2"]
        mock_service_class.return_value = mock_service

        result = handle_progress_integration(mock_db, mock_order, "FAILED")

        assert "blocked_milestones" in result
        assert len(result["blocked_milestones"]) == 2

    @patch('app.services.progress_integration_service.ProgressIntegrationService')
    def test_acceptance_passed(self, mock_service_class):
        """测试验收通过处理"""
        mock_db = MagicMock()
        mock_order = MagicMock()

        mock_service = MagicMock()
        mock_service.handle_acceptance_passed.return_value = ["milestone1"]
        mock_service_class.return_value = mock_service

        result = handle_progress_integration(mock_db, mock_order, "PASSED")

        assert "unblocked_milestones" in result
        assert len(result["unblocked_milestones"]) == 1

    @patch('app.services.progress_integration_service.ProgressIntegrationService')
    def test_exception_handling(self, mock_service_class):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_service_class.side_effect = Exception("Service error")

        result = handle_progress_integration(mock_db, mock_order, "PASSED")

        assert "error" in result


@pytest.mark.unit
class TestCheckAutoStageTransitionAfterAcceptance:
    """测试 check_auto_stage_transition_after_acceptance 函数"""

    def test_not_passed(self):
        """测试验收未通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = 1

        result = check_auto_stage_transition_after_acceptance(mock_db, mock_order, "FAILED")

        assert result == {}

    def test_no_project_id(self):
        """测试没有项目ID"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = None

        result = check_auto_stage_transition_after_acceptance(mock_db, mock_order, "PASSED")

        assert result == {}

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_fat_auto_transition(self, mock_service_class):
        """测试FAT验收后自动阶段流转"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.stage = "S7"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_order = MagicMock()
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"

        mock_service = MagicMock()
        mock_service.check_auto_stage_transition.return_value = {"auto_advanced": True}
        mock_service_class.return_value = mock_service

        result = check_auto_stage_transition_after_acceptance(mock_db, mock_order, "PASSED")

        assert result.get("auto_advanced") is True

    @patch('app.services.status_transition_service.StatusTransitionService')
    def test_final_auto_transition(self, mock_service_class):
        """测试终验收后自动阶段流转"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.stage = "S8"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_order = MagicMock()
        mock_order.project_id = 1
        mock_order.acceptance_type = "FINAL"

        mock_service = MagicMock()
        mock_service.check_auto_stage_transition.return_value = {"auto_advanced": True}
        mock_service_class.return_value = mock_service

        result = check_auto_stage_transition_after_acceptance(mock_db, mock_order, "PASSED")

        assert result.get("auto_advanced") is True


@pytest.mark.unit
class TestTriggerWarrantyPeriod:
    """测试 trigger_warranty_period 函数"""

    def test_not_passed(self):
        """测试验收未通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"

        trigger_warranty_period(mock_db, mock_order, "FAILED")

        mock_db.query.assert_not_called()

    def test_not_final(self):
        """测试非终验收"""
        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"

        trigger_warranty_period(mock_db, mock_order, "PASSED")

        mock_db.query.assert_not_called()

    def test_project_not_found(self):
        """测试项目不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"
        mock_order.project_id = 999

        trigger_warranty_period(mock_db, mock_order, "PASSED")

    def test_trigger_success(self):
        """测试成功触发质保期"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.project_code = "P001"

        mock_machine = MagicMock()

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
            elif model_name == 'Machine':
                query_mock.filter.return_value.all.return_value = [mock_machine]
            return query_mock

        mock_db.query.side_effect = query_side_effect

        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"
        mock_order.project_id = 1

        trigger_warranty_period(mock_db, mock_order, "PASSED")

        assert mock_project.stage == "S9"
        assert mock_machine.stage == "S9"
        assert mock_machine.status == "COMPLETED"


@pytest.mark.unit
class TestTriggerBonusCalculation:
    """测试 trigger_bonus_calculation 函数"""

    def test_not_passed(self):
        """测试验收未通过"""
        mock_db = MagicMock()
        mock_order = MagicMock()

        trigger_bonus_calculation(mock_db, mock_order, "FAILED")

        mock_db.query.assert_not_called()

    @patch('app.services.bonus.BonusCalculator')
    def test_trigger_success(self, mock_calculator_class):
        """测试成功触发奖金计算"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator

        mock_order = MagicMock()
        mock_order.project_id = 1

        trigger_bonus_calculation(mock_db, mock_order, "PASSED")

        mock_calculator.trigger_acceptance_bonus_calculation.assert_called_once()

    @patch('app.services.bonus.BonusCalculator')
    def test_exception_handling(self, mock_calculator_class):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        mock_order = MagicMock()
        mock_order.project_id = 1

        # Should not raise exception
        trigger_bonus_calculation(mock_db, mock_order, "PASSED")


@pytest.mark.unit
class TestAcceptanceCompletionIntegration:
    """集成测试"""

    def test_all_functions_importable(self):
        """测试所有函数可导入"""
        from app.services.acceptance_completion_service import (
            check_auto_stage_transition_after_acceptance,
            handle_acceptance_status_transition,
            handle_progress_integration,
            trigger_bonus_calculation,
            trigger_invoice_on_acceptance,
            trigger_warranty_period,
            update_acceptance_order_status,
            validate_required_check_items,
        )

        assert validate_required_check_items is not None
        assert update_acceptance_order_status is not None
        assert trigger_invoice_on_acceptance is not None
        assert handle_acceptance_status_transition is not None
        assert handle_progress_integration is not None
        assert check_auto_stage_transition_after_acceptance is not None
        assert trigger_warranty_period is not None
        assert trigger_bonus_calculation is not None
