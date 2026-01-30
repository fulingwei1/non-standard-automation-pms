# -*- coding: utf-8 -*-
"""
AcceptanceCompletionService 综合单元测试

测试覆盖:
- validate_required_check_items: 验证必检项
- update_acceptance_order_status: 更新验收单状态
- trigger_invoice_on_acceptance: 触发开票
- handle_acceptance_status_transition: 处理验收状态联动
- handle_progress_integration: 处理进度集成
- check_auto_stage_transition_after_acceptance: 检查自动阶段流转
- trigger_warranty_period: 触发质保期
- trigger_bonus_calculation: 触发奖金计算
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestValidateRequiredCheckItems:
    """测试 validate_required_check_items 函数"""

    def test_raises_exception_when_pending_items_exist(self):
        """测试有未完成必检项时抛出异常"""
        from app.services.acceptance_completion_service import (
            validate_required_check_items,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        with pytest.raises(Exception) as exc_info:
            validate_required_check_items(mock_db, order_id=1)

        assert "5 个必检项未完成检查" in str(exc_info.value.detail)

    def test_passes_when_no_pending_items(self):
        """测试无未完成必检项时通过"""
        from app.services.acceptance_completion_service import (
            validate_required_check_items,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # 应该不抛出异常
        validate_required_check_items(mock_db, order_id=1)


class TestUpdateAcceptanceOrderStatus:
    """测试 update_acceptance_order_status 函数"""

    def test_updates_order_status_to_completed(self):
        """测试更新验收单状态为已完成"""
        from app.services.acceptance_completion_service import (
            update_acceptance_order_status,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.status = "IN_PROGRESS"

        update_acceptance_order_status(
            mock_db,
            mock_order,
            overall_result="PASSED",
            conclusion="验收通过",
            conditions=None,
        )

        assert mock_order.status == "COMPLETED"
        assert mock_order.overall_result == "PASSED"
        assert mock_order.conclusion == "验收通过"
        assert mock_order.actual_end_date is not None
        mock_db.add.assert_called_once_with(mock_order)
        mock_db.flush.assert_called_once()

    def test_updates_with_conditions(self):
        """测试更新有条件通过的验收单"""
        from app.services.acceptance_completion_service import (
            update_acceptance_order_status,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        update_acceptance_order_status(
            mock_db,
            mock_order,
            overall_result="CONDITIONAL",
            conclusion="有条件通过",
            conditions="需整改问题A",
        )

        assert mock_order.overall_result == "CONDITIONAL"
        assert mock_order.conditions == "需整改问题A"


class TestTriggerInvoiceOnAcceptance:
    """测试 trigger_invoice_on_acceptance 函数"""

    def test_returns_failure_when_auto_trigger_disabled(self):
        """测试未启用自动开票时返回失败"""
        from app.services.acceptance_completion_service import (
            trigger_invoice_on_acceptance,
        )

        mock_db = MagicMock()

        result = trigger_invoice_on_acceptance(mock_db, order_id=1, auto_trigger=False)

        assert result["success"] is False
        assert "未启用自动开票" in result["message"]

    def test_triggers_invoice_when_enabled(self):
        """测试启用自动开票时触发"""
        from app.services.acceptance_completion_service import (
            trigger_invoice_on_acceptance,
        )

        mock_db = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.InvoiceAutoService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.check_and_create_invoice_request.return_value = {
                "success": True,
                "invoice_requests": [{"id": 1}],
            }
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"AUTO_CREATE_INVOICE_ON_ACCEPTANCE": "false"}):
                result = trigger_invoice_on_acceptance(
                    mock_db, order_id=1, auto_trigger=True
                )

            assert result["success"] is True
            assert len(result["invoice_requests"]) == 1

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.acceptance_completion_service import (
            trigger_invoice_on_acceptance,
        )

        mock_db = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.InvoiceAutoService"
        ) as MockService:
            MockService.side_effect = Exception("Service error")

            result = trigger_invoice_on_acceptance(
                mock_db, order_id=1, auto_trigger=True
            )

            assert result["success"] is False
            assert "error" in result


class TestHandleAcceptanceStatusTransition:
    """测试 handle_acceptance_status_transition 函数"""

    def test_handles_fat_passed(self):
        """测试 FAT 验收通过的处理"""
        from app.services.acceptance_completion_service import (
            handle_acceptance_status_transition,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

            mock_service.handle_fat_passed.assert_called_once_with(1, 1)

    def test_handles_fat_failed(self):
        """测试 FAT 验收失败的处理"""
        from app.services.acceptance_completion_service import (
            handle_acceptance_status_transition,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1
        mock_order.id = 10

        # Mock issues query
        mock_issue = MagicMock()
        mock_issue.issue_description = "问题描述"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_issue]

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            handle_acceptance_status_transition(mock_db, mock_order, "FAILED")

            mock_service.handle_fat_failed.assert_called_once()

    def test_handles_sat_passed(self):
        """测试 SAT 验收通过的处理"""
        from app.services.acceptance_completion_service import (
            handle_acceptance_status_transition,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "SAT"
        mock_order.project_id = 1
        mock_order.machine_id = 1

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

            mock_service.handle_sat_passed.assert_called_once_with(1, 1)

    def test_handles_final_passed(self):
        """测试终验收通过的处理"""
        from app.services.acceptance_completion_service import (
            handle_acceptance_status_transition,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"
        mock_order.project_id = 1

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            handle_acceptance_status_transition(mock_db, mock_order, "PASSED")

            mock_service.handle_final_acceptance_passed.assert_called_once_with(1)

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.acceptance_completion_service import (
            handle_acceptance_status_transition,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            MockService.side_effect = Exception("Service error")

            # 应该不抛出异常
            handle_acceptance_status_transition(mock_db, mock_order, "PASSED")


class TestHandleProgressIntegration:
    """测试 handle_progress_integration 函数"""

    def test_handles_failed_acceptance(self):
        """测试处理验收失败的进度影响"""
        from app.services.acceptance_completion_service import (
            handle_progress_integration,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.ProgressIntegrationService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.handle_acceptance_failed.return_value = [1, 2]
            MockService.return_value = mock_service

            result = handle_progress_integration(mock_db, mock_order, "FAILED")

            assert "blocked_milestones" in result
            assert result["blocked_milestones"] == [1, 2]

    def test_handles_passed_acceptance(self):
        """测试处理验收通过的进度影响"""
        from app.services.acceptance_completion_service import (
            handle_progress_integration,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.ProgressIntegrationService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.handle_acceptance_passed.return_value = [3, 4]
            MockService.return_value = mock_service

            result = handle_progress_integration(mock_db, mock_order, "PASSED")

            assert "unblocked_milestones" in result
            assert result["unblocked_milestones"] == [3, 4]

    def test_returns_empty_for_other_results(self):
        """测试其他结果返回空"""
        from app.services.acceptance_completion_service import (
            handle_progress_integration,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.ProgressIntegrationService"
        ):
            result = handle_progress_integration(mock_db, mock_order, "CONDITIONAL")

        assert result == {}


class TestCheckAutoStageTransitionAfterAcceptance:
    """测试 check_auto_stage_transition_after_acceptance 函数"""

    def test_returns_empty_when_not_passed(self):
        """测试验收未通过时返回空"""
        from app.services.acceptance_completion_service import (
            check_auto_stage_transition_after_acceptance,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        result = check_auto_stage_transition_after_acceptance(
            mock_db, mock_order, "FAILED"
        )

        assert result == {}

    def test_returns_empty_when_no_project(self):
        """测试无项目ID时返回空"""
        from app.services.acceptance_completion_service import (
            check_auto_stage_transition_after_acceptance,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = None

        result = check_auto_stage_transition_after_acceptance(
            mock_db, mock_order, "PASSED"
        )

        assert result == {}

    def test_triggers_fat_auto_transition(self):
        """测试 FAT 验收后自动流转"""
        from app.services.acceptance_completion_service import (
            check_auto_stage_transition_after_acceptance,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = 1
        mock_order.acceptance_type = "FAT"

        mock_project = MagicMock()
        mock_project.stage = "S7"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch(
            "app.services.acceptance_completion_service.StatusTransitionService"
        ) as MockService:
            mock_service = MagicMock()
            mock_service.check_auto_stage_transition.return_value = {
                "auto_advanced": True
            }
            MockService.return_value = mock_service

            result = check_auto_stage_transition_after_acceptance(
                mock_db, mock_order, "PASSED"
            )

            assert result.get("auto_advanced") is True


class TestTriggerWarrantyPeriod:
    """测试 trigger_warranty_period 函数"""

    def test_skips_when_not_passed(self):
        """测试验收未通过时跳过"""
        from app.services.acceptance_completion_service import trigger_warranty_period

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"

        trigger_warranty_period(mock_db, mock_order, "FAILED")

        mock_db.query.assert_not_called()

    def test_skips_when_not_final(self):
        """测试非终验收时跳过"""
        from app.services.acceptance_completion_service import trigger_warranty_period

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FAT"

        trigger_warranty_period(mock_db, mock_order, "PASSED")

        mock_db.query.assert_not_called()

    def test_updates_project_and_machines(self):
        """测试更新项目和设备状态"""
        from app.services.acceptance_completion_service import trigger_warranty_period

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.acceptance_type = "FINAL"
        mock_order.project_id = 1

        mock_project = MagicMock()
        mock_project.project_code = "PJ001"

        mock_machine = MagicMock()

        # 设置查询返回
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_machine]

        trigger_warranty_period(mock_db, mock_order, "PASSED")

        assert mock_project.stage == "S9"
        assert mock_project.actual_end_date == date.today()


class TestTriggerBonusCalculation:
    """测试 trigger_bonus_calculation 函数"""

    def test_skips_when_not_passed(self):
        """测试验收未通过时跳过"""
        from app.services.acceptance_completion_service import (
            trigger_bonus_calculation,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()

        trigger_bonus_calculation(mock_db, mock_order, "FAILED")

        mock_db.query.assert_not_called()

    def test_triggers_bonus_calculation(self):
        """测试触发奖金计算"""
        from app.services.acceptance_completion_service import (
            trigger_bonus_calculation,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = 1

        mock_project = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch(
            "app.services.acceptance_completion_service.BonusCalculator"
        ) as MockCalculator:
            mock_calculator = MagicMock()
            MockCalculator.return_value = mock_calculator

            trigger_bonus_calculation(mock_db, mock_order, "PASSED")

            mock_calculator.trigger_acceptance_bonus_calculation.assert_called_once_with(
                mock_project, mock_order
            )

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.acceptance_completion_service import (
            trigger_bonus_calculation,
        )

        mock_db = MagicMock()
        mock_order = MagicMock()
        mock_order.project_id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch(
            "app.services.acceptance_completion_service.BonusCalculator"
        ) as MockCalculator:
            MockCalculator.side_effect = Exception("Calculator error")

            # 应该不抛出异常
            trigger_bonus_calculation(mock_db, mock_order, "PASSED")
